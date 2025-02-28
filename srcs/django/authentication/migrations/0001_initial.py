# Generated manually - clean migration from scratch

from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
import django.db.models.deletion
import authentication.models.user


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('sessions', '0001_initial'),
    ]

    operations = [
        # CustomUser model
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                
                # Custom fields
                ('fortytwo_image', models.URLField(max_length=500, blank=True, null=True)),
                ('profile_image', models.ImageField(upload_to=authentication.models.user.CustomUser.profile_image_path, null=True, blank=True)),
                ('fortytwo_id', models.CharField(max_length=50, blank=True, null=True)),
                ('is_fortytwo_user', models.BooleanField(default=False)),
                ('email_verified', models.BooleanField(default=False)),
                ('email_verification_token', models.CharField(max_length=255, blank=True, null=True)),
                ('email_token_created_at', models.DateTimeField(null=True, blank=True)),
                ('two_factor_enabled', models.BooleanField(default=False)),
                ('two_factor_secret', models.CharField(max_length=32, blank=True, null=True)),
                ('last_2fa_code', models.CharField(max_length=6, blank=True, null=True)),
                ('last_2fa_time', models.DateTimeField(null=True)),
                ('pending_email', models.EmailField(blank=True, null=True)),
                ('pending_email_token', models.CharField(max_length=255, blank=True, null=True)),
                ('inactivity_notified', models.BooleanField(default=False)),
                ('inactivity_notification_date', models.DateTimeField(null=True, blank=True)),
                
                # Relations
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        
        # PreviousPassword model
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
        
        # UserSession model
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
                'app_label': 'authentication',
            },
        ),
        
        # Index for PreviousPassword
        migrations.AddIndex(
            model_name='previouspassword',
            index=models.Index(fields=['user', '-created_at'], name='authenticati_user_id_19ac48_idx'),
        ),
    ]
