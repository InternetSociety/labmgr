from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationForm

from lab.fields import UserModelChoiceField
from lab.models import Template
from lab.utils import get_unknown_node_choices, get_unknown_project_choices

User = get_user_model()


class MyRegistrationForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            'first_name',
            'last_name',
            User.get_email_field_name(),
            'password1',
            'password2'
        ]


class AddTemplateForm(forms.ModelForm):
    available_templates = forms.ChoiceField(label=_('Available templates'), choices=get_unknown_project_choices)

    class Meta:
        model = Template
        fields = ('available_templates', 'allow_new_exercises', 'default_time_limit')

    def clean(self):
        if 'available_templates' in self.cleaned_data:
            self.instance.gns3_id = self.cleaned_data['available_templates']

            for key, value in self.fields['available_templates'].choices:
                if key == self.cleaned_data['available_templates']:
                    self.instance.name = value
                    break
            else:
                raise ValidationError(
                    _('Name for project {} not found').format(self.cleaned_data['available_templates']),
                    code='invalid_choice',
                    params={
                        'value': self.cleaned_data['available_templates']
                    },
                )

        super().clean()


class NodeAddForm(forms.Form):
    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gns3_id'] = forms.ChoiceField(label=_('Available nodes'),
                                                   choices=get_unknown_node_choices(project.gns3_id))

    gns3_id = forms.ChoiceField(label=_('Available nodes'), choices=[])
    node_type = forms.ChoiceField(label=_('Node type'), choices=[
        ('W', _('Node for student to work on')),
        ('M', _('Node for monitor the results of the work')),
        ('I', _('Node with an IRR database')),
    ])


class StudentAddForm(forms.Form):
    template = forms.ModelChoiceField(label=_('Exercise template'), queryset=Template.objects.all())
    student = UserModelChoiceField(label=_('Student'), queryset=get_user_model().objects.all())
    time_limit = forms.IntegerField(label=_('Time limit'), required=False, help_text=_('in minutes'))

    def clean(self):
        super().clean()
