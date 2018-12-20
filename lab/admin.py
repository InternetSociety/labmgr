from django import template
from django.contrib import admin
from django.db.models import Count, Q
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedModelAdmin, NestedStackedInline

import lab.views.admin
from lab.forms import AddTemplateForm
from lab.models import (Exercise, ExerciseNode, ExerciseState, IRRGoal, IRRNode, IRRTemplate, MonitorGoal, MonitorNode,
                        MonitorTemplate, Template, WorkNode, irr_goal_types, monitor_goal_types)
from lab.utils import get_unknown_nodes
from lab.utils.diagram import ProjectDiagram
from lab.utils.gns3 import get_gns3_session
from lab.views.utils import DrawingView


class InlineMonitorGoalAdmin(admin.StackedInline):
    model = MonitorGoal
    extra = 0


@admin.register(MonitorTemplate)
class MonitorTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin_goal_types')
    inlines = (InlineMonitorGoalAdmin,)

    def admin_goal_types(self, instance: MonitorTemplate):
        goal_types = instance.monitorgoal_set.order_by('goal_type').values_list('goal_type', flat=True)
        return mark_safe(', '.join([escape(str(monitor_goal_types[goal_type])) for goal_type in goal_types]))

    admin_goal_types.short_description = _('Goal types')


class InlineIRRGoalAdmin(admin.StackedInline):
    model = IRRGoal
    extra = 0


@admin.register(IRRTemplate)
class IRRTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin_goal_types')
    inlines = (InlineIRRGoalAdmin,)

    def admin_goal_types(self, instance: IRRTemplate):
        goal_types = instance.irrgoal_set.order_by('goal_type').values_list('goal_type', flat=True)
        return mark_safe(', '.join([escape(str(irr_goal_types[goal_type])) for goal_type in goal_types]))

    admin_goal_types.short_description = _('Goal types')


class InlineWorkNodeAdmin(admin.StackedInline):
    model = WorkNode
    fields = ('default_username', 'default_password', 'instructions')
    readonly_fields = ('name',)

    def has_add_permission(self, request, obj):
        # We have a custom implementation for adding nodes
        return False


class InlineMonitorNodeAdmin(admin.StackedInline):
    model = MonitorNode
    fields = ('monitor_template', 'instructions')
    readonly_fields = ('name', 'instructions')

    def has_add_permission(self, request, obj):
        # We have a custom implementation for adding nodes
        return False


class InlineIRRNodeAdmin(admin.StackedInline):
    model = IRRNode
    fields = ('irr_template', 'maintainer', 'maintainer_password', 'instructions')
    readonly_fields = ('name', 'instructions')

    def has_add_permission(self, request, obj):
        # We have a custom implementation for adding nodes
        return False


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'allow_new_exercises', 'default_time_limit', 'admin_nodes', 'admin_students')
    list_filter = ('allow_new_exercises', 'default_time_limit')
    readonly_fields = ('name', 'gns3_id',)
    fields = ('name', 'gns3_id', 'instructions', 'allow_new_exercises', 'default_time_limit')
    ordering = ('name',)
    inlines = (InlineWorkNodeAdmin, InlineMonitorNodeAdmin, InlineIRRNodeAdmin)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(student_count=Count('exercise'))

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and not add:
            # Prepare the network drawing and hyperlinks
            drawing_context = ProjectDiagram(obj).get_data(show_state=False)
            drawing = render_to_string(
                template_name=DrawingView.template_name,
                context=drawing_context,
            )

            remaining_nodes = get_unknown_nodes(obj.gns3_id)
            can_add_nodes = len(list(remaining_nodes)) > 0

            context.update({
                'drawing': drawing,
                'can_add_nodes': can_add_nodes,
            })
        return super().render_change_form(request=request, context=context, add=add, change=change, form_url=form_url,
                                          obj=obj)

    def get_urls(self):
        wrap = self.admin_site.admin_view

        urls = [
            path('<path:object_id>/nodes/add/', wrap(lab.views.admin.NodeAddView.as_view()), name='node_add'),
            path('<path:object_id>/students/add/', wrap(lab.views.admin.StudentAddView.as_view()), name='student_add'),
        ]
        urls += super().get_urls()

        return urls

    def get_fieldsets(self, request, obj=None):
        if not obj:
            # Overrule default field set
            return [(None, {
                'fields': ['available_templates', 'allow_new_exercises', 'default_time_limit']
            })]
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if not obj:
            defaults['form'] = AddTemplateForm
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []

        return super().get_inline_instances(request=request, obj=obj)

    def admin_nodes(self, instance: Template):
        work_nodes = WorkNode.objects.filter(project=instance).count()
        monitor_nodes = MonitorNode.objects.filter(project=instance).count()
        irr_nodes = IRRNode.objects.filter(project=instance).count()

        tpl = template.Template("""
             {% load i18n %}
             {% blocktrans count count=work_nodes %}
                 {{ count }} work node
             {% plural %}
                 {{ count }} work nodes
             {% endblocktrans %}
             <br>
             {% blocktrans count count=monitor_nodes %}
                 {{ count }} monitor node
             {% plural %}
                 {{ count }} monitor nodes
             {% endblocktrans %}
             <br>
             {% blocktrans count count=irr_nodes %}
                 {{ count }} IRR node
             {% plural %}
                 {{ count }} IRR nodes
             {% endblocktrans %}
         """)
        return tpl.render(template.Context({
            'work_nodes': work_nodes,
            'monitor_nodes': monitor_nodes,
            'irr_nodes': irr_nodes,
        }))

    admin_nodes.short_description = _('Nodes')

    def admin_students(self, instance):
        tpl = template.Template("""
             {% load i18n %}
             <a href="{% url 'admin:lab_exercise_changelist' %}?based_on__project_ptr__exact={{ instance.pk }}">
                 {% blocktrans count count=instance.student_count %}
                     {{ count }} student
                 {% plural %}
                     {{ count }} students
                 {% endblocktrans %}
             </a>
             <br>
             <a href="{% url 'admin:student_add' object_id=instance.id %}">{% trans "Add student" %}</a>
         """)
        return tpl.render(template.Context({
            'instance': instance
        }))

    admin_students.short_description = _('Students')
    admin_students.admin_order_field = 'student_count'


