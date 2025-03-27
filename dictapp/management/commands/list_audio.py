from django.core.management.base import BaseCommand
from dictapp.models import AudioEntry

class Command(BaseCommand):
    help = 'List all audio entries with Avar word and audio URL'

    def handle(self, *args, **kwargs):
        for audio in AudioEntry.objects.all():
            self.stdout.write(f"{audio.entry.avar_word} - {audio.audio_file.url}")
