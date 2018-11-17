from datetime import timedelta

from django.conf.global_settings import AUTH_USER_MODEL
from django.db import models
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from macaddress.fields import MACAddressField
from model_utils.managers import InheritanceManager
from requests import RequestException, Session

from lab.fields import InheritanceForeignKey
from lab.utils import get_gns3_nodes
from lab.utils.gns3 import fix_monitor_option, get_gns3_node, get_gns3_session, gns3_base_url, monitor_option

monitor_goal_type_choices = (
    ('Routes IPv4', _('IPv4 routes')),
    ('Routes IPv6', _('IPv6 routes')),
    ('Received traffic', _('Received traffic')),
)
monitor_goal_types = dict(monitor_goal_type_choices)

irr_goal_type_choices = (
    ('NEIGHBORS', _('Import/export')),
    ('ASN IPv4', _('IPv4 from ASN')),
    ('ASN IPv6', _('IPv6 from ASN')),
    ('AS-SET IPv4', _('IPv4 from AS-SET')),
    ('AS-SET IPv6', _('IPv6 from AS-SET')),
)
irr_goal_types = dict(irr_goal_type_choices)


class Project(models.Model):
    gns3_id = models.UUIDField(verbose_name=_('project id'), unique=True, editable=False)
    name = models.CharField(verbose_name=_('name'), max_length=100, editable=False)

    objects = InheritanceManager()

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ('name',)

    def __str__(self):
        return self.name


class Template(Project):
    allow_new_exercises = models.BooleanField(verbose_name=_('allow self-signup'), default=False,
                                              help_text=_('Allow any student to start '
                                                          'this exercise without supervision'))
    default_time_limit = models.PositiveIntegerField(verbose_name=_('default time limit'), null=True, blank=True,
                                                     help_text=_('in minutes'))

    instructions = models.TextField(verbose_name=_('exercise instructions'), blank=True,
                                    help_text=_('Use markdown for styling'))

    class Meta:
        verbose_name = _('exercise template')
        verbose_name_plural = _('exercise templates')

    @property
    def public_name(self):
        name = self.name
        if name.lower().startswith('template'):
            name = name[8:]
        name = name.strip(':_- ')
        return name

    @atomic
    def clone(self, name: str, student: AUTH_USER_MODEL, time_limit=None):
        gns3_id = str(self.gns3_id).lower()

        session = get_gns3_session()

        # We can only duplicate if the project is stopped
        # This should be the current state of templates anyway, but let's make sure...
        session.post(gns3_base_url + '/v2/projects/' + gns3_id + '/nodes/stop')
        result = session.post(gns3_base_url + '/v2/projects/' + gns3_id + '/duplicate', json={
            'name': name,
        }).json()

        try:
            # Open the project so its data becomes available in the API
            exercise_base_url = gns3_base_url + '/v2/projects/' + result['project_id']
            session.post(exercise_base_url + '/open')

            # Store the exercise
            exercise = Exercise(gns3_id=result['project_id'], name=name, student=student, based_on=self)
            if time_limit:
                exercise.deadline = timezone.now() + timedelta(minutes=time_limit)
            exercise.save()

            # The nodes will have different IDs, match them on MAC fix_address
            server_nodes = get_gns3_nodes(exercise.gns3_id)
            for template_node in TemplateNode.objects.select_subclasses().filter(project=self):
                for server_node in server_nodes:
                    if server_node['properties']['mac_address'] == template_node.mac_address:
                        break
                else:
                    raise RuntimeError(_("Node {node.name} ({node.mac_address}) not found in cloned project")
                                       .format(node=template_node))

                new_node = ExerciseNode(
                    project=exercise,
                    gns3_id=server_node['node_id'],
                    name=server_node['name'],
                    mac_address=server_node['properties']['mac_address'],
                    template_node=template_node
                )
                new_node.save()

                # Make sure the monitor option is present when needed
                new_node.gns3_update_monitor_option(session=session)

        except Exception:
            # Clean up: remove the created project
            session.delete(gns3_base_url + '/v2/projects/' + result['project_id'])
            raise

        # Start exercise
        exercise.gns3_start(session=session)

        return exercise


