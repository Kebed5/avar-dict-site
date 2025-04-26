from django.shortcuts import render
from .models import Entry
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import EntrySerializer
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from .forms import SuggestedEntryForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Entry, SuggestedEntry, AudioEntry
from .forms import SuggestedEntryForm, AudioEntryForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages


def search_view(request):
    query = request.GET.get('q', '')
    mode = request.GET.get('mode', 'avar_rus')  # Default search mode
    results = []

    if query:
        if mode == 'avar_rus':
            results = Entry.objects.filter(avar_word__icontains=query)
        elif mode == 'rus_avar':
            results = Entry.objects.filter(russian_translations__icontains=query)
        elif mode == 'avar_eng':
            results = Entry.objects.filter(avar_word__icontains=query)
        elif mode == 'eng_avar':
            results = Entry.objects.filter(english_translations__icontains=query)

    return render(request, 'dictapp/search.html', {
    'results': results,
    'query': query,
    'mode': mode
    })

@api_view(['GET'])
def api_search(request):
    query = request.GET.get('q', '')
    mode = request.GET.get('mode', 'avar_rus')
    entries = []

    if query:
        if mode == 'avar_rus':
            entries = Entry.objects.filter(avar_word__icontains=query)
        elif mode == 'rus_avar':
            entries = Entry.objects.filter(russian_translations__icontains=query)
        elif mode == 'avar_eng':
            entries = Entry.objects.filter(avar_word__icontains=query)
        elif mode == 'eng_avar':
            entries = Entry.objects.filter(english_translations__icontains=query)

    serializer = EntrySerializer(entries, many=True)
    return Response(serializer.data)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'dictapp/register.html', {'form': form})

@login_required
def suggest_entry_view(request):
    if request.method == 'POST':
        form = SuggestedEntryForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.suggested_by = request.user
            suggestion.save()
            messages.success(request, "✅ Your suggestion has been submitted! Thank you!")
            return redirect('search')       
    else:
        form = SuggestedEntryForm()

    return render(request, 'dictapp/suggest_entry.html', {'form': form})


@login_required
def upload_audio_view(request):
    if request.method == 'POST':
        form = AudioEntryForm(request.POST, request.FILES)
        if form.is_valid():
            audio_entry = form.save(commit=False)
            audio_entry.uploaded_by = request.user
            audio_entry.save()
            messages.success(request, "✅ Audio uploaded successfully!")
            return redirect('search')  # After upload, redirect back to search or a thank you page
    else:
        form = AudioEntryForm()

    return render(request, 'dictapp/upload_audio.html', {'form': form})

@staff_member_required
def review_suggestions_view(request):
    suggestions = SuggestedEntry.objects.filter(approved=False)

    return render(request, 'dictapp/review_suggestions.html', {
        'suggestions': suggestions
    })

@staff_member_required
def approve_suggestion_view(request, suggestion_id):
    suggestion = SuggestedEntry.objects.get(id=suggestion_id)

    # Create a new real Entry from the suggestion
    Entry.objects.create(
        avar_word=suggestion.avar_word,
        russian_translations=suggestion.russian_translations,
        english_translations=suggestion.english_translations,
        examples=suggestion.examples,
        created_by=suggestion.suggested_by
    )

    suggestion.approved = True
    suggestion.save()
    messages.success(request, "✅ Suggestion approved and added to dictionary!")
    return redirect('review_suggestions')

@staff_member_required
def reject_suggestion_view(request, suggestion_id):
    suggestion = SuggestedEntry.objects.get(id=suggestion_id)
    suggestion.delete()
    messages.error(request, "❌ Suggestion rejected and deleted.")
    return redirect('review_suggestions')
