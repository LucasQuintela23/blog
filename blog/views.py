from typing import Any, cast

from django.contrib.postgres import search as pg_search
from django.db import models
from django.db.models import Q, QuerySet
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView

from blog.context_processors import LanguageCode, get_selected_language

from .models import About, Category, Post


SearchQuery = pg_search.SearchQuery
SearchHeadline = getattr(pg_search, "SearchHeadline", None)


SUPPORTED_POST_LANGUAGES: set[LanguageCode] = {'pt', 'en', 'es'}


def get_post_language(request: HttpRequest) -> LanguageCode:
    return get_selected_language(request)


def translate_ui_term(value: str | None, selected_language: LanguageCode) -> str | None:
    if not value or selected_language == 'pt':
        return value

    normalized_value = value.strip().lower()

    term_map = {
        'qa': {
            'en': 'Quality Assurance',
            'es': 'Aseguramiento de Calidad',
        },
        'geral': {
            'en': 'General',
            'es': 'General',
        },
        'garantia de qualidade': {
            'en': 'Quality Assurance',
            'es': 'Aseguramiento de Calidad',
        },
        'qualidade': {
            'en': 'Quality',
            'es': 'Calidad',
        },
        'engenharia de software': {
            'en': 'Software Engineering',
            'es': 'Ingeniería de Software',
        },
        'tecnologia': {
            'en': 'Technology',
            'es': 'Tecnología',
        },
        'dados': {
            'en': 'Data',
            'es': 'Datos',
        },
    }

    translated = term_map.get(normalized_value, {}).get(selected_language)
    if translated:
        return translated

    return value

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 4

    def _selected_language(self) -> LanguageCode:
        return get_post_language(self.request)
    
    def get_queryset(self) -> QuerySet[Post]:
        queryset: QuerySet[Post] = Post.objects.filter(
            status=Post.Status.PUBLISHED
        ).order_by('-created_at').select_related('category').prefetch_related('tags')
        selected_language = self._selected_language()
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            # Search in Title and Summary (removed body for better relevance)
            if selected_language == 'en':
                language_filters = Q(title_en__icontains=search_query) | Q(summary_en__icontains=search_query)
            elif selected_language == 'es':
                language_filters = Q(title_es__icontains=search_query) | Q(summary_es__icontains=search_query)
            else:
                language_filters = Q(title__icontains=search_query) | Q(summary__icontains=search_query)

            queryset = queryset.filter(language_filters).distinct()
        
        # Filter by category if category slug is provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        return queryset
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        selected_language = self._selected_language()
        # Get all categories with their post count
        from django.db.models import Count
        context['all_categories'] = Category.objects.annotate(
            post_count=Count('posts', filter=models.Q(posts__status=Post.Status.PUBLISHED))
        ).filter(post_count__gt=0).order_by('name')
        
        # Add search query to context
        search_query = self.request.GET.get('q')
        if search_query:
            context['search_query'] = search_query
        
        # Add current category to context if filtering
        category_slug = self.request.GET.get('category')
        if category_slug:
            context['current_category'] = Category.objects.filter(slug=category_slug).first()
        
        context['selected_language'] = selected_language
        for category in context.get('all_categories', []):
            category.display_name = translate_ui_term(category.name, selected_language)
        for post in context.get('posts', []):
            post.ensure_language_translation(selected_language)
            translated = post.get_translated_content(selected_language)
            post.display_title = translated['title']
            post.display_summary = translated['summary']
            if post.category:
                post.category.display_name = translate_ui_term(post.category.name, selected_language)
        
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        selected_language = get_post_language(self.request)
        obj = cast(Post, self.get_object())
        obj.ensure_language_translation(selected_language)
        translated: dict[str, str] = obj.get_translated_content(selected_language)

        context['selected_language'] = selected_language
        context['display_title'] = translated['title']
        context['display_summary'] = translated['summary']
        context['display_body_html'] = translated['body_html']
        context['display_category_name'] = translate_ui_term(
            obj.category.name if obj.category else 'Geral',
            selected_language,
        )
        return context


