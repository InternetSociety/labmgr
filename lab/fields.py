from django.db.models import ForeignKey
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.forms import ModelChoiceField
from model_utils.managers import InheritanceManagerMixin


class UserModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        name = obj.get_full_name() or obj.username
        return "{name} ({email})".format(name=name, email=obj.email)


class InheritanceForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_queryset(self, **hints):
        if isinstance(self.field.remote_field.model.objects, InheritanceManagerMixin):
            # Return most specific subclass for InheritanceManager capable models
            return self.field.remote_field.model.objects.select_subclasses()
        else:
            # Otherwise stick to the default behaviour
            return super().get_queryset(**hints)


# Foreign key that automatically resolves to most-specific subclass
class InheritanceForeignKey(ForeignKey):
    forward_related_accessor_class = InheritanceForwardManyToOneDescriptor
