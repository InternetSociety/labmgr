from django.db.models.signals import pre_delete
from django.dispatch import receiver

from lab.models import Exercise


# noinspection PyUnusedLocal
@receiver(signal=pre_delete, sender=Exercise)
def delete_gns3(sender, instance: Exercise, **_kwargs):
    instance.gns3_delete()
