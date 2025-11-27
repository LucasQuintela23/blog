from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.db import models
from django.db.models import Q
from .models import Post, Tag, Category, Comment, About
from django.http import JsonResponse
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline
from django.urls import reverse

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 4
    
    def get_queryset(self):
        queryset = Post.objects.filter(status=Post.Status.PUBLISHED).order_by('-created_at').select_related('category').prefetch_related('tags')
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            # Search in Title, Summary and Tags (removed body for better relevance)
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(summary__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
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
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
            
        self.object = self.get_object()
        body = request.POST.get('body')
        
        if body:
            author = request.user.get_full_name() or request.user.username
            Comment.objects.create(post=self.object, author=author, body=body)
            
        return self.get(request, *args, **kwargs)


class AboutView(TemplateView):
    template_name = "blog/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about'] = About.objects.first()
        return context

def search_posts_json(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    results = []
    seen_ids = set()

    # 1. Title and Summary matches (Simple & Fast)
    simple_matches = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).filter(
        Q(title__icontains=query) | Q(summary__icontains=query)
    ).only('title', 'slug', 'created_at', 'summary')[:5]
    
    for post in simple_matches:
        seen_ids.add(post.id)
        
        # Determine match type and snippet
        if query.lower() in post.title.lower():
            match_type = 'Título'
            snippet = post.summary[:150] + '...' if post.summary else ''
        else:
            match_type = 'Resumo'
            # Simple highlight for summary
            import re
            text = post.summary
            # Case insensitive replace to add mark tags
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            snippet = pattern.sub(lambda m: f'<mark>{m.group()}</mark>', text)

        results.append({
            'title': post.title,
            'url': reverse('blog:post_detail', args=[post.slug]),
            'snippet': snippet,
            'date': post.created_at.strftime('%Y - %B'),
            'type': match_type
        })
        
    # 2. Body matches (using SearchHeadline for context)
    try:
        search_query = SearchQuery(query, config='portuguese')
        body_matches = Post.objects.filter(
            status=Post.Status.PUBLISHED
        ).exclude(
            id__in=seen_ids
        ).annotate(
            headline=SearchHeadline(
                'body_text',
                search_query,
                start_sel='<mark>',
                stop_sel='</mark>',
                config='portuguese'
            )
        ).filter(headline__icontains=query)[:5]
        
        for post in body_matches:
            results.append({
                'title': post.title,
                'url': reverse('blog:post_detail', args=[post.slug]),
                'snippet': post.headline, 
                'date': post.created_at.strftime('%Y - %B'),
                'type': 'Conteúdo'
            })
            
    except Exception as e:
        print(f"Search error: {e}")
        # Fallback: Simple contains search on body if Postgres search fails
        fallback_matches = Post.objects.filter(
            status=Post.Status.PUBLISHED,
            body_text__icontains=query
        ).exclude(id__in=seen_ids)[:3]
        
        for post in fallback_matches:
             results.append({
                'title': post.title,
                'url': reverse('blog:post_detail', args=[post.slug]),
                'snippet': '...conteúdo encontrado...', 
                'date': post.created_at.strftime('%Y - %B'),
                'type': 'Conteúdo'
            })

    return JsonResponse({'results': results})
