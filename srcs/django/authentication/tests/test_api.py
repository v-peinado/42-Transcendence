from rest_framework.test import APITestCase
from django.urls import reverse
from ..models import CustomUser

class APITests(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.user.is_active = True
        self.user.email_verified = True  
        self.user.save()

    def test_login_api(self):
        url = reverse('api:api_login')
        
        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password'] 
        }
        response = self.client.post(url, login_data, format='json')
        self.assertIn(response.status_code, [200, 302])

    def test_register_api(self):
        url = reverse('api:api_register')
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'NewPassword123!',
            'password2': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, 201)

    def test_edit_profile_api(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:api_edit_profile')
        response = self.client.patch(url, {
            'email': 'updated@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')