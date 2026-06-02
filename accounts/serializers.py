from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'avatar', 
            'bio',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']