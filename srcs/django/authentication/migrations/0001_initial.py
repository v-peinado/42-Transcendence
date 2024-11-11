# authentication/migrations/0001_initial.py
from django.db import migrations
from django.contrib.auth.models import User
from django.db import models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE auth_user ADD CONSTRAINT unique_email UNIQUE (email);',
            reverse_sql='ALTER TABLE auth_user DROP CONSTRAINT IF EXISTS unique_email;'
        ),
    ]