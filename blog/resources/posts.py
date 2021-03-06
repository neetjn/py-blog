import base64
import falcon
import redis
from falcon_redis_cache.hooks import CacheProvider
from blog.core.posts import get_posts, get_post, create_post, edit_post, delete_post, \
    post_to_dto, like_post, view_post, get_post_comments, create_post_comment, search_posts, \
    post_to_v2_dto
from blog.core.comments import comment_to_dto
from blog.db import Post, User
from blog.errors import UnauthorizedRequestError
from blog.hooks.responders import auto_respond, request_body, response_body
from blog.hooks.users import is_logged_in
from blog.mediatypes import PostV2DtoSerializer, PostCollectionV2DtoSerializer, \
    PostFormDtoSerializer, PostCollectionV2Dto, UserRoles, LinkDto, \
    CommentFormDtoSerializer, PostSearchSettingsDtoSerializer, HttpMethods, \
    PostDtoSerializer
from blog.resources import comments as comments
from blog.resources.base import BaseResource
from blog.utils.serializers import from_json


class BLOG_POST_RESOURCE_HREF_REL(object):

    SELF = 'self'
    POST_LIKE = 'post-like'
    POST_VIEW = 'post-view'
    POST_COMMENT = 'post-comment'


def get_post_links(req: falcon.Request, post: Post) -> list:
    """
    Construct post resource links.

    :param req: Request object to pull host from.
    :type req: falcon.Request
    :param post: Post document to construct links for.
    :type post: Post
    """
    return [
        LinkDto(rel=BLOG_POST_RESOURCE_HREF_REL.SELF,
                href=PostResource.url_to(req.netloc, post_id=post.id),
                accepted_methods=[HttpMethods.GET, HttpMethods.PUT, HttpMethods.DELETE]),
        LinkDto(rel=BLOG_POST_RESOURCE_HREF_REL.POST_COMMENT,
                href=PostCommentResource.url_to(req.netloc, post_id=post.id),
                accepted_methods=[HttpMethods.POST]),
        LinkDto(rel=BLOG_POST_RESOURCE_HREF_REL.POST_LIKE,
                href=PostLikeResource.url_to(req.netloc, post_id=post.id),
                accepted_methods=[HttpMethods.PUT]),
        LinkDto(rel=BLOG_POST_RESOURCE_HREF_REL.POST_VIEW,
                href=PostViewResource.url_to(req.netloc, post_id=post.id),
                accepted_methods=[HttpMethods.PUT])]


def user_has_post_access(user: User, post_id: str) -> bool:
    """
    Verify user's ability to update or delete post.

    :param user: User resource to pull information from.
    :type user: User
    :param post_id: Identifier of post resource.
    :type post_id: str
    """
    return get_post(post_id).author != user.id and \
        user.role not in (UserRoles.ADMIN, UserRoles.MODERATOR)


class PostCommentResource(BaseResource):

    route = '/v1/post/{post_id}/comment'

    @falcon.before(auto_respond)
    @falcon.before(request_body, CommentFormDtoSerializer)
    @falcon.before(is_logged_in)
    def on_post(self, req, resp, post_id):
        """Create comment for existing post resource"""
        user = req.context.get('user')
        create_post_comment(post_id, str(user.id), req.payload)


class PostViewResource(BaseResource):

    route = '/v1/post/{post_id}/view'

    @falcon.before(auto_respond)
    @falcon.before(is_logged_in)
    def on_put(self, req, resp, post_id):
        """View an existing post resource"""
        user = req.context.get('user')
        view_post(post_id, str(user.id), req.access_route[0])


class PostLikeResource(BaseResource):

    route = '/v1/post/{post_id}/like'

    @falcon.before(auto_respond)
    @falcon.before(is_logged_in)
    def on_put(self, req, resp, post_id):
        """Like an existing post resource"""
        user = req.context.get('user')
        like_post(post_id, str(user.id))


