from django.conf import settings
from django.contrib.auth.views import PasswordResetView
from django.contrib import admin
from django.urls import include, path
from turkle.admin import admin_site

admin.autodiscover()

urlpatterns = [
    # backward compatibility - remove with Turkle 3.0 release
    path('turkle/', include('turkle.urls')),

    path('admin/', admin_site.urls),
    path('', include('django.contrib.auth.urls')),
    path('', include('turkle.urls')),
]

# for sending emails behind proxies
if hasattr(settings, 'TURKLE_EMAIL_CONTEXT'):
    pass_reset = path('password_reset/', PasswordResetView.as_view(
        extra_email_context=settings.TURKLE_EMAIL_CONTEXT), name='password_reset')
    urlpatterns = [pass_reset] + urlpatterns
