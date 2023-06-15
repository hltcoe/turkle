from rest_framework.authtoken.admin import TokenAdmin

# required until this is merged in: https://github.com/encode/django-rest-framework/pull/8534
TokenAdmin.autocomplete_fields = ("user",)
