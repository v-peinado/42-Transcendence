from rest_framework import serializers
from authentication.models import CustomUser
from authentication.services.password_service import PasswordService
from django.utils.html import escape
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    is_fortytwo_user = serializers.BooleanField(read_only=True)
    profile_image = serializers.URLField(read_only=True)

    class Meta:
        model = CustomUser
        fields = '__all__'
        read_only_fields = ['profile_image', 'is_fortytwo_user', 'fortytwo_id']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True}
        }

    def validate(self, data):
        username = escape(data.get('username', '')).lower()
        email = escape(data.get('email', '')).lower()
        password1 = data.get('password1')
        password2 = data.get('password2')

        try:
            PasswordService.validate_manual_registration(
                username=username,
                email=email,
                password1=password1,
                password2=password2
            )
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        return {
            'username': username,
            'email': email,
            'password1': password1,
            'password2': password2
        }

    def create(self, validated_data):
        validated_data.pop('password2', None)
        password = validated_data.pop('password1', None)
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            is_fortytwo_user=False
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(style={'input_type': 'password'})
    new_password1 = serializers.CharField(style={'input_type': 'password'})
    new_password2 = serializers.CharField(style={'input_type': 'password'})

class TwoFactorVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(style={'input_type': 'password'})
    new_password2 = serializers.CharField(style={'input_type': 'password'})