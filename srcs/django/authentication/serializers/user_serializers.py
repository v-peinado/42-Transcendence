from rest_framework import serializers
from authentication.models import CustomUser
import re
from django.contrib.auth.password_validation import validate_password
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

    def validate_username(self, value):
        # Validación de longitud máxima
        max_length = 10  # Define el número máximo de caracteres permitidos
        if len(value) > max_length:
            raise serializers.ValidationError(
                f"El nombre de usuario no puede tener más de {max_length} caracteres"
            )
        
        # Validaciones existentes
        if value.startswith('42.'):
            raise serializers.ValidationError(
                "El prefijo '42.' está reservado para usuarios de 42"
            )
        
        # Nueva validación de caracteres
        if not all(char.isprintable() and not char.isspace() for char in value):
            raise serializers.ValidationError(
                "El nombre de usuario no puede contener espacios ni caracteres especiales"
            )
        
        return value.lower()

    def validate_email(self, value):
        # Validaciones existentes
        if re.match(r'.*@student\.42.*\.com$', value.lower()):
            raise serializers.ValidationError(
                "Los correos con dominio @student.42*.com están reservados para usuarios de 42"
            )
        
        # Nueva validación de caracteres en la parte local del email
        local_part = value.split('@')[0]
        if not all(char.isprintable() and not char.isspace() for char in local_part):
            raise serializers.ValidationError(
                "El email no puede contener espacios ni caracteres especiales en la parte local"
            )
        
        return value.lower()

    def validate_password1(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        if not all(char.isprintable() and not char.isspace() for char in value):
            raise serializers.ValidationError(
                "La contraseña no puede contener espacios ni caracteres especiales"
            )
        return value

    def validate(self, data):
        # Validación de contraseñas
        if data.get('password1') != data.get('password2'):
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden"
            })

        # Validación adicional de nombre de usuario y email
        username = data.get('username', '')
        email = data.get('email', '')

        # Doble verificación para el prefijo 42.
        if '42.' in username.lower():
            raise serializers.ValidationError({
                "username": "No se permite usar '42.' en el nombre de usuario"
            })

        # Doble verificación para email de 42
        if re.search(r'@student\.42.*\.com$', email.lower()):
            raise serializers.ValidationError({
                "email": "No se permite usar correos de 42"
            })

        # Verificar duplicados
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({
                "username": "Este nombre de usuario ya está en uso"
            })
        
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "email": "Este correo electrónico ya está registrado"
            })

        return data

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

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

class TwoFactorVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(style={'input_type': 'password'})
    new_password2 = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data