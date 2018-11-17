import json
import re
import select
import socket

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from redis import StrictRedis
from ws4redis import settings as private_settings
from ws4redis.redis_store import RedisMessage

from generic.utils import print_debug, print_error, print_message, print_notice, print_warning
from generic.websocket import LabPublisher
from lab.models import ExerciseNode, ExerciseState, IRRNode, irr_goal_types, monitor_goal_types

channel_pattern = re.compile(rb'^server:(\d+)/events$')


class StateConnection:
    header = re.compile(r'^\*\*\*\*\*\[ +(.*?) +\]\*\*\*\*\*$')

    def __init__(self, connection: socket.socket):
        self.connection = connection
        self.buffer = ''
        self.uuid = None
        self.node = None

        self.current_section_name = None
        self.current_section = ''

    def collect_data(self):
        data = self.connection.recv(1024)
        if not data:
            # The end
            return False

        self.buffer += data.decode('utf-8')

        while True:
            parts = self.buffer.split('\n', 1)
            if len(parts) == 1:
                # No newline, still building a line, done for now
                return True

            # We have a line! Store remainder and process the line
            line = parts[0].rstrip()
            self.buffer = parts[1]

            # Check if a new section begins
            match = self.header.match(line)
            if match:
                # First submit the previous section, if any
                self.submit()

                name = match.group(1)
                if self.node and name == 'END':
                    print_debug(_('Submitted {node.name} state of {exercise.name}').format(section=name, node=self.node,
                                                                                           exercise=self.node.project))
                    self.current_section_name = None
                else:
                    self.current_section_name = name

                self.current_section = ''
            else:
                # Not a section start, so add to current section
                self.current_section += line + '\n'

    @atomic
    def submit(self):
        # Remember
        name = self.current_section_name
        content = self.current_section

        # Clear the state vars
        self.current_section_name = None
        self.current_section = ''

        # Do we have any data?
        if not name:
            return

        # Process
        if name == 'UUID':
            # This is the UUID of the node
            self.uuid = content.strip().lower()

        if not self.uuid:
            # We can't do anything yet
            return

        if not self.node:
            try:
                self.node = ExerciseNode.objects.get(gns3_id=self.uuid)
            except ExerciseNode.DoesNotExist:
                print_error(_('Unable to submit {section} of {uuid}').format(section=name, uuid=self.uuid))
                return

        if name in monitor_goal_types or name in irr_goal_types:
            state, created = ExerciseState.objects.select_for_update().get_or_create(defaults={
                'state': content,
            }, exercise_node=self.node, goal_type=name)

            if state.state != content:
                # State changed
                state.state = content
                state.save()

            redis_publisher = LabPublisher(facility='{}/events'.format(self.node.project_id), broadcast=True)
            redis_publisher.publish_message(RedisMessage(json.dumps({
                'type': 'state',
                'goal_type': name,
                'node': self.node.id,
                'content': content,
                'ts': state.last_update,
            }, cls=DjangoJSONEncoder)))
        elif name in ['QUERY-RESULT', 'UPDATE-RESULT']:
            redis_publisher = LabPublisher(facility='{}/events'.format(self.node.project_id), broadcast=True)
            redis_publisher.publish_message(RedisMessage(json.dumps({
                'type': 'irr-query-response' if name == 'QUERY-RESULT' else 'irr-update-response',
                'node': self.node.id,
                'request': 'irr-query' if name == 'QUERY-RESULT' else 'irr-update',
                'response': content,
            }, cls=DjangoJSONEncoder)))

        elif name != 'UUID':
            print_error(_("Unknown section name: [{}] from {}").format(name, self.uuid))

    def send_message(self, data):
        # We only know how to send messages to IIR nodes
        if not self.node or not isinstance(self.node.template_node, IRRNode):
            return

        if data['type'] == 'irr-query':
            self.connection.send(b"*****[ QUERY ]*****\n")
            self.connection.send(data['query'].encode() + b'\n')
            self.connection.send(b"*****[ END ]*****\n")

        elif data['type'] == 'irr-update':
            self.connection.send(b"*****[ UPDATE ]*****\n")
            self.connection.send(data['update'].encode() + b'\n')
            self.connection.send(b"*****[ END ]*****\n")

    def fileno(self):
        return self.connection.fileno()

    def close(self):
        return self.connection.close()


def run():
    try:
        print_notice(_("Listening for state updates on {addr}:{port}").format(
            addr=settings.STATE_COLLECTOR['ADDRESS'],
            port=settings.STATE_COLLECTOR['PORT'],
        ))

        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_sock.setblocking(False)
        listen_sock.bind((settings.STATE_COLLECTOR['ADDRESS'], settings.STATE_COLLECTOR['PORT']))
        listen_sock.listen(128)

        redis = StrictRedis(**private_settings.WS4REDIS_CONNECTION)
        subscriber = redis.pubsub()
        subscriber.psubscribe('server:*/events')

        # noinspection PyProtectedMember
        redis_fd = subscriber.connection._sock.fileno()

        sockets = [listen_sock, redis_fd]

        while sockets:
            readable, writable, exceptional = select.select(sockets, [], [])

            for s in readable:
                if s is listen_sock:
                    connection, client_address = s.accept()
                    print_message("Incoming state connection from {addr}".format(addr=client_address))
                    connection.setblocking(False)
                    sockets.append(StateConnection(connection))

                    # Ask for ID
                    connection.send(b"*****[ ID ]*****\n")
                    connection.send(b"*****[ END ]*****\n")

                    continue

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

                    if data['type'] not in ['irr-query', 'irr-update']:
                        # Not for us
                        continue

                    node_id = int(data['node_id'])

                    # Find the connection belonging to this exercise node
                    for sc in sockets:
                        if isinstance(sc, StateConnection) and sc.node and \
                                sc.node.project_id == exercise_id and sc.node.id == node_id:
                            break
                    else:
                        print_warning(_("No existing connection found for exercise {exercise} node {node}")
                                      .format(exercise=exercise_id, node=node_id))

                        redis_publisher = LabPublisher(facility='{}/events'.format(exercise_id), broadcast=True)
                        redis_publisher.publish_message(RedisMessage(json.dumps({
                            'type': data['type'] + '-response',
                            'node': node_id,
                            'response': 'Server is not yet available',
                        }, cls=DjangoJSONEncoder)))

                        continue

                    sc.send_message(data)
                    continue

                result = s.collect_data()
                if not result:
                    # End of connection
                    print_message("Lost state connection from {addr}".format(addr=s.connection.getpeername()))
                    sockets.remove(s)
                    s.close()

    except Exception as e:
        print_error(e)
