from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import TokenProxy

from ..admin import admin_site

admin_site.register(TokenProxy, TokenAdmin)
