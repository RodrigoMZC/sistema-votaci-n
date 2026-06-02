from rest_framework import serializers
from .models import Poll, Option, Vote
from django.db.models import Count

class OptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = [
            'id', 
            'text', 
            'image', 
            'weight', 
            'vote_count'
        ]
        read_only_fields = ['id']

    def get_vote_count(self, obj):
        return obj.votes.count()


class PollSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    user_voted = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = [
            'id', 
            'title', 
            'description', 
            'type',
            'required_votes',
            'deadline', 
            'is_active', 
            'team', 
            'created_by', 
            'created_at', 
            'options', 
            'user_voted'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'team']

    def get_user_voted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Vote.objects.filter(user=request.user, option__poll=obj).exists()
        return False


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'option', 'voted_at']
        read_only_fields = ['id', 'voted_at']

    def validate(self, data):
        request = self.context.get('request')
        option = data['option']
        poll = option.poll

        # Verificar que la encuesta esté activa
        if not poll.is_active:
            raise serializers.ValidationError('Esta votación ya no está activa.')

        # Verificar que el usuario no haya votado ya
        if Vote.objects.filter(user=request.user, option__poll=poll).exists():
            raise serializers.ValidationError('Ya votaste en esta encuesta.')

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        vote = Vote.objects.create(user=request.user, **validated_data)
        # Verificar cierre automático
        vote.option.poll.check_and_close()
        return vote


class PollResultsSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = [
            'id', 
            'title', 
            'type', 
            'is_active', 
            'total_votes', 
            'winner', 
            'options'
        ]

    def get_options(self, obj):
        results = []
        for option in obj.options.all():
            vote_count = option.votes.count()
            score = vote_count * option.weight if obj.type == 'weighted' else vote_count
            results.append({
                'id': option.id,
                'text': option.text,
                'vote_count': vote_count,
                'score': score,
            })
        return sorted(results, key=lambda x: x['score'], reverse=True)

    def get_total_votes(self, obj):
        return Vote.objects.filter(option__poll=obj).count()

    def get_winner(self, obj):
        options = self.get_options(obj)
        return options[0] if options else None