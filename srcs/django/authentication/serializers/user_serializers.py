from rest_framework import serializers
from authentication.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    is_fortytwo_user = serializers.BooleanField(read_only=True)
    profile_image = serializers.URLField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'username', 
            'email', 
            'password1', 
            'password2',
            'profile_image',
            'is_fortytwo_user',
            'fortytwo_id'
        ]
        read_only_fields = ['profile_image', 'is_fortytwo_user', 'fortytwo_id']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True}
        }

    def validate(self, data):
        # Validar nombre de usuario primero
        if CustomUser.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError({
                "username": "Este nombre de usuario ya está en uso"
            })

        # Validar email
        if CustomUser.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({
                "email": "Este email ya está registrado"
            })

        # Validar contraseñas
        if data.get('password1') != data.get('password2'):
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden"
            })

        return data

    def create(self, validated_data):
        try:
            user = CustomUser.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password1']
            )
            return user
        except Exception as e:
            raise serializers.ValidationError({
                "error": "Error inesperado al crear el usuario"
            })