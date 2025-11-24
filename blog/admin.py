from django.contrib import admin
from .models import Post, Tag, About

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')
    readonly_fields = ('html_preview', 'updated_at')
    
    def html_preview(self, obj):
        from django.utils.html import mark_safe
        return mark_safe(obj.body_html) if obj.body_html else ""
    
    html_preview.short_description = "HTML Preview (Saved)"

    class Media:
        js = (
            'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
            'blog/js/admin_markdown.js',
        )
        css = {
            'all': (
                'blog/css/admin_markdown.css',
                'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css',
            )
        }

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at', 'cover_image')
    list_filter = ('status', 'created_at', 'tags')
    search_fields = ('title', 'summary', 'body_markdown', 'tags__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('html_preview', 'created_at', 'updated_at')
    filter_horizontal = ('tags',)
    
    def html_preview(self, obj):
        from django.utils.html import mark_safe
        return mark_safe(obj.body_html) if obj.body_html else ""
    
    html_preview.short_description = "HTML Preview (Saved)"

    class Media:
        js = (
            'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
            'blog/js/admin_markdown.js',
        )
        css = {
            'all': (
                'blog/css/admin_markdown.css',
                'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css',
            )
        }
