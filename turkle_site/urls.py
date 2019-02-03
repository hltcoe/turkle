from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from turkle.admin import admin_site
import turkle.views
from turkle_site.settings import TURKLE_EMAIL_ENABLED


admin.autodiscover()

urlpatterns = [
    url(r'^$', turkle.views.index, name='index'),

    # Route based on this "Failproof Favicons" blog post:
    #   http://staticfiles.productiondjango.com/blog/failproof-favicons/
    url(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name="favicon"
    ),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^turkle/', include('turkle.urls')),

    url(r'^admin/', admin_site.urls),

    url(r'^login/$',
        auth_views.LoginView.as_view(
            extra_context={'TURKLE_EMAIL_ENABLED': TURKLE_EMAIL_ENABLED}
        ),
        name="login"),
    url(r'^', include('django.contrib.auth.urls')),
]