class Exercise(Project):
    student = models.ForeignKey(verbose_name=_('student'), to=AUTH_USER_MODEL, on_delete=models.PROTECT)
    based_on = models.ForeignKey(verbose_name=_('template'), to=Template, on_delete=models.PROTECT)

    started = models.DateTimeField(verbose_name=_('started'), auto_now_add=True)
    deadline = models.DateTimeField(verbose_name=_('deadline'), null=True, blank=True)

    def is_active(self):
        now = timezone.now()
        if self.started > now:
            return False
        if not self.deadline:
            return True

        return now < self.deadline

    def is_running(self):
        try:
            nodes = get_gns3_nodes(str(self.gns3_id))
        except RequestException:
            return None

        total = len(nodes)
        running = len([node for node in nodes if node['status'] == 'started'])
        if running == total:
            return True
        elif running == 0:
            return False
        else:
            return None

    is_running.short_description = _('Running')
    is_running.boolean = True

    def gns3_start(self, *, session=None):
        if not session:
            session = get_gns3_session()

        try:
            session.put(gns3_base_url + '/v2/projects/' + str(self.gns3_id).lower(), json={
                'auto_close': False,
                'auto_open': True,
                'auto_start': True,
            })
            session.post(gns3_base_url + '/v2/projects/' + str(self.gns3_id).lower() + '/nodes/start')
        except RequestException:
            pass

    def gns3_stop(self, *, session=None):
        if not session:
            session = get_gns3_session()

        try:
            session.put(gns3_base_url + '/v2/projects/' + str(self.gns3_id).lower(), json={
                'auto_close': False,
                'auto_open': False,
                'auto_start': False,
            })
            session.post(gns3_base_url + '/v2/projects/' + str(self.gns3_id).lower() + '/nodes/stop')
        except RequestException:
            pass

    def gns3_delete(self, *, session=None):
        if not session:
            session = get_gns3_session()

        self.gns3_stop(session=session)
        try:
            session.delete(gns3_base_url + '/v2/projects/' + str(self.gns3_id).lower())
        except RequestException:
            pass

    class Meta:
        verbose_name = _('exercise')
        verbose_name_plural = _('exercises')


class MonitorTemplate(models.Model):
    name = models.CharField(verbose_name=_('name'), unique=True, max_length=50)
    instructions = models.TextField(verbose_name=_('instructions'), blank=True,
                                    help_text=_('Use markdown for styling'))

    class Meta:
        verbose_name = _('monitor template')
        verbose_name_plural = _('monitor templates')
        ordering = ('name',)

    def __str__(self):
        return self.name


class MonitorGoal(models.Model):
    monitor_template = models.ForeignKey(verbose_name=_('monitor template'), to=MonitorTemplate,
                                         on_delete=models.CASCADE)
    goal_type = models.CharField(verbose_name=_('goal type'), max_length=50, choices=monitor_goal_type_choices)
    goal_content = models.TextField(verbose_name=_('goal content'), blank=True)

    class Meta:
        verbose_name = _('monitor goal')
        verbose_name_plural = _('monitor goals')
        ordering = ('monitor_template__name', 'goal_type')
        unique_together = (
            ('monitor_template', 'goal_type'),
        )

    def __str__(self):
        return _('{template.name}: {goal_type}').format(template=self.monitor_template,
                                                        goal_type=self.get_goal_type_display())


class IRRTemplate(models.Model):
    name = models.CharField(verbose_name=_('name'), unique=True, max_length=50)
    instructions = models.TextField(verbose_name=_('instructions'), blank=True,
                                    help_text=_('Use markdown for styling'))

    class Meta:
        verbose_name = _('IRR template')
        verbose_name_plural = _('IRR templates')
        ordering = ('name',)

    def __str__(self):
        return self.name


class IRRGoal(models.Model):
    irr_template = models.ForeignKey(verbose_name=_('IRR template'), to=IRRTemplate,
                                     on_delete=models.CASCADE)
    goal_type = models.CharField(verbose_name=_('goal type'), max_length=50, choices=irr_goal_type_choices)
    goal_content = models.TextField(verbose_name=_('goal content'), blank=True)

    class Meta:
        verbose_name = _('IRR goal')
        verbose_name_plural = _('IRR goals')
        ordering = ('irr_template__name', 'goal_type')
        unique_together = (
            ('irr_template', 'goal_type'),
        )

    def __str__(self):
        return _('{template.name}: {goal_type}').format(template=self.irr_template,
                                                        goal_type=self.get_goal_type_display())


class Node(models.Model):
    project = InheritanceForeignKey(verbose_name=_('project'), to=Project, on_delete=models.CASCADE)
    gns3_id = models.UUIDField(verbose_name=_('node id'), unique=True, editable=False)
    name = models.CharField(verbose_name=_('name'), max_length=50)
    mac_address = MACAddressField(verbose_name=_('MAC fix_address'))

    objects = InheritanceManager()

    class Meta:
        verbose_name = _('node')
        verbose_name_plural = _('nodes')
        ordering = ('project__name', 'name')
        unique_together = (
            ('project', 'gns3_id'),
            ('project', 'mac_address'),
        )

    def __str__(self):
        return self.name


