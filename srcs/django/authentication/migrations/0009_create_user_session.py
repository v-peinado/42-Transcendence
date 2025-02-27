from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('sessions', '0001_initial'),  # Ensure sessions app is migrated first
        ('authentication', '0008_add_missing_user_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.customuser')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sessions.session')),
            ],
            options={
                'unique_together': {('user', 'session')},
            },
        ),
    ]
