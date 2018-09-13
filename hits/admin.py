try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.contrib import admin
from django.db import models
from django.forms import FileField, ModelForm, TextInput
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from hits.models import Hit, HitBatch, HitTemplate


class HitBatchForm(ModelForm):
    csv_file = FileField()


class HitBatchAdmin(admin.ModelAdmin):
    fields = ('hit_template', 'name', 'csv_file')
    form = HitBatchForm
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'60'})},
    }
    list_display = ('filename', 'total_hits', 'total_finished_hits', 'download_csv')

    def download_csv(self, obj):
        download_url = reverse('download_batch_csv', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}">Download CSV results file</a>'.format(download_url))

    def save_model(self, request, obj, form, change):
        obj.filename = request.FILES['csv_file']._name
        csv_text = request.FILES['csv_file'].read().decode('utf-8')
        super(HitBatchAdmin, self).save_model(request, obj, form, change)
        csv_fh = StringIO(csv_text)
        obj.create_hits_from_csv(csv_fh)


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
