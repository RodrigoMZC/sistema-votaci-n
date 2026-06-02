from rest_framework import serializers
from .models import Team, TeamMember
from accounts.models import CustomUser

class TeamMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            'id',
            'username', 
            'avatar', 
            'role', 
            'joined_at'
        ]
        read_only_fields = ['id', 'joined_at']

class TeamSerializer(serializers.ModelSerializer):
    members = TeamMemberSerializer(many=True, read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'slug',
            'logo', 
            'description',
            'primary_color',
            'secondary_color',
            'created_by',
            'created_at',
            'members'
        ]
        read_only_fields = [
            'id', 
            'slug', 
            'created_at', 
            'created_by'
        ]