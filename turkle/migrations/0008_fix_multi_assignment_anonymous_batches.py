from django.db import migrations

from turkle.models import Batch


def fix_multi_assignment_anonymous_batches(apps, schema_editor):
    Batch.objects.filter(login_required=False, assignments_per_task__gt=1).update(login_required=True)


class Migration(migrations.Migration):
    dependencies = [
        ('turkle', '0007_auto_20200702_1925'),
    ]

    operations = [
        migrations.RunPython(fix_multi_assignment_anonymous_batches),
    ]
