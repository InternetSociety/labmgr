# Merge default settings and local settings without creating an import loop
# if local_settings wants to imports default_settings
from .default_settings import *

try:
    from .local_settings import *
except ImportError:
    raise RuntimeError("Local settings not found!") from None

if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
