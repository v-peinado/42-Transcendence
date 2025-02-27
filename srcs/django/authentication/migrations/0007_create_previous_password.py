from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0006_fix_models_import_paths'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreviousPassword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='previous_passwords', to='authentication.customuser')),
            ],
            options={
                'verbose_name': 'Previous Password',
                'verbose_name_plural': 'Previous Passwords',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='previouspassword',
            index=models.Index(fields=['user', '-created_at'], name='authenticati_user_id_19ac48_idx'),
        ),
    ]
