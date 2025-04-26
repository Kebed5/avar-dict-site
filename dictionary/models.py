from django.db import models

class Entry(models.Model):
    avar_word = models.CharField(max_length=255, unique=True)
    russian_translations = models.TextField()
    english_translations = models.TextField(blank=True, null=True)
    examples = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.avar_word
