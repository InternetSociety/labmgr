from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls.resolvers import RoutePattern
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisStore, SELF
from ws4redis.subscriber import RedisSubscriber

events_route = RoutePattern('ws/<int:project_id>/events')


# noinspection PyUnusedLocal
def get_allowed_channels(request, channels):
    try:
        if not request.user.is_authenticated:
            raise PermissionDenied("Please log in")

        path_info = request.environ.get('PATH_INFO', '').lstrip('/')

        events = events_route.match(path_info)
        if events:
            extra_path, _args, kwargs = events
            if extra_path != '':
                # We don't accept trailing garbage
                raise Http404

            authorized = request.session.get('authorized_exercises', [])
            if kwargs['project_id'] in authorized:
                return {'subscribe-broadcast', 'publish-server'}

            raise PermissionDenied("No access to this exercise")

        # Fall through means nothing matched
        raise Http404

    except Http404:
        raise PermissionDenied("URL doesn't exist")


class LabRedisStore(RedisStore):
    def _get_message_channels(self, request=None, facility='{facility}', broadcast=False,
                              groups=(), users=(), sessions=(), server=False):
        channels = super()._get_message_channels(request, facility, broadcast=broadcast, groups=groups, users=users,
                                                 sessions=sessions)

        if server:
            prefix = self.get_prefix()
            channels.append('{prefix}server:{facility}'.format(prefix=prefix, facility=facility))

        return channels


class LabPublisher(RedisPublisher, LabRedisStore):
    pass


class LabSubscriber(RedisSubscriber, LabRedisStore):
    subscription_channels = RedisSubscriber.subscription_channels + ['subscribe-server']
    publish_channels = RedisSubscriber.publish_channels + ['publish-server']

    def set_pubsub_channels(self, request, channels):
        """
        Initialize the channels used for publishing and subscribing messages through the message queue.
        """
        facility = request.path_info.replace(settings.WEBSOCKET_URL, '', 1)

        # initialize publishers
        audience = {
            'users': 'publish-user' in channels and [SELF] or [],
            'groups': 'publish-group' in channels and [SELF] or [],
            'sessions': 'publish-session' in channels and [SELF] or [],
            'broadcast': 'publish-broadcast' in channels,
            'server': 'publish-server' in channels,
        }
        self._publishers = set()
        for key in self._get_message_channels(request=request, facility=facility, **audience):
            self._publishers.add(key)

        # initialize subscribers
        audience = {
            'users': 'subscribe-user' in channels and [SELF] or [],
            'groups': 'subscribe-group' in channels and [SELF] or [],
            'sessions': 'subscribe-session' in channels and [SELF] or [],
            'broadcast': 'subscribe-broadcast' in channels,
            'server': 'subscribe-server' in channels,
        }
        self._subscription = self._connection.pubsub()
        for key in self._get_message_channels(request=request, facility=facility, **audience):
            self._subscription.subscribe(key)
