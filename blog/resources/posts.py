import falcon
from blog.core.posts import get_posts, get_post, create_post, edit_post, delete_post, \
    post_to_dto
from blog.db import User
from blog.errors import UnauthorizedRequest
from blog.hooks.users import require_login
from blog.mediatypes import PostDtoSerializer, PostCollectionDtoSerializer, \
    PostFormDtoSerializer, PostCollectionDto, UserRoles
from blog.resources.base import BaseResource
from blog.utils.serializers import from_json, to_json

# TODO: include functionality and endpoint for liking post
# can include like endpoint in post link


def user_has_post_access(user: User, post_id: str) -> bool:
    return get_post(post_id).author != user.id and \
        user.role not in (UserRoles.admin, UserRoles.moderator)


class PostResource(BaseResource):

    route = '/v1/post/{post_id}/'

    def on_get(self, req, resp, post_id):
        """Fetch single post resource."""
        resp.status = falcon.HTTP_200
        post_dto = post_to_dto(get_post(post_id))
        # no need to construct url, pull from request
        post_dto.href = req.uri
        resp.body = to_json(PostDtoSerializer, post_dto)

    @falcon.before(require_login)
    def on_put(self, req, resp, post_id):
        """Update single post resource."""
        resp.status = falcon.HTTP_204
        user = req.context.get('user')
        if not user_has_post_access(user, post_id):
            raise UnauthorizedRequest(user)
        payload = req.stream.read()
        edit_post(post_id, from_json(PostFormDtoSerializer, payload))

    @falcon.before(require_login)
    def on_delete(self, req, resp, post_id):
        """Delete single post resource."""
        resp.status = falcon.HTTP_204
        user = req.context.get('user')
        if not user_has_post_access(user, post_id):
            raise UnauthorizedRequest(user)
        delete_post(post_id)


class PostCollectionResource(BaseResource):

    route = '/v1/posts/'

    def on_get(self, req, resp):
        """
        Fetch grid view for all post resources.

        Note: This endpoint support pagination, pagination arguments must be provided via query args.
        """
        resp.status = falcon.HTTP_200
        post_collection_dto = PostCollectionDto(
            posts=[post_to_dto(post, href=PostResource.url_to(req.host, post_id=post.id), comments=False)
            for post in get_posts(start=req.params.get('start'), count=req.params.get('count'))])
        resp.body = to_json(PostCollectionDtoSerializer, post_collection_dto)

    @falcon.before(require_login)
    def on_post(self, req, resp):
        """Create a new post resource."""
        resp.status = falcon.HTTP_201
        payload = req.stream.read()
        user = req.context.get('user')
        create_post(user.id, from_json(PostFormDtoSerializer, payload))
        # link to grid view
        resp.set_header('Location', req.uri)
