from django.db import models
from django.contrib.postgres.search import TrigramSimilarity


class Entry(models.Model):
    avar_word = models.CharField(max_length=255)
    russian_translations = models.TextField()
    english_translations = models.TextField()
    example = models.TextField(blank=True)

    def __str__(self):
        return self.avar_word


class SuggestedEntry(models.Model):
    user_id = models.BigIntegerField()
    avar_word = models.CharField(max_length=255)
    russian_translation = models.TextField()
    english_translation = models.TextField(blank=True, null=True)
    example = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.avar_word} (suggested by {self.user_id})"


class AudioEntry(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, null=True, blank=True)
    audio_file = models.FileField(upload_to='audio/')
    telegram_file_id = models.CharField(max_length=255, blank=True)
    uploaded_by = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entry.avar_word} (by user {self.uploaded_by})"