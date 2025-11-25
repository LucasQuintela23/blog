from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('api/search/', views.search_posts_json, name='search_posts_json'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
]
