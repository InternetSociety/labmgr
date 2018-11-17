from ipaddress import ip_address, ip_network

from django.conf import settings
from django.http import HttpRequest


def allowed(request: HttpRequest):
    """
    Function to determine whether to show the toolbar on a given page.
    """
    if not settings.DEBUG:
        return False

    try:
        remote_addr = ip_address(request.META.get('REMOTE_ADDR', None))
        for subnet in settings.INTERNAL_IPS:
            subnet = ip_network(subnet)
            if remote_addr in subnet:
                return True
    except ValueError:
        pass

    # No access granted
    return False
