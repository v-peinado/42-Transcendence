# authentication/tests/test_base.py
from django.test import TestCase
from ..models import CustomUser

class BaseTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )