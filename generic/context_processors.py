from django.conf import settings


# noinspection PyUnusedLocal
def site_title(request):
    return {
        'site_title': settings.SITE_TITLE,
        'site_header': settings.SITE_HEADER,
    }
