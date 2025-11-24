import nh3
import markdown
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex

class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', _('Draft')
        PUBLISHED = 'PB', _('Published')

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    slug = models.SlugField(unique=True, db_index=True, verbose_name=_("Slug"))
    summary = models.TextField(verbose_name=_("Summary"))
    body_markdown = models.TextField(verbose_name=_("Markdown Content"))
    body_html = models.TextField(editable=False, verbose_name=_("HTML Content"))
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        indexes = [
            GinIndex(fields=['search_vector']),
        ]

    def save(self, *args, **kwargs):
        # 1. Convert Markdown to HTML
        # Using extra for tables, etc., and codehilite for syntax highlighting
        html_content = markdown.markdown(
            self.body_markdown,
            extensions=['extra', 'codehilite', 'toc']
        )
        
        # 2. Sanitize HTML with nh3 (strict)
        allowed_tags = {
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 
            'li', 'ol', 'p', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'img', 'br', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'
        }
        allowed_attributes = {
            'a': {'href', 'title', 'target', 'rel'},
            'img': {'src', 'alt', 'title', 'width', 'height'},
            '*': {'class', 'id'}, # Allow class for syntax highlighting and IDs for anchors
        }
        
        clean_html = nh3.clean(
            html_content, 
            tags=allowed_tags, 
            attributes=allowed_attributes,
            link_rel="noopener noreferrer"
        )
        
        self.body_html = clean_html
        
        super().save(*args, **kwargs)
        
        # Update SearchVector after save (requires PK)
        # This is a simple approach; for high traffic, consider moving to a signal or DB trigger
        if self.pk:
            Post.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('title', 'summary', 'body_markdown')
            )

    def __str__(self):
        return self.title
