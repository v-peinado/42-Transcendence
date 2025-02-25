from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0004_customuser_fortytwo_image'),  # Actualizado a la última migración
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='inactivity_notified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='inactivity_notification_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
