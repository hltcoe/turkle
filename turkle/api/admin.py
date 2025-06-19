from rest_framework.authtoken.admin import TokenAdmin

# registers the user field for autocomplete in the admin UI
TokenAdmin.autocomplete_fields = ("user",)
