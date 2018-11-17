import re

from lab.utils.gns3 import get_gns3_session, gns3_base_url


class ProjectDiagram:
    def __init__(self, project):
        self.project = project

    @property
    def gns3_id(self):
        return str(self.project.gns3_id).lower()

    @staticmethod
    def get_width(item):
        if 'width' in item:
            return item['width']

        if 'svg' in item:
            match = re.search(r'\b' + r'width="(\d+)"', item['svg'])
            if match:
                return int(match.group(1))

        return 0

    @staticmethod
    def get_height(item):
        if 'height' in item:
            return item['height']

        if 'svg' in item:
            match = re.search(r'\b' + r'height="(\d+)"', item['svg'])
            if match:
                return int(match.group(1))

        return 0

    def get_data(self, show_state=True):
        session = get_gns3_session()

        session.post(gns3_base_url + '/v2/projects/' + self.gns3_id + '/open')
        raw_drawings = session.get(gns3_base_url + '/v2/projects/' + self.gns3_id + '/drawings').json()
        raw_nodes = session.get(gns3_base_url + '/v2/projects/' + self.gns3_id + '/nodes').json()
        raw_links = session.get(gns3_base_url + '/v2/projects/' + self.gns3_id + '/links').json()

        # Normalise coordinates
        xs = [item['x'] for item in raw_nodes + raw_drawings]
        xs += [item['x'] + self.get_width(item) for item in raw_nodes + raw_drawings]
        ys = [item['y'] for item in raw_nodes + raw_drawings]
        ys += [item['y'] + self.get_height(item) for item in raw_nodes + raw_drawings]
        zs = [item['z'] for item in raw_nodes + raw_drawings]

        lowest_x = min(xs)
        lowest_y = min(ys)
        lowest_z = min(zs)
        highest_x = max(xs)
        highest_y = max(ys)

        drawings = []
        for raw_drawing in raw_drawings:
            drawings.append({
                'drawing_id': raw_drawing['drawing_id'],
                'svg': raw_drawing['svg'],
                'x': raw_drawing['x'] - lowest_x,
                'y': raw_drawing['y'] - lowest_y,
                'z': raw_drawing['z'] - lowest_z,
                'rotation': raw_drawing['rotation'],
            })

        nodes = []
        for raw_node in raw_nodes:
            nodes.append({
                'node_id': raw_node['node_id'],
                'status': raw_node['status'],
                'width': raw_node['width'],
                'height': raw_node['height'],
                'symbol': raw_node['symbol'],
                'x': raw_node['x'] - lowest_x,
                'y': raw_node['y'] - lowest_y,
                'z': raw_node['z'] - lowest_z,
                'label': {
                    'style': raw_node['label']['style'],
                    'text': raw_node['label']['text'],
                    'x': raw_node['label']['x'],
                    'y': raw_node['label']['y'],
                    'rotation': raw_node['label']['rotation'],
                }
            })

        links = []
        node_map = {node['node_id']: node for node in nodes}
        for raw_link in raw_links:
            node1 = node_map.get(raw_link['nodes'][0]['node_id'], None)
            node2 = node_map.get(raw_link['nodes'][1]['node_id'], None)
            if not node1 or not node2:
                continue

            link = {
                'x1': node1['x'],
                'y1': node1['y'],
                'x1_offset': node1['width'] / 2,
                'y1_offset': node1['height'] / 2,
                'label1': raw_link['nodes'][0]['label'],

                'x2': node2['x'],
                'y2': node2['y'],
                'x2_offset': node2['width'] / 2,
                'y2_offset': node2['height'] / 2,
                'label2': raw_link['nodes'][1]['label'],
            }
            links.append(link)

        return {
            'show_state': show_state,
            'scene_width': highest_x - lowest_x,
            'scene_height': highest_y - lowest_y,
            'drawings': drawings,
            'links': links,
            'nodes': nodes,
        }