class TemplateNode(Node):
    pass


class WorkNode(TemplateNode):
    default_username = models.CharField(verbose_name=_('username'), max_length=50, blank=True)
    default_password = models.CharField(verbose_name=_('password'), max_length=50, blank=True)

    instructions = models.TextField(verbose_name=_('instructions'), blank=True,
                                    help_text=_('Use markdown for styling'))

    class Meta:
        verbose_name = _('work node')
        verbose_name_plural = _('work nodes')


class MonitorNode(TemplateNode):
    monitor_template = models.ForeignKey(verbose_name=_('monitor template'), to=MonitorTemplate, blank=True, null=True,
                                         on_delete=models.CASCADE)

    @property
    def instructions(self):
        try:
            return self.monitor_template.instructions
        except MonitorTemplate.DoesNotExist:
            return ''

    class Meta:
        verbose_name = _('monitor node')
        verbose_name_plural = _('monitor nodes')


class IRRNode(TemplateNode):
    maintainer = models.CharField(verbose_name=_('maintainer'), max_length=50, blank=True)
    maintainer_password = models.CharField(verbose_name=_('maintainer password'), max_length=50, blank=True)

    default_username = models.CharField(verbose_name=_('console username'), max_length=50, blank=True)
    default_password = models.CharField(verbose_name=_('console password'), max_length=50, blank=True)

    irr_template = models.ForeignKey(verbose_name=_('IRR template'), to=IRRTemplate, blank=True, null=True,
                                     on_delete=models.CASCADE)

    @property
    def instructions(self):
        try:
            return self.irr_template.instructions
        except MonitorTemplate.DoesNotExist:
            return ''

    class Meta:
        verbose_name = _('IRR node')
        verbose_name_plural = _('IRR nodes')


class ExerciseNode(Node):
    template_node = InheritanceForeignKey(verbose_name=_('template node'), to=TemplateNode, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('exercise node')
        verbose_name_plural = _('exercise nodes')

    def gns3_update_monitor_option(self, *, session: Session = None):
        if not session:
            session = get_gns3_session()

        # This only applies to nodes linked to a monitor node
        if not isinstance(self.template_node, (MonitorNode, IRRNode)):
            return

        server_node = get_gns3_node(self.project.gns3_id, self.gns3_id)

        # Shortcut if option is already ok
        if monitor_option in server_node['properties']['options']:
            return

        project_base_url = gns3_base_url + '/v2/projects/' + server_node['project_id']
        node_base_url = project_base_url + '/nodes/' + server_node['node_id']

        # Remove old monitor options and add new one
        options = fix_monitor_option(server_node['properties']['options'])

        # Push new config and restart the node
        session.put(node_base_url, json={
            'properties': {
                'options': options,
            }
        })

        # Restart if necessary
        if server_node['status'] == 'started':
            self.gns3_stop(session=session)
            self.gns3_start(session=session)

    def gns3_start(self, *, session=None):
        if not session:
            session = get_gns3_session()

        project_base_url = gns3_base_url + '/v2/projects/' + str(self.project.gns3_id).lower()
        node_base_url = project_base_url + '/nodes/' + str(self.gns3_id).lower()

        session.post(node_base_url + '/start')

    def gns3_stop(self, *, session=None):
        if not session:
            session = get_gns3_session()

        project_base_url = gns3_base_url + '/v2/projects/' + str(self.project.gns3_id).lower()
        node_base_url = project_base_url + '/nodes/' + str(self.gns3_id).lower()

        session.post(node_base_url + '/stop')


class ExerciseState(models.Model):
    exercise_node = models.ForeignKey(verbose_name=_('exercise node'), to=ExerciseNode, on_delete=models.CASCADE)
    goal_type = models.CharField(verbose_name=_('goal type'), max_length=50,
                                 choices=monitor_goal_type_choices + irr_goal_type_choices)
    state = models.TextField(verbose_name=_('state'), blank=True)
    last_update = models.DateTimeField(verbose_name=_('last update'), auto_now=True)

    class Meta:
        verbose_name = _('exercise state')
        verbose_name_plural = _('exercise states')
        ordering = ('exercise_node__name', 'goal_type')
        unique_together = (
            ('exercise_node', 'goal_type'),
        )

    def __str__(self):
        return _('{node.name}: {goal_type} at {last_update}').format(node=self.exercise_node,
                                                                     goal_type=self.get_goal_type_display(),
                                                                     last_update=self.last_update)
