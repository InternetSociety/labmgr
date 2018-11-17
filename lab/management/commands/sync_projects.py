from django.core.management.base import BaseCommand

from lab.mules import sync_projects


class Command(BaseCommand):
    help = 'Manually sync the projects with GNS3'

    def handle(self, *args, **options):
        sync_projects.run(run_once=True)
