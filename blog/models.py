import nh3
import markdown
from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Nome"))
    slug = models.SlugField(unique=True, db_index=True, verbose_name=_("Slug"))

    class Meta:
        verbose_name = _("Categoria")
        verbose_name_plural = _("Categorias")

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Nome"))
    slug = models.SlugField(unique=True, db_index=True, verbose_name=_("Slug"))

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', _('Rascunho')
        PUBLISHED = 'PB', _('Publicado')

    title = models.CharField(max_length=255, verbose_name=_("Título"))
    slug = models.SlugField(unique=True, db_index=True, verbose_name=_("Slug"))
    summary = models.TextField(verbose_name=_("Resumo"))
    body_markdown = models.TextField(verbose_name=_("Conteúdo Markdown"))
    body_html = models.TextField(editable=False, verbose_name=_("Conteúdo HTML"))
    body_text = models.TextField(editable=False, verbose_name=_("Conteúdo Texto"), blank=True)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status")
    )
    author = models.CharField(max_length=100, default="Admin", verbose_name=_("Autor"))
    read_time = models.IntegerField(default=5, verbose_name=_("Tempo de Leitura (minutos)"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts', verbose_name=_("Categoria"))
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True, verbose_name=_("Tags"))
    cover_image = models.ImageField(upload_to='posts/covers/', blank=True, null=True, verbose_name=_("Imagem de Capa"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))
    
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        verbose_name = _("Postagem")
        verbose_name_plural = _("Postagens")
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
            'a': {'href', 'title', 'target'},
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
        self.body_text = strip_tags(clean_html)
        
        super().save(*args, **kwargs)
        
        # Update SearchVector after save (requires PK)
        # This is a simple approach; for high traffic, consider moving to a signal or DB trigger
        if self.pk:
            Post.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('title', 'summary', 'body_markdown')
            )

    def __str__(self):
        return self.title


class About(models.Model):
    title = models.CharField(max_length=255, default="Sobre Mim", verbose_name=_("Título"))
    body_markdown = models.TextField(verbose_name=_("Conteúdo Markdown"))
    body_html = models.TextField(editable=False, verbose_name=_("Conteúdo HTML"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))

    class Meta:
        verbose_name = _("Página Sobre")
        verbose_name_plural = _("Página Sobre")

    def save(self, *args, **kwargs):
        # 1. Convert Markdown to HTML
        html_content = markdown.markdown(
            self.body_markdown,
            extensions=['extra', 'codehilite', 'toc']
        )
        
        # 2. Sanitize HTML
        allowed_tags = {
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 
            'li', 'ol', 'p', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'img', 'br', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'
        }
        allowed_attributes = {
            'a': {'href', 'title', 'target'},
            'img': {'src', 'alt', 'title', 'width', 'height'},
            '*': {'class', 'id'},
        }
        
        clean_html = nh3.clean(
            html_content, 
            tags=allowed_tags, 
            attributes=allowed_attributes,
            link_rel="noopener noreferrer"
        )
        
        self.body_html = clean_html
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.CharField(max_length=100, verbose_name=_('Autor'))
    body = models.TextField(verbose_name=_('Comentário'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Criado em'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Comentário')
        verbose_name_plural = _('Comentários')

    def __str__(self):
        return f"Comentário de {self.author} em {self.post.title}"
