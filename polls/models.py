from django.db import models
from django.conf import settings
from django.urls import reverse
from teams.models import Team
from django.utils import timezone
import uuid

# Create your models here.
class Poll(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TYPE_CHOICES = [
        ('simple', 'Simple'),
        ('weighted', 'Ponderada'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='simple')
    required_votes = models.PositiveIntegerField(default=0, help_text="0 = sin mínimo")
    deadline = models.DateTimeField(null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='polls')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='polls_created'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('polls:detail', kwargs={
            'team_slug': self.team.slug,
            'poll_id': self.id,
        })

    def check_and_close(self):
        # Cierra la encuesta si se cumple alguna condicion de cierre.
        total_votes = Vote.objects.filter(option__poll=self).count()
        if self.required_votes and total_votes >= self.required_votes:
            self.is_active = False
            self.save()
        elif self.deadline and timezone.now() >= self.deadline:
            self.is_active = False
            self.save()
        
class Option(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    image = models.ImageField(upload_to='options/', blank=True, null=True)
    weight = models.FloatField(default=1.0, help_text="Solo aplica en votación ponderada")

    def __str__(self):
        return f"{self.poll} — {self.text}"


class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'option')]

    def __str__(self):
        return f"{self.user} → {self.option}"