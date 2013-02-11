from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'turkle.views.home', name='home'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^hits/', include('hits.urls')),

    # Welcome pages
    #url(r'^welcome/$')
    #url(r'^welcome?variant=worker/$')
    #url(r'^welcome?variant=requester/$')

    url(r'^admin/', include(admin.site.urls)),

)
