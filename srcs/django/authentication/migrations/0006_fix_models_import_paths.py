from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0005_add_inactivity_fields'),
    ]

    operations = [
        # Only update CustomUser verbose_name options since the model definitely exists
        migrations.AlterModelOptions(
            name='customuser',
            options={'verbose_name': 'User', 'verbose_name_plural': 'Users'},
        ),
        # We'll add PreviousPassword in the next migration
    ]
