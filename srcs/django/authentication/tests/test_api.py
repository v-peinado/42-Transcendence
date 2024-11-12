from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User

class APIViewsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()