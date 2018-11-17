import time
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from django.utils.translation import gettext as _
from requests import RequestException

from generic.utils import print_debug, print_message, print_notice, print_warning, print_error
from lab.models import Exercise, ExerciseNode, Project
from lab.utils import (get_gns3_nodes, get_gns3_projects)
from lab.utils.gns3 import get_gns3_session, gns3_base_url

session = get_gns3_session()


def sync_projects_to_db():
    print_debug("Synchronising projects")

    # Detect projects on the server
    server_projects = get_gns3_projects(session=session)

    # Sync projects
    projects = Project.objects.select_subclasses()
    for project in projects:
        try:
            for server_project in server_projects:
                if server_project['project_id'].lower() == str(project.gns3_id).lower():
                    break
            else:
                # Where did that one go?!?
                print_warning("- " + _("Project {project.name} disappeared from GNS3 server").format(project=project))
                # project.delete()
                continue

            # Open the project so its data becomes available in the API
            session.post(gns3_base_url + '/v2/projects/' + server_project['project_id'] + '/open')

            if server_project['name'] != project.name:
                print_message("- " + _("Project {old_name} renamed to {new_name}")
                              .format(old_name=project.name, new_name=server_project['name']))
                project.name = server_project['name']
                project.save()

            # Sync nodes
            server_nodes = get_gns3_nodes(server_project['project_id'], session=session)
            nodes = project.node_set.select_subclasses()
            for node in nodes:
                for server_node in server_nodes:
                    if server_node['node_id'].lower() == str(node.gns3_id).lower():
                        break
                else:
                    # Where did that one go?!?
                    print_warning("- " + _("Node {node.name} of project {project.name} disappeared from GNS3 server")
                                  .format(node=node, project=project))
                    # node.delete()
                    continue

                if server_node['name'] != node.name:
                    print_message("- " + _("Project {project.name} node {old} renamed to {new}")
                                  .format(project=project, old=node.name, new=server_node['name']))
                    node.name = server_node['name']
                    node.save()

                if server_node['properties']['mac_address'] != node.mac_address:
                    print_message("- " + _("Project {project.name} node {node.name} "
                                           "change MAC fix_address from {old} to {new}")
                                  .format(project=project, node=node, old=node.mac_address,
                                          new=server_node['properties']['mac_address']))
                    node.mac_address = server_node['properties']['mac_address']
                    node.save()

                if isinstance(node, ExerciseNode):
                    node.gns3_update_monitor_option(session=session)

            if isinstance(project, Exercise):
                running = len([node for node in server_nodes if node['status'] == 'started'])

                if running and project.deadline and project.deadline < timezone.now():
                    print_notice(_("Stopping exercise {}").format(project.name))
                    project.gns3_stop(session=session)

                if project.deadline and project.deadline < timezone.now() - timedelta(weeks=1):
                    print_notice(_("Deleting exercise {}").format(project.name))
                    project.delete()
                    continue

        except IntegrityError:
            print_error("  - " + _("Template is still referenced, leaving it for now"))


def run(run_once=False):
    try:
        # Test reachability
        data = session.get(gns3_base_url + '/v2/version').json()
        print_notice(_("Connected to {hostname}:{port} (GNS v{version})").format(hostname=settings.GNS3['HOST'],
                                                                                 port=settings.GNS3['PORT'],
                                                                                 version=data['version']))

        # Run
        while True:
            sync_projects_to_db()

            if run_once:
                return

            time.sleep(10)

    except RequestException as e:
        print(_("Cannot connect to GNS3 server: {}".format(e)))

        if not run_once:
            # Don't exit too quickly, otherwise uwsgi loops too fast
            time.sleep(60)

    except Exception as e:
        print(_('Unexpected error: {}').format(e))
