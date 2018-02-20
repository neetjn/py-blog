from r2dto import fields, validators, Serializer


class LinkDto(object):

    def __init__(self, rel=None, href=None):
        self.rel = rel
        self.href = href


class LinkDtoSerializer(Serializer):

    rel = fields.StringField()
    href = fields.StringField()

    class Meta(object):
        model = LinkDto


class UserDto(object):

    def __init__(self, **kwargs):

        self.username = kwargs.get('username', '')
        self.email = kwargs.get('email', '')
        self.full_name = kwargs.get('full_name', '')
        self.comments = kwargs.get('comments', [])
        self.total_likes = kwargs.get('total_links', 0)
        self.last_posted = kwargs.get('last_posted', None)
        self.last_activity = kwargs.get('last_activity', None)
        self.links = kwargs.get('links', [])


class UserDtoSerializer(object):

    username = fields.StringField()
    full_name = fields.StringField(name='fullName')
    email = fields.StringField()
    posts = fields.ListField(fields.StringField)
    comments = fields.ListField(fields.StringField)
    total_likes = fields.IntegerField(name='totalLikes')
    last_posted = fields.DateTimeField(name='lastPosted')
    last_activity = fields.DateTimeField(name='lastActivity')
    links = fields.ListField(fields.ObjectField(LinkDtoSerializer))

    class Meta(object):
        model = UserDto


class UserWithPasswordDto(object):

    def __init__(self):

        username = fields.StringField()
        password = fields.StringField()
        email = fields.StringField()


class CommentDto(object):

    def __init__(self, **kwargs):

        self.id = kwargs.get('id', '')
        self.author = kwargs.get('author', '')
        self.content = kwargs.get('content', '')
        self.tags = kwargs.get('tags', [])
        self.created = kwargs.get('created', None)
        self.edited = kwargs.get('edited', None)
        self.comments = kwargs.get('comments', [])
        self.likes = kwargs.get('likes', 0)
        self.views = kwargs.get('views', 0)
        self.links = wargs.get('links', [])


class CommentDtoSerializer(Serializer):

    id = fields.StringField()
    author = fields.StringField()
    content = fields.StringField()
    tags = fields.ListField(fields.StringField)
    created = fields.DateTimeField()
    edited = fields.DateTimeField()
    comments = fields.ListField(fields.StringField)
    likes = fields.IntegerField()
    views = fields.IntegerField()
    links = fields.ListField(fields.ObjectField(LinkDtoSerializer))

    class Meta(object):

        model = CommentDto


class PostViewDto(object):

    def __init__(self, **kwargs):

        self.ip_address = kwargs.get('ip_address', None)
        self.view_time = kwargs.get('view_time', None)


class PostViewDtoSerializer(Serializer):

    ip_address = fields.StringField(name='ipAddress', required=True)
    view_time = fields.DateTimeField(name='viewTime', required=True)

    class Meta(object):

        model = PostViewDto


class PostDto(object):

    def __init__(self, **kwargs):

        self.id = kwargs.get('id', '')
        self.title = kwargs.get('title', '')
        self.author = kwargs.get('author', '')
        self.content = kwargs.get('content', '')
        self.tags = kwargs.get('tags', [])
        self.created = kwargs.get('created', None)
        self.edited = kwargs.get('edited', None)
        self.comments = kwargs.get('comments', [])
        self.likes = kwargs.get('likes', 0)
        self.views = kwargs.get('views', 0)
        self.links = kwargs.get('links', [])


class PostDtoSerializer(Serializer):

    id = fields.StringField()
    title = fields.StringField()
    author = fields.StringField()
    content = fields.StringField()
    tags = fields.ListField(fields.StringField)
    created = fields.DateTimeField()
    edited = fields.DateTimeField()
    comments = fields.ListField(CommentSerializer)
    likes = fields.IntegerField()
    views = fields.ListField(PostViewSerializer)
    links = fields.ListField(fields.ObjectField(LinkDtoSerializer))

    class Meta(object):

        model = PostDto