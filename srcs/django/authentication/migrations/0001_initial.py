from django.db import migrations, models
import django.contrib.auth.models
import django.utils.timezone
import django.contrib.auth.validators
import authentication.models.user

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()])),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('email_hash', models.CharField(db_index=True, max_length=64, null=True, unique=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('fortytwo_image', models.URLField(blank=True, max_length=500, null=True)),
                ('fortytwo_id', models.CharField(blank=True, max_length=50, null=True)),
                ('is_fortytwo_user', models.BooleanField(default=False)),
                ('email_verified', models.BooleanField(default=False)),
                ('email_verification_token', models.CharField(blank=True, max_length=255, null=True)),
                ('email_token_created_at', models.DateTimeField(blank=True, null=True)),
                ('two_factor_enabled', models.BooleanField(default=False)),
                ('two_factor_secret', models.CharField(blank=True, max_length=32, null=True)),
                ('last_2fa_code', models.CharField(blank=True, max_length=6, null=True)),
                ('last_2fa_time', models.DateTimeField(blank=True, null=True)),
                ('pending_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('pending_email_token', models.CharField(blank=True, max_length=255, null=True)),
                ('inactivity_notified', models.BooleanField(default=False)),
                ('inactivity_notification_date', models.DateTimeField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='customuser_set', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='customuser_set', to='auth.permission')),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
