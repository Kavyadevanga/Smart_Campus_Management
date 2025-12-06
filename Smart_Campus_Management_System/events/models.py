from django.db import models
from accounts.models import User

class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    date = models.DateTimeField()

    def __str__(self):
        return self.title


class EventParticipants(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_participated')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')

    class Meta:
        unique_together = ('student', 'event')
