from django.conf.urls import include, url
from django.contrib import admin

from hits.admin import admin_site
import hits.views


admin.autodiscover()

urlpatterns = [
    # Examples:
    url(r'^$', hits.views.index, name='index'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^hits/', include('hits.urls')),

    url(r'^admin/', admin_site.urls),

    url('^', include('django.contrib.auth.urls')),
]
