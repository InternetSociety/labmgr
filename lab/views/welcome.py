from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from lab.models import Template


def templates_for_user(user):
    if not user.is_authenticated:
        return Template.objects.none()

    return Template.objects \
        .filter(allow_new_exercises=True) \
        .exclude(id__in=user.exercise_set
                 .exclude(deadline__lt=timezone.now())
                 .values_list('based_on_id', flat=True))


class Welcome(TemplateView):
    template_name = 'welcome.html'

    def get_context_data(self, request, **kwargs):
        return {
            'templates': templates_for_user(request.user),
        }

    def get(self, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        return self.render_to_response(context)


class CloneTemplateView(View):
    # noinspection PyMethodMayBeStatic
    def get(self, *_args, **_kwargs):
        return HttpResponseRedirect('/')

    # noinspection PyMethodMayBeStatic
    def post(self, request, project_id):
        if not request.user.is_authenticated:
            raise PermissionDenied("Not logged in")

        template = get_object_or_404(templates_for_user(request.user), id=project_id)

        # Add student name to project name
        project_name = template.public_name + ' for ' + (request.user.get_full_name() or request.user.username)

        # Clone the template
        exercise = template.clone(name=project_name,
                                  student=request.user,
                                  time_limit=template.default_time_limit)

        # Redirect to the dashboard
        return HttpResponseRedirect(reverse('project_dashboard', kwargs={
            'project_id': exercise.id
        }))
