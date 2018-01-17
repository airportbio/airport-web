from django.conf.urls import url
from . import views

app_name = 'searchengine'
urlpatterns = [
    url(r'^$', views.search, name='search'),
    url(r'^search_result/.*$', views.search_result, name='search_result'),
    url(r'^signup/', views.signup_view, name='signup'),
]
