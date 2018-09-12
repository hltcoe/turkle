from django.contrib import admin
from django.db import models
from django.forms import TextInput
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from hits.models import Hit, HitBatch, HitTemplate


class HitBatchAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'60'})},
    }
    list_display = ('filename', 'download_csv')

    def download_csv(self, obj):
        download_url = reverse('download_batch_csv', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}">Download CSV results file</a>'.format(download_url))

class HitTemplateAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'60'})},
    }

    # Fieldnames are extracted from form text, and should not be edited directly
    exclude = ('fieldnames',)
    readonly_fields = ('form_fieldnames',)

    def form_fieldnames(self, instance):
        return format_html_join('\n', "<li>{}</li>",
                                ((f, ) for f in instance.fieldnames.keys()))


admin.site.register(Hit)
admin.site.register(HitBatch, HitBatchAdmin)
admin.site.register(HitTemplate, HitTemplateAdmin)
