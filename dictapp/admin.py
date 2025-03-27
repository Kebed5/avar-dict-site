from django.contrib import admin
from .models import AudioEntry, Entry, SuggestedEntry
from django.utils.html import format_html

# Register AudioEntry (if no custom admin needed)
admin.site.register(AudioEntry)

# ✅ Entry with custom admin
@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('avar_word', 'russian_translations', 'english_translations', 'example')

# ✅ SuggestedEntry with approval action
@admin.register(SuggestedEntry)
class SuggestedEntryAdmin(admin.ModelAdmin):
    list_display = ('avar_word', 'russian_translation', 'english_translation', 'example', 'user_id')
    actions = ['approve_entries']

    @admin.action(description="✅ Approve selected suggestions")
    def approve_entries(self, request, queryset):
        created = 0
        for suggestion in queryset:
            Entry.objects.create(
                avar_word=suggestion.avar_word,
                russian_translations=suggestion.russian_translation,
                english_translations=suggestion.english_translation,
                example=suggestion.example
            )
            suggestion.delete()
            created += 1

        self.message_user(request, f"{created} entries approved and moved to Entry model.")


class AudioEntryAdmin(admin.ModelAdmin):
    list_display = ('entry', 'user_id', 'audio_tag')

    def audio_tag(self, obj):
        if obj.audio_file:
            return format_html('<audio controls src="{}"></audio>', obj.audio_file.url)
        return "No audio"
    audio_tag.short_description = "Audio Preview"