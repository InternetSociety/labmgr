from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from lab.models import Exercise, ExerciseNode, IRRNode, MonitorNode, WorkNode
from lab.utils.diagram import ProjectDiagram


class Dashboard(TemplateView):
    template_name = 'lab/dashboard.html'

    def get_context_data(self, request: HttpRequest, project_id, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Not logged in")

        exercise = get_object_or_404(Exercise, pk=project_id)
        if not request.user.is_staff and exercise.student != request.user:
            raise PermissionDenied("No access to that exercise")

        authorized = set(request.session.get('authorized_exercises', []))
        authorized.add(exercise.id)
        request.session['authorized_exercises'] = list(authorized)

        nodes = {}
        for node in exercise.node_set.select_subclasses():
            assert isinstance(node, ExerciseNode)

            node_data = {
                'id': node.id,
                'gns3_id': node.gns3_id,
                'name': node.name,
                'type': node.template_node.__class__.__name__,
                'info': dict(
                    instructions=node.template_node.instructions,
                ),
            }

            if isinstance(node.template_node, (WorkNode, IRRNode)):
                node_data['info'].update(dict(
                    username=node.template_node.default_username,
                    password=node.template_node.default_password,
                ))

            if isinstance(node.template_node, IRRNode):
                node_data['info'].update(dict(
                    maintainer=node.template_node.maintainer,
                    maintainer_password=node.template_node.maintainer_password,
                ))

            if isinstance(node.template_node, (MonitorNode, IRRNode)):
                node_state = {}

                # Put in the goals
                if isinstance(node.template_node, MonitorNode) and node.template_node.monitor_template:
                    goals = node.template_node.monitor_template.monitorgoal_set.all()
                elif isinstance(node.template_node, IRRNode) and node.template_node.irr_template:
                    goals = node.template_node.irr_template.irrgoal_set.all()
                else:
                    goals = []

                for goal in goals:
                    node_state[goal.goal_type] = {
                        'goal_type': goal.goal_type,
                        'goal_type_display': goal.get_goal_type_display(),
                        'state': '',
                        'goal': goal.goal_content,
                        'last_update': None,
                    }

                # Completely skip MonitorNode if there are no goals
                if not node_state:
                    continue

                # Put in the states of those goals
                states = node.exercisestate_set.filter(goal_type__in=node_state.keys())
                for state in states:
                    node_state[state.goal_type]['state'] = state.state
                    node_state[state.goal_type]['last_update'] = state.last_update

                node_data['state'] = node_state

            nodes[node.id] = node_data

        diagram = ProjectDiagram(exercise)
        return {
            'exercise': {
                'id': exercise.id,
                'name': exercise.name,
                'instructions': exercise.based_on.instructions,
                'based_on': exercise.based_on.name,
                'started': exercise.started,
                'deadline': exercise.deadline,
                'nodes': nodes,
            },
            'diagram': diagram.get_data(show_state=True),
        }

    def get(self, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        return self.render_to_response(context)
