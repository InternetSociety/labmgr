import json
import re
import select
from base64 import b64encode
from telnetlib import Telnet
from traceback import print_exc

from django.utils.translation import gettext_lazy as _
from redis import StrictRedis
from ws4redis import settings as private_settings
from ws4redis.redis_store import RedisMessage

from generic.utils import print_error, print_notice, print_warning
from generic.websocket import LabPublisher
from lab.models import ExerciseNode, IRRNode, WorkNode, monitor_goal_type_choices
from lab.utils.gns3 import get_gns3_node

goal_types = dict(monitor_goal_type_choices).keys()

channel_pattern = re.compile(rb'^server:(\d+)/events$')


class LabTelnet(Telnet):
    def __init__(self, key, host, port):
        super().__init__(host, port, 0.01)
        self.key = key


def run():
    print_notice("Starting telnet relay")

    try:
        redis = StrictRedis(**private_settings.WS4REDIS_CONNECTION)
        subscriber = redis.pubsub()
        subscriber.psubscribe('server:*/events')

        # noinspection PyProtectedMember
        redis_fd = subscriber.connection._sock.fileno()
        sockets = [redis_fd]

        sessions = {}

        while sockets:
            readable, writable, exceptional = select.select(sockets, [], [])
            for s in readable:
                if s is redis_fd:
                    # Data from websocket to telnet
                    message = subscriber.parse_response()
                    msg_type = message.pop(0)
                    if msg_type != b'pmessage':
                        continue

                    pattern, channel, message = message
                    match = channel_pattern.match(channel)
                    if not match:
                        print_warning(_("Malformed channel name: {}").format(channel))
                        continue

                    exercise_id = int(match.group(1))
                    data = json.loads(message)
                    if 'type' not in data or 'node_id' not in data:
                        print_warning(_("Malformed terminal input: {}").format(message))
                        continue

                    if data['type'] != 'terminal-input':
                        # Not for us
                        continue

                    node_id = int(data['node_id'])

                    key = (exercise_id, node_id)
                    if key in sessions:
                        session = sessions[key]
                    else:
                        nodes = list(ExerciseNode.objects
                                     .filter(project_id=exercise_id, id=node_id)
                                     .select_related('project'))
                        if not nodes or not isinstance(nodes[0].template_node, (WorkNode, IRRNode)):
                            print_warning(_("Invalid node-id {node_id} provided for exercise {exercise_id}")
                                          .format(node_id=node_id, exercise_id=exercise_id))
                        node = nodes[0]
                        gns3_node = get_gns3_node(node.project.gns3_id, node.gns3_id)

                        if gns3_node['console_type'] != 'telnet':
                            # We can only handle telnet consoles, put on the ignore list
                            sessions[key] = None
                            continue

                        if gns3_node['console_host'] == '::':
                            host = '::1'
                        elif gns3_node['console_host'] == '0.0.0.0':
                            host = '127.0.0.1'
                        else:
                            host = gns3_node['console_host']

                        port = gns3_node['console']

                        try:
                            session = LabTelnet(key, host, port)
                            print_notice(_("Telnet connection to {} {} established").format(host, port))
                        except ConnectionRefusedError:
                            print_warning(_("Connection refused by {} {}").format(host, port))
                            continue

                        sockets.append(session)
                        sessions[key] = session

                    # If there is no session then ignore the data
                    if not session:
                        continue

                    # Write the data to the session
                    try:
                        session.write(data['data'].encode())
                    except EOFError:
                        # Connection closed, clean up
                        print_warning(_("Telnet connection to {} {} closed").format(session.host, session.port))
                        sockets.remove(s)
                        del sessions[s.key]
                    except (OSError, IOError) as e:
                        print_exc()
                        print_error(e)

                else:
                    # Data from telnet to websocket
                    exercise_id, node_id = s.key
                    try:
                        data = s.read_eager()

                        redis_publisher = LabPublisher(facility='{}/events'.format(exercise_id), broadcast=True)
                        redis_publisher.publish_message(RedisMessage(json.dumps({
                            'type': 'terminal-output',
                            'node_id': node_id,
                            'data': b64encode(data).decode('ascii'),
                        })))

                    except EOFError:
                        # Connection closed, clean up
                        print_warning(_("Telnet connection to {} {} closed").format(s.host, s.port))
                        sockets.remove(s)
                        del sessions[s.key]
                    except (OSError, IOError) as e:
                        print_exc()
                        print_error(e)

    except Exception as e:
        print_exc()
        print_error(e)
