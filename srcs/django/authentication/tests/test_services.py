from .test_base import BaseTestCase 
from ..services.auth_service import AuthenticationService
from ..services.password_service import PasswordService
from django.urls import reverse

class AuthServiceTest(BaseTestCase):
    def test_login(self):
        # Tests para AuthenticationService
        pass

class ViewsTest(BaseTestCase):
    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)