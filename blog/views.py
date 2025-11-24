from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.db import models
from django.db.models import Q
from .models import Post, Tag, Comment, About

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.filter(status=Post.Status.PUBLISHED).order_by('-created_at')
        
        # Filter by tag if tag slug is provided
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all tags with their post count
        from django.db.models import Count
        context['all_tags'] = Tag.objects.annotate(
            post_count=Count('posts', filter=models.Q(posts__status=Post.Status.PUBLISHED))
        ).filter(post_count__gt=0).order_by('-post_count')
        
        # Add current tag to context if filtering
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            context['current_tag'] = Tag.objects.filter(slug=tag_slug).first()
        
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        author = request.POST.get('author')
        body = request.POST.get('body')
        if author and body:
            Comment.objects.create(post=self.object, author=author, body=body)
        return self.get(request, *args, **kwargs)


class AboutView(TemplateView):
    template_name = "blog/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about'] = About.objects.first()
        return context
