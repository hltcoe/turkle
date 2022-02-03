from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
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