class PostResource(BaseResource):

    route = '/v1/post/{post_id}/'

    @CacheProvider.from_cache
    @falcon.before(auto_respond)
    @falcon.after(response_body, PostDtoSerializer)
    def on_get(self, req, resp, post_id):
        """Fetch single post resource."""
        post = get_post(post_id)
        post_dto = post_to_dto(post, href=req.uri, links=get_post_links(req, post))
        post_comments = get_post_comments(post_id)

        post_dto.comments = [comment_to_dto(comment,
                                            href=comments.CommentResource.url_to(req.netloc,
                                            comment_id=str(comment.id),
                                            links=comments.get_comment_links(req, comment))) for comment in post_comments]

        resp.body = post_dto

    @falcon.before(auto_respond)
    @falcon.before(request_body, PostFormDtoSerializer)
    @falcon.before(is_logged_in)
    def on_put(self, req, resp, post_id):
        """Update single post resource."""
        user = req.context.get('user')
        if not user_has_post_access(user, post_id):
            raise UnauthorizedRequestError(user)
        # ensure non authorized users cannot set post featured status
        if user.role not in (UserRoles.ADMIN, UserRoles.MODERATOR) and req.payload.featured:
            post = get_post(post_id)
            if not post.featured:
                raise UnauthorizedRequestError()
        edit_post(post_id, req.payload)

    @falcon.before(auto_respond)
    @falcon.before(is_logged_in)
    def on_delete(self, req, resp, post_id):
        """Delete single post resource."""
        user = req.context.get('user')
        if not user_has_post_access(user, post_id):
            raise UnauthorizedRequestError(user)
        delete_post(post_id)


class PostCollectionResource(BaseResource):

    route = '/v1/posts/'
    cache_with_query = True

    @CacheProvider.from_cache
    @falcon.before(auto_respond)
    @falcon.after(response_body, PostCollectionV2DtoSerializer)
    def on_get(self, req, resp):
        """
        Fetch grid view for all post resources.

        Note: This endpoint supports pagination, pagination arguments must be provided via query args.
        """
        pagination = req.context.get('pagination')
        post_collection_dto = PostCollectionV2Dto(posts=[
            post_to_v2_dto(post, href=PostResource.url_to(req.netloc, post_id=post.id), links=get_post_links(req, post))
            for post in get_posts(start=pagination.get('start'),
                                  count=pagination.get('count'))])
        resp.body = post_collection_dto

    @falcon.before(auto_respond)
    @falcon.before(request_body, PostFormDtoSerializer)
    @falcon.before(is_logged_in)
    def on_post(self, req, resp):
        """Create a new post resource."""
        user = req.context.get('user')
        create_post(user.id, req.payload)
        # link to grid view
        resp.set_header('Location', req.uri)


class PostSearchResource(BaseResource):

    route = '/v1/posts/search/'
    cache_with_query = True

    @CacheProvider.from_cache
    @falcon.before(auto_respond)
    @falcon.before(request_body, PostSearchSettingsDtoSerializer)
    @falcon.before(is_logged_in)
    @falcon.after(response_body, PostCollectionV2DtoSerializer)
    def on_post(self, req, resp):
        """Search for an existing post resource."""
        pagination = req.context.get('pagination')
        user = req.context.get('user')
        post_collection_dto = PostCollectionV2Dto(posts=[
            post_to_v2_dto(post, href=PostResource.url_to(req.netloc, post_id=post.id), links=get_post_links(req, post))
            for post in search_posts(req.payload, str(user.id), pagination.get('start'), pagination.get('count'))])
        resp.body = post_collection_dto


# override resource binded cache with later defined resources
PostCommentResource.binded_resources = [PostResource]
PostViewResource.binded_resources = [PostResource]
PostLikeResource.binded_resources = [PostResource]
PostResource.binded_resources = [PostCollectionResource, PostSearchResource]