class InlineExerciseState(NestedStackedInline):
    model = ExerciseState
    fields = ('admin_state',)
    readonly_fields = ('admin_state',)

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def admin_state(self, instance: ExerciseState):
        return mark_safe('<span style="font-family: monospace; white-space: pre; line-height: 100%;">' +
                         escape(instance.state) + '</span>')

    admin_state.short_description = _('State')


class InlineExerciseNode(NestedStackedInline):
    model = ExerciseNode
    exclude = ('name', 'mac_address', 'template_node')
    inlines = [InlineExerciseState]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(Q(template_node__in=MonitorNode.objects.all()) | Q(template_node__in=IRRNode.objects.all()))

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Exercise)
class ExerciseAdmin(NestedModelAdmin):
    list_display = ('student', 'name', 'based_on', 'started', 'deadline', 'is_running', 'admin_dashboard')
    list_filter = ('based_on', 'student')
    readonly_fields = ('name', 'gns3_id', 'admin_student', 'based_on', 'started')
    fields = ('name', 'gns3_id', 'admin_student', 'based_on', 'started', 'deadline')
    ordering = ('name',)
    inlines = (InlineExerciseNode,)
    actions = ['start_exercise', 'stop_exercise']

    # noinspection PyMethodMayBeStatic
    def start_exercise(self, _request, queryset):
        session = get_gns3_session()
        for exercise in queryset:
            exercise.deadline = None
            exercise.save()
            exercise.gns3_start(session=session)

    start_exercise.short_description = _('Start exercise')

    # noinspection PyMethodMayBeStatic
    def stop_exercise(self, _request, queryset):
        session = get_gns3_session()
        for exercise in queryset:
            exercise.deadline = timezone.now()
            exercise.save()
            exercise.gns3_stop(session=session)

    stop_exercise.short_description = _('Stop exercise')

    def add_view(self, request, form_url='', extra_context=None):
        return lab.views.admin.StudentAddView.as_view()(request, extra_context=extra_context)

    def admin_dashboard(self, instance: Exercise):
        url = reverse('project_dashboard', kwargs={
            'project_id': instance.id
        })
        return mark_safe('<a href="{url}" target="_blank">{title}</a>'.format(
            url=escape(url),
            title=escape(_("Dashboard"))
        ))

    admin_dashboard.short_description = _('Dashboard')

    def admin_student(self, instance: Exercise):
        name = instance.student.get_full_name() or instance.student.username
        return "{name} ({email})".format(name=name, email=instance.student.email)

    admin_student.short_description = _('Student')
