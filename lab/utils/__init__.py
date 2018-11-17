from lab.utils.gns3 import GNS3_UUID, get_gns3_nodes, get_gns3_projects


def get_unknown_projects():
    from lab.models import Project

    existing_project_ids = [str(project_id).lower() for project_id in
                            Project.objects.all().values_list('gns3_id', flat=True)]

    for project in get_gns3_projects():
        if project['project_id'].lower() in existing_project_ids:
            continue

        yield project


def get_unknown_project_choices():
    choices = []
    for project in get_unknown_projects():
        choices.append((project['project_id'], project['name']))

    choices.sort(key=lambda c: c[1])
    return choices


def get_unknown_nodes(template_id: GNS3_UUID):
    from lab.models import Node

    existing_node_ids = [str(node_id).lower() for node_id in
                         Node.objects.filter(project__gns3_id=template_id).values_list('gns3_id', flat=True)]

    for node in get_gns3_nodes(template_id):
        if node['node_id'].lower() in existing_node_ids:
            continue

        yield node


def get_unknown_node_choices(project_id: GNS3_UUID):
    choices = []
    for node in get_unknown_nodes(project_id):
        choices.append((node['node_id'], node['name']))

    choices.sort(key=lambda c: c[1])
    return choices
