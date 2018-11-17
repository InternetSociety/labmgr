from django.contrib import admin
from django.contrib.admin.helpers import Fieldset
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escapejs
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin

from lab.apps import LabConfig
from lab.forms import NodeAddForm, StudentAddForm
from lab.models import Exercise, IRRNode, MonitorNode, Template, WorkNode
from lab.utils.diagram import ProjectDiagram
from lab.utils.gns3 import get_gns3_node
from lab.views.utils import DrawingView


class NodeAddView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'admin/lab/template/node_add.html'

    def get_context_data(self, request, object_id, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Not logged in")

        template = get_object_or_404(Template, pk=object_id)
        form_kwargs = {
            'project': template,
            'initial': {
                'project_id': template.id,
                'node_type': 'M',
            }
        }

        if request.method == 'POST':
            form = NodeAddForm(request.POST, **form_kwargs)
            if form.is_valid():
                node = get_gns3_node(template.gns3_id, form.cleaned_data['gns3_id'])

                if form.cleaned_data['node_type'] == 'W':
                    instance = WorkNode(
                        project=template,
                        gns3_id=form.cleaned_data['gns3_id'],
                        name=node['name'],
                        mac_address=node['properties']['mac_address']
                    )
                elif form.cleaned_data['node_type'] == 'M':
                    instance = MonitorNode(
                        project=template,
                        gns3_id=form.cleaned_data['gns3_id'],
                        name=node['name'],
                        mac_address=node['properties']['mac_address']
                    )
                elif form.cleaned_data['node_type'] == 'I':
                    instance = IRRNode(
                        project=template,
                        gns3_id=form.cleaned_data['gns3_id'],
                        name=node['name'],
                        mac_address=node['properties']['mac_address']
                    )
                else:
                    raise Http404

                instance.save()
                if request.POST.get('_addanother'):
                    return {
                        'redirect': reverse('admin:node_add', kwargs={
                            'object_id': template.id
                        }),
                    }
                else:
                    return {
                        'redirect': reverse('admin:lab_template_change', kwargs={
                            'object_id': template.id
                        }),
                    }
        else:
            form = NodeAddForm(**form_kwargs)

        fieldsets = [
            Fieldset(form, fields=form.fields.keys())
        ]

        # Prepare the network drawing and hyperlinks
        drawing_context = ProjectDiagram(template).get_data(show_state=False)
        available_nodes = dict(form.fields['gns3_id'].choices)
        for node in drawing_context['nodes']:
            if node['node_id'] in available_nodes:
                node['link'] = mark_safe(
                    "javascript:document.getElementById('id_gns3_id').value='" + escapejs(node['node_id']) + "'"
                )
            else:
                node['disabled'] = True

        drawing = render_to_string(
            template_name=DrawingView.template_name,
            context=drawing_context,
        )

        context = {
            **admin.site.each_context(request),
            'title': _('Add node to {template.name}').format(template=template),
            'lab_app_name': LabConfig.verbose_name,
            'template_name_plural': Template._meta.verbose_name_plural,
            'template': template,
            'adminform': fieldsets,
            'drawing': drawing,
            'show_save_and_add_another': len(available_nodes) > 1,
        }

        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        if 'redirect' in context:
            return redirect(context['redirect'])
        return self.render_to_response(context)


class StudentAddView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'admin/lab/template/student_add.html'

    def get_context_data(self, request, object_id=None, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Not logged in")

        if object_id:
            template = get_object_or_404(Template, pk=object_id)
            default_time_limit = template.default_time_limit
            title = _('Add student to {template.name}').format(template=template)
        else:
            template = None
            default_time_limit = None
            title = _('Add student')

        form_kwargs = {
            'initial': {
                'template': template,
                'time_limit': default_time_limit,
            }
        }

        if request.method == 'POST':
            form = StudentAddForm(request.POST, **form_kwargs)

            if form.is_valid():
                # Clean up template name
                name = form.cleaned_data['template'].name
                if name.lower().startswith('template'):
                    name = name[8:]
                name = name.strip(':_- ')

                # Add student name to project name
                project_name = name + ' for ' + (
                        form.cleaned_data['student'].get_full_name() or
                        form.cleaned_data['student'].username
                )

                # Clone the template
                form.cleaned_data['template'].clone(name=project_name,
                                                    student=form.cleaned_data['student'],
                                                    time_limit=form.cleaned_data['time_limit'])

                if template:
                    if request.POST.get('_addanother'):
                        return {
                            'redirect': reverse('admin:student_add', kwargs={
                                'object_id': template.id
                            }),
                        }
                    else:
                        return {
                            'redirect': reverse('admin:lab_template_changelist'),
                        }
                else:
                    if request.POST.get('_addanother'):
                        return {
                            'redirect': reverse('admin:lab_exercise_add'),
                        }
                    else:
                        return {
                            'redirect': reverse('admin:lab_exercise_changelist'),
                        }

        else:
            form = StudentAddForm(**form_kwargs)

        fieldsets = [
            Fieldset(form, fields=form.fields.keys())
        ]

        context = {
            **admin.site.each_context(request),
            'title': title,
            'lab_app_name': LabConfig.verbose_name,
            'template_name_plural': Template._meta.verbose_name_plural,
            'exercise_name_plural': Exercise._meta.verbose_name_plural,
            'template': template,
            'templates': Template.objects.all(),
            'adminform': fieldsets,
            'show_save_and_add_another': True,
        }

        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        if 'redirect' in context:
            return redirect(context['redirect'])
        return self.render_to_response(context)
