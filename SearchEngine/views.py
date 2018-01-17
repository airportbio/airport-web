from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.template.loader import render_to_string
from django.http import HttpResponse, StreamingHttpResponse
from django.template import Context, Template
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from SearchEngine.lib.utils import FindSearchResult, Paginator
from .models import SearchQuery, Recommendation, ServerName, SuggestedServers
from .forms import SearchForm, SuggestServer
from itertools import islice
from collections import Counter
import json
from datetime import datetime


def home(request):
    recommendations = Recommendation.objects.all()
    return render(request, 'SearchEngine/base.html',
                  {})

def user_profile(request):
    pass


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})



def generate_template(all_result, error, user):
    t = Template(open('SearchEngine/templates/SearchEngine/page_format.html').read())
    
    while True:
        if not all_result.has_next():
            print("break")
            break
        c = Context(
        {'all_results': all_result,
        'error': error,
        'founded_results': 'X',
        'user': user,
        'selected_len': True,
        'show_image': False,})
        yield t.render(c)

@csrf_exempt
def search_result(request, page=1):
    global all_result
    keyword = request.POST.get('keyword')
    if keyword is not None:
        selected = json.loads(request.POST.get('selected'))
        try:
            search_model = SearchQuery()
            search_model.user = request.user
            search_model.add(word=keyword, servers=list(selected))
        except ValueError:
            # user is not authenticated
            pass
        searcher = FindSearchResult(keyword=keyword, servers=selected, user=request.user)
        try:
            error = False
            # start_time = datetime.now()
            all_result = Paginator(searcher.find_result(),
                                   range_frame=2,
                                   rows_number=20)
            # print("execution time -- > {} ".format(datetime.now() - start_time))
        except ValueError as exc:
            # invalid keywords
            error = """INVALID KEYWORD:
            Your keyword contains invalid notations!
            {}""".format(exc)

        html = render_to_string('SearchEngine/page_format.html',
                                {'all_results': all_result,
                                 'page': all_result[1],
                                 'error': error,
                                 'founded_results': 'X',
                                 'user': request.user,
                                 'selected_len': True,
                                 'show_image': False,
                                 'is_other_pages':all_result.has_other_pages()})

        return HttpResponse(json.dumps({'html': html}),
                            content_type="application/json")
    else:
        page = int(request.GET.get('page', 1))
        return render(request, 
                      'SearchEngine/page_format.html',
                       {'all_results': all_result,
                        'page': all_result[page],
                        'error': False,
                        'founded_results': 'X',
                        'user': request.user,
                        'selected_len': True,
                        'show_image': False,
                        'is_other_pages':all_result.has_other_pages()})

@login_required
def recom_redirect(request, keyword):
    servers = ServerName.objects.all()
    selected = {s.name: s.path for s in servers}
    searcher = FindSearchResult(keyword=keyword, servers=selected, user=request.user)
    all_result = Paginator(searcher.find_result(),
                                   range_frame=2,
                                   rows_number=20)
    return render(request, 
                  'SearchEngine/page_format.html',
                  {'all_results': all_result,
                   'page': all_result[1],
                   'error': False,
                   'founded_results': 'X',
                   'user': request.user,
                   'selected_len': True,
                   'show_image': False,
                   'is_other_pages':all_result.has_other_pages()})
@csrf_exempt
def search(request):
    search_form = SearchForm()
    servers = ServerName.objects.all()

    try:
        queryset = Recommendation.objects.filter(user=request.user)
        recom_model = queryset[0]
    except (IndexError, TypeError):
        recomwords = []
    else:
        recomwords = Counter(recom_model.recommendations).most_common(7)
    return render(request, 'SearchEngine/search.html',
                  {'search_form': search_form,
                   'servers': servers,
                   'user': request.user,
                   'recommended_words': recomwords,
                   'show_image':True})

@csrf_exempt
@login_required
def suggest_server(request):
    if request.GET.get('name'):
        form = SuggestServer(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            url = form.cleaned_data['url']
            metadata_link = form.cleaned_data['metadata_link']
            info = form.cleaned_data['extra_information']
            model = SuggestedServers()

            model.name = name
            model.url = url
            model.metadata_link = metadata_link
            model.extra_information = info

            model.save()

            return render(request, 'SearchEngine/thanks.html',
                          {'user': request.user})

    if request.method == 'GET':
        suggestform = SuggestServer()
        return render(request, 'SearchEngine/suggest_server.html',
                    {'form': suggestform,
                    'user': request.user
                    })

#def submit_suggestion(request):
