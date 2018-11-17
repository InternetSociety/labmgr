from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic import RedirectView
from django_registration.backends.activation.views import RegistrationView

import lab.views
import lab.views.welcome
from lab.forms import MyRegistrationForm

urlpatterns = [
    path('', lab.views.welcome.Welcome.as_view(), name='welcome'),
    path('', RedirectView.as_view(url='/admin/')),
    path('admin/', admin.site.urls),
    path('accounts/register/', RegistrationView.as_view(form_class=MyRegistrationForm),
         name='django_registration_register'),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('nested_admin/', include('nested_admin.urls')),
    path('lab/', include('lab.urls')),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]

    except ImportError:
        pass
