from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Post

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by published status unless user is staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(status=Post.Status.PUBLISHED)
        return queryset

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status=Post.Status.PUBLISHED)
        return queryset
