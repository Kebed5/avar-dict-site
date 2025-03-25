from django.shortcuts import render
from .models import Entry

def search_view(request):
    query = request.GET.get('q')
    results = []

    if query:
        results = Entry.objects.filter(avar_word__icontains=query)

    return render(request, 'dictapp/search.html', {
        'results': results,
        'query': query
    })
