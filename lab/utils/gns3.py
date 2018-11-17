import re
from typing import Union
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from requests import RequestException, Session
from requests.auth import HTTPBasicAuth

# Construct monitor connection option
monitor_option = '-serial tcp:{ADDRESS}:{PORT},reconnect=5'.format(**settings.STATE_COLLECTOR)

GNS3_UUID = Union[UUID, str]

gns3_base_url = 'http://{hostname}:{port}'.format(hostname=settings.GNS3['HOST'], port=settings.GNS3['PORT'])


def raise_exception_on_fail(response, *_args, **_kwargs):
    if response.status_code >= 400:
        raise RequestException(response.reason, response=response)


def get_gns3_session():
    user = settings.GNS3.get('USER', None)
    password = settings.GNS3.get('PASSWORD', None)

    session = Session()
    if user and password:
        session.auth = HTTPBasicAuth(username=user, password=password)

    session.hooks = {
        'response': raise_exception_on_fail
    }

    return session


def get_gns3_projects(*, session: Session = None):
    projects = cache.get('gns3_projects')
    if not projects:
        if not session:
            session = get_gns3_session()
        projects = session.get(gns3_base_url + '/v2/projects').json()
        cache.set('gns3_projects', projects, 10)

    return projects


def get_gns3_nodes(project_id: GNS3_UUID, *, session: Session = None):
    project_id = str(project_id).lower()

    nodes = cache.get('gns3_' + project_id + '_nodes')
    if not nodes:
        if not session:
            session = get_gns3_session()
        nodes = session.get(gns3_base_url + '/v2/projects/' + project_id + '/nodes').json()
        cache.set('gns3_' + project_id + '_nodes', nodes, 3)

    return nodes


def get_gns3_node(project_id: GNS3_UUID, node_id: GNS3_UUID, *, session: Session = None):
    # Optimization: get all (cached) nodes, and get the result from there
    nodes = get_gns3_nodes(project_id, session=session)

    node_id = str(node_id).lower()

    for node in nodes:
        if node['node_id'].lower() == node_id:
            return node

    # Simulate a request error
    raise RequestException('Not Found')


def fix_monitor_option(options):
    options = re.sub(r'(\A|\s)-serial tcp:\d+\.\d+\.\d+\.\d+:\d+,reconnect=\d+(\Z|\s)', ' ', options)
    options += ' ' + monitor_option
    options = re.sub(' +', ' ', options)
    return options.strip()
