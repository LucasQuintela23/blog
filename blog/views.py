from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.db import models
from django.db.models import Q
from .models import Post, Tag, Category, Comment, About

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.filter(status=Post.Status.PUBLISHED).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            # Use Q objects for simple substring matching as requested
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(summary__icontains=search_query) |
                Q(body_markdown__icontains=search_query)
            )
        
        # Filter by category if category slug is provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by tag if tag slug is provided
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all categories with their post count
        from django.db.models import Count
        context['all_categories'] = Category.objects.annotate(
            post_count=Count('posts', filter=models.Q(posts__status=Post.Status.PUBLISHED))
        ).filter(post_count__gt=0).order_by('name')
        
        # Get all tags with their post count
        context['all_tags'] = Tag.objects.annotate(
            post_count=Count('posts', filter=models.Q(posts__status=Post.Status.PUBLISHED))
        ).filter(post_count__gt=0).order_by('-post_count')
        
        # Add search query to context
        search_query = self.request.GET.get('q')
        if search_query:
            context['search_query'] = search_query
        
        # Add current category to context if filtering
        category_slug = self.request.GET.get('category')
        if category_slug:
            context['current_category'] = Category.objects.filter(slug=category_slug).first()
        
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
