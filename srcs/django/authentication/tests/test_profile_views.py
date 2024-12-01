from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import CustomUser

class ProfileAPITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)

    def test_update_profile_image(self):
        """Test actualización de imagen de perfil"""
        url = reverse('edit_profile')  # Cambiar de api_profile_image a edit_profile
        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        response = self.client.post(url, {'profile_image': image})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # Redirección

    def test_restore_default_image(self):
        """Test restauración de imagen por defecto"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:api_profile_image')  # Añadir namespace 'api'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)