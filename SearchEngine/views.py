from django.shortcuts import render, redirect, render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
# from django.contrib.auth.forms import UserCreationForm
from django.template.loader import render_to_string
from django.http import HttpResponse, StreamingHttpResponse
from django.template import Context, Template, RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
from SearchEngine.lib.utils import FindSearchResult, Paginator
from SearchEngine.lib.custom_exceptions import NoResultException
from .models import SearchQuery, Recommendation, ServerName, SuggestedServers, Path
from .forms import SearchForm, SuggestServer, CaptchaUserCreateForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import login as authlogin
from itertools import islice
from collections import Counter
import json
from datetime import datetime
import requests



def home(request):
    recommendations = Recommendation.objects.all()
    return render(request, 'SearchEngine/base.html',
                  {})

def user_profile(request):
    pass

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def verify_captcha(data, request):
    captcha_rs = data.get('g-recaptcha-response')
    #captcha = form.cleaned_data.get('captcha')
    url = "https://www.google.com/recaptcha/api/siteverify"
    params = {'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': captcha_rs,
                'remoteip': get_client_ip(request)
                }
    verify_rs = requests.get(url, params=params, verify=True)
    verify_rs = verify_rs.json()
    status = verify_rs.get("success", False)
    return status

def login(request):
    if request.method == 'POST':
        data = request.POST
        status = verify_captcha(data, request)
        print(status)
        if status:
            return authlogin(request)
    return render(request,
                  'registration/login.html',
                  {'form': AuthenticationForm()})


def signup_view(request):
    print("view")
    if request.method == 'POST':
        data = request.POST
        form = CaptchaUserCreateForm(data)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            status = verify_captcha(data, request)
            print(status)
            if status:
                user = authenticate(username=username, password=raw_password)
                authlogin(request, user)
                return redirect('/')
    else:
        form = CaptchaUserCreateForm()
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
    global selected_length
    keyword = request.POST.get('keyword')
    exact_only = request.POST.get('exact_only')
    if keyword is not None:
        selected = json.loads(request.POST.get('selected'))
        try:
            search_model = SearchQuery()
            search_model.user = request.user
            search_model.add(word=keyword,
                             servers=list(selected),
                             exact_only={'false':False,
                                         'true':True}.get(exact_only, False))
        except ValueError:
            # user is not authenticated
            pass
        searcher = FindSearchResult(keyword=keyword,
                                    servers=selected,
                                    user=request.user,
                                    exact_only=exact_only)
        try:
            error = False
            # start_time = datetime.now()
            all_result = Paginator(searcher.find_result(),
                                   range_frame=2,
                                   rows_number=30)
            # print("execution time -- > {} ".format(datetime.now() - start_time))
        except ValueError as exc:
            # invalid keywords
            error = """INVALID KEYWORD: Your keyword contains invalid notations!\n
            Exception: {}""".format(exc)
        except NoResultException as exc:
            error = exc

        selected_length = len(selected)
        if error:
            html = render_to_string('SearchEngine/page_format.html',
                                    {'error': error,
                                    'selected_len': selected_length,
                                    'founded_results': 'X',
                                    'user': request.user,
                                    'show_image': False,})
        else:
            html = render_to_string('SearchEngine/page_format.html',
                                    {'all_results': all_result,
                                    'page': all_result[1],
                                    'error': error,
                                    'founded_results': 'X',
                                    'user': request.user,
                                    'selected_len': selected_length,
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
                        'selected_len': selected_length,
                        'show_image': False,
                        'is_other_pages':all_result.has_other_pages()})

@login_required
def recom_redirect(request, keyword):
    servers = ServerName.objects.all()
    selected = {s.name: s.path for s in servers}
    searcher = FindSearchResult(keyword=keyword,
                                servers=selected,
                                user=request.user,
                                exact_only='false')    
    all_result = Paginator(searcher.find_result(),
                            range_frame=2,
                            rows_number=30)

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


def meta_links(request, server_name, path_id):
    path_obj = Path.objects.get(id__exact=path_id)
    server_obj = ServerName.objects.get(name__exact=server_name)
    return render(request, 
                  'SearchEngine/meta_links.html',
                  {'links': path_obj.meta_path,
                   'server_url': server_obj.path,
                   'path': path_obj.path,
                   'server_name': server_name,
                   'user': request.user,})

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

def handler404(request, exception=None):
    response = render(request, '404.html', {},)
    response.status_code = 404
    return response


def handler500(request, exception=None):
    response = render(request, '500.html', {},)
    response.status_code = 500
    return response
  