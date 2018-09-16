try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.contrib import admin
from django.db import models
from django.forms import FileField, ModelForm, TextInput, ValidationError
from django.urls import reverse
from django.utils.html import format_html, format_html_join
import unicodecsv

from hits.models import Hit, HitBatch, HitTemplate


class HitBatchForm(ModelForm):
    csv_file = FileField()

    def clean(self):
        cleaned_data = super(HitBatchForm, self).clean()

        csv_file = cleaned_data.get("csv_file", False)
        hit_template = cleaned_data.get("hit_template", False)

        validation_errors = []

        rows = unicodecsv.reader(csv_file)
        header = rows.next()

        csv_fields = set(header)
        template_fields = set(hit_template.fieldnames)
        if csv_fields != template_fields:
            csv_but_not_template = csv_fields.difference(template_fields)
            if csv_but_not_template:
                validation_errors.append(
                    ValidationError(
                        'The CSV file contained fields that are not in the HIT template. '
                        'These extra fields are: %s' %
                        ', '.join(csv_but_not_template)))
            template_but_not_csv = template_fields.difference(csv_fields)
            if template_but_not_csv:
                validation_errors.append(
                    ValidationError(
                        'The CSV file is missing fields that are in the HIT template. '
                        'These missing fields are: %s' %
                        ', '.join(template_but_not_csv)))

        expected_fields = len(header)
        for (i, row) in enumerate(rows):
            if len(row) != expected_fields:
                validation_errors.append(
                    ValidationError(
                        'The CSV file header has %d fields, but line %d has %d fields' %
                        (expected_fields, i+2, len(row))))

        if validation_errors:
            raise ValidationError(validation_errors)

        # Rewind file, so it can be re-read
        csv_file.seek(0)


class HitBatchAdmin(admin.ModelAdmin):
    fields = ('hit_template', 'name', 'filename', 'csv_file')
    form = HitBatchForm
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'60'})},
    }
    list_display = ('filename', 'total_hits', 'total_finished_hits', 'download_csv')
    readonly_fields = ('filename',)

    def download_csv(self, obj):
        download_url = reverse('download_batch_csv', kwargs={'batch_id': obj.id})
        return format_html('<a href="{}">Download CSV results file</a>'.format(download_url))

    def save_model(self, request, obj, form, change):
        obj.filename = request.FILES['csv_file']._name
        csv_text = request.FILES['csv_file'].read()
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
