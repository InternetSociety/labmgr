import time

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View

from lab.models import Exercise, ExerciseNode
from lab.utils.gns3 import get_gns3_session, gns3_base_url


class StartExerciseView(View):
    # noinspection PyMethodMayBeStatic
    def get(self, *_args, **_kwargs):
        return HttpResponseRedirect('/')

    # noinspection PyMethodMayBeStatic
    def post(self, request, project_id):
        if not request.user.is_authenticated:
            raise PermissionDenied("Not logged in")

        project = get_object_or_404(Exercise, id=project_id)
        if not request.user.is_staff and project.student != request.user:
            raise PermissionDenied("No access to that exercise")

        if project.deadline and timezone.now() > project.deadline:
            # Deadline has passed
            if not request.user.is_staff:
                # Not allowed
                raise PermissionDenied("The deadline has expired for this exercise")

            # Staff gets to remove the deadline
            project.deadline = None
            project.save()

        project.gns3_start()
        while not project.is_running():
            time.sleep(0.2)

        return HttpResponseRedirect('/')


class StopExerciseView(View):
    # noinspection PyMethodMayBeStatic
    def get(self, *_args, **_kwargs):
        return HttpResponseRedirect('/')

    # noinspection PyMethodMayBeStatic
    def post(self, request, project_id):
        if not request.user.is_authenticated:
            raise PermissionDenied("Not logged in")

        project = get_object_or_404(Exercise, id=project_id)
        if not request.user.is_staff and project.student != request.user:
            raise PermissionDenied("No access to that exercise")

        project.gns3_stop()
        while project.is_running():
            time.sleep(0.2)

        return HttpResponseRedirect('/')


class ReloadNodeView(View):
    # noinspection PyMethodMayBeStatic
    def post(self, request, node_id):
        if not request.user.is_authenticated:
            raise PermissionDenied("Not logged in")

        node = get_object_or_404(ExerciseNode, id=node_id)
        if not request.user.is_staff and node.project.student != request.user:
            raise PermissionDenied("No access to that exercise")

        session = get_gns3_session()
        session.post(gns3_base_url + '/v2' +
                     '/projects/' + str(node.project.gns3_id).lower() +
                     '/nodes/' + str(node.gns3_id).lower() + '/stop')
        time.sleep(1)
        session.post(gns3_base_url + '/v2' +
                     '/projects/' + str(node.project.gns3_id).lower() +
                     '/nodes/' + str(node.gns3_id).lower() + '/start')

        return HttpResponse()
