from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class LabManagerAdminConfig(AdminConfig):
    default_site = 'generic.admin.LabManagerAdminSite'


class LabManagerAdminSite(AdminSite):
    # Text to put at the end of each page's <title>.
    @property
    def site_title(self):
        return settings.SITE_TITLE

    # Text to put in each page's <h1>.
    @property
    def site_header(self):
        return settings.SITE_HEADER

    # Text to put at the top of the admin index page.
    @property
    def index_title(self):
        return settings.INDEX_TITLE
