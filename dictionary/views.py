from django.shortcuts import render
from .models import Entry
from django.db.models import Q

def search_entries(request):
    query = request.GET.get('q')
    results = []

    if query:
        results = Entry.objects.filter(
            Q(avar_word__icontains=query) |
            Q(russian_translations__icontains=query) |
            Q(english_translations__icontains=query)
        )

    return render(request, 'dictionary/search.html', {'results': results, 'query': query})