class AboutView(TemplateView):
    template_name = "blog/about.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        selected_language = get_post_language(self.request)
        about = About.objects.first()
        context['about'] = about
        context['selected_language'] = selected_language

        if about:
            about.ensure_language_translation(selected_language)
            translated = about.get_translated_content(selected_language)
            context['display_about_title'] = translated['title']
            context['display_about_body_html'] = translated['body_html']
        return context

def search_posts_json(request: HttpRequest) -> JsonResponse:
    query = str(request.GET.get('q', ''))
    selected_language = get_post_language(request)
    lang_suffix = f"?lang={selected_language}" if selected_language != 'pt' else ''
    if len(query) < 2:
        return JsonResponse({'results': []})

    results: list[dict[str, str]] = []
    seen_ids: set[int] = set()

    # 1. Title and Summary matches (Simple & Fast)
    if selected_language == 'en':
        simple_filter = Q(title_en__icontains=query) | Q(summary_en__icontains=query)
        match_title_label = 'Title'
        match_summary_label = 'Summary'
        content_label = 'Content'
    elif selected_language == 'es':
        simple_filter = Q(title_es__icontains=query) | Q(summary_es__icontains=query)
        match_title_label = 'Título'
        match_summary_label = 'Resumen'
        content_label = 'Contenido'
    else:
        simple_filter = Q(title__icontains=query) | Q(summary__icontains=query)
        match_title_label = 'Título'
        match_summary_label = 'Resumo'
        content_label = 'Conteúdo'

    simple_matches = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).filter(simple_filter).only(
        'title', 'title_en', 'title_es', 'slug', 'created_at',
        'summary', 'summary_en', 'summary_es'
    )[:5]
    
    for post in simple_matches:
        if post.pk is not None:
            seen_ids.add(int(post.pk))

        translated: dict[str, str] = post.get_translated_content(selected_language)
        title: str = translated['title']
        summary: str = translated['summary']
        
        # Determine match type and snippet
        if query.lower() in title.lower():
            match_type = match_title_label
            snippet = summary[:150] + '...' if summary else ''
        else:
            match_type = match_summary_label
            # Simple highlight for summary
            import re
            text: str = summary
            # Case insensitive replace to add mark tags
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            snippet = pattern.sub(lambda m: f'<mark>{m.group()}</mark>', text)

        results.append({
            'title': title,
            'url': f"{reverse('blog:post_detail', args=[post.slug])}{lang_suffix}",
            'snippet': snippet,
            'date': post.created_at.strftime('%Y - %B'),
            'type': match_type
        })
        
    # 2. Body matches (using SearchHeadline for context)
    try:
        if SearchHeadline is None:
            raise RuntimeError("SearchHeadline indisponivel para este ambiente")

        search_query = SearchQuery(query, config='portuguese')
        body_matches = Post.objects.filter(status=Post.Status.PUBLISHED).exclude(
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
            headline = str(getattr(post, 'headline', ''))
            results.append({
                'title': post.title,
                'url': f"{reverse('blog:post_detail', args=[post.slug])}{lang_suffix}",
                'snippet': headline,
                'date': post.created_at.strftime('%Y - %B'),
                'type': content_label
            })
            
    except Exception:
        # Fallback: Simple contains search on body if Postgres search fails
        fallback_matches = Post.objects.filter(
            status=Post.Status.PUBLISHED,
            body_text__icontains=query
        ).exclude(id__in=seen_ids)[:3]
        
        for post in fallback_matches:
             results.append({
                'title': post.title,
                     'url': f"{reverse('blog:post_detail', args=[post.slug])}{lang_suffix}",
                'snippet': '...conteúdo encontrado...', 
                'date': post.created_at.strftime('%Y - %B'),
                     'type': content_label
            })

    return JsonResponse({'results': results})
