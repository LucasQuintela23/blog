import nh3
import markdown
import re
import requests
import logging
from django.db import models
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex


logger = logging.getLogger(__name__)


def _normalize_unclosed_code_fences(markdown_text: str) -> str:
    """Auto-close unbalanced fenced code blocks to keep preview and publish consistent."""
    if not markdown_text:
        return markdown_text

    fence_count = markdown_text.count("```")
    if fence_count % 2 != 0:
        return f"{markdown_text.rstrip()}\n```"
    return markdown_text


def _looks_like_html(content: str) -> bool:
    return bool(content and re.search(r"<\s*[a-zA-Z][^>]*>", content))


def _normalize_mermaid_blocks(markdown_text: str) -> str:
    """Wrap plain Mermaid text into fenced mermaid blocks when needed."""
    if not markdown_text or "```mermaid" in markdown_text:
        return markdown_text

    lines = markdown_text.splitlines()
    out = []
    i = 0

    while i < len(lines):
        current = lines[i].strip()
        starts_mermaid = current.startswith("graph ") or current.startswith("flowchart ")
        if not starts_mermaid:
            out.append(lines[i])
            i += 1
            continue

        block = [lines[i]]
        i += 1
        while i < len(lines) and lines[i].strip():
            block.append(lines[i])
            i += 1

        out.append("```mermaid")
        out.extend(block)
        out.append("```")

        if i < len(lines):
            out.append(lines[i])
            i += 1

    return "\n".join(out)


def _sanitize_html(html_content: str) -> str:
    allowed_tags = {
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i',
        'li', 'ol', 'p', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'img', 'br', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span',
        'video', 'source', 'iframe', 'figure', 'figcaption'
    }
    allowed_attributes = {
        'a': {'href', 'title', 'target'},
        'img': {'src', 'alt', 'title', 'width', 'height'},
        'source': {'src', 'type'},
        'video': {'controls', 'width', 'height', 'autoplay', 'loop', 'muted', 'poster'},
        'iframe': {'src', 'title', 'width', 'height', 'allow', 'allowfullscreen', 'frameborder'},
        '*': {'class', 'id', 'style'},
    }

    return nh3.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        link_rel="noopener noreferrer"
    )


def _translate_with_libretranslate(text: str, target_language: str) -> str:
    """Translate text using LibreTranslate and return original text on failures."""
    if not text or not text.strip():
        return text

    if not getattr(settings, 'LIBRETRANSLATE_ENABLED', False):
        return text

    endpoint = getattr(settings, 'LIBRETRANSLATE_URL', '').strip()
    if not endpoint:
        return text

    payload = {
        'q': text,
        'source': getattr(settings, 'LIBRETRANSLATE_SOURCE_LANGUAGE', 'pt'),
        'target': target_language,
        'format': 'text',
    }
    api_key = getattr(settings, 'LIBRETRANSLATE_API_KEY', '').strip()
    if api_key:
        payload['api_key'] = api_key

    timeout = int(getattr(settings, 'LIBRETRANSLATE_TIMEOUT', 15))

    try:
        response = requests.post(endpoint, data=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        translated = data.get('translatedText')
        return translated if translated else text
    except Exception as exc:
        logger.warning("LibreTranslate falhou para target=%s: %s", target_language, exc)
        return text


def _translate_markdown_preserving_code(markdown_text: str, target_language: str) -> str:
    """Translate markdown text while preserving fenced and inline code spans."""
    if not markdown_text or not markdown_text.strip():
        return markdown_text

    # Ensure unclosed fences are balanced before masking code blocks.
    normalized_markdown = _normalize_unclosed_code_fences(markdown_text)

    placeholders: dict[str, str] = {}

    def replace_fenced(match: re.Match[str]) -> str:
        token = f"ZXQFENCEDBLOCK{len(placeholders)}QXZ"
        placeholders[token] = match.group(0)
        return token

    def replace_inline(match: re.Match[str]) -> str:
        token = f"ZXQINLINECODE{len(placeholders)}QXZ"
        placeholders[token] = match.group(0)
        return token

    masked = re.sub(r"```[\s\S]*?(?:```|$)", replace_fenced, normalized_markdown)
    masked = re.sub(r"`[^`\n]+`", replace_inline, masked)

    translated = _translate_with_libretranslate(masked, target_language)

    for token, original in placeholders.items():
        translated = translated.replace(token, original)

    return translated


def _needs_translation(source_text: str, translated_text: str) -> bool:
    source = (source_text or '').strip()
    translated = (translated_text or '').strip()
    if not source:
        return False
    return (not translated) or (translated == source)


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
    title_en = models.CharField(max_length=255, blank=True, default='', verbose_name=_("Título (Inglês)"))
    title_es = models.CharField(max_length=255, blank=True, default='', verbose_name=_("Título (Espanhol)"))
    slug = models.SlugField(unique=True, db_index=True, verbose_name=_("Slug"))
    summary = models.TextField(verbose_name=_("Resumo"))
    summary_en = models.TextField(blank=True, default='', verbose_name=_("Resumo (Inglês)"))
    summary_es = models.TextField(blank=True, default='', verbose_name=_("Resumo (Espanhol)"))
    body_markdown = models.TextField(verbose_name=_("Conteúdo Markdown"))
    body_markdown_en = models.TextField(blank=True, default='', verbose_name=_("Conteúdo Markdown (Inglês)"))
    body_markdown_es = models.TextField(blank=True, default='', verbose_name=_("Conteúdo Markdown (Espanhol)"))
    body_html = models.TextField(editable=False, verbose_name=_("Conteúdo HTML"))
    body_html_en = models.TextField(editable=False, blank=True, default='', verbose_name=_("Conteúdo HTML (Inglês)"))
    body_html_es = models.TextField(editable=False, blank=True, default='', verbose_name=_("Conteúdo HTML (Espanhol)"))
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

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        def render_markdown(markdown_source: str) -> str:
            if _looks_like_html(markdown_source):
                return markdown_source
            normalized_markdown = _normalize_mermaid_blocks(
                _normalize_unclosed_code_fences(markdown_source)
            )
            return markdown.markdown(
                normalized_markdown,
                extensions=['extra', 'codehilite', 'toc']
            )

        source_markdown = self.body_markdown or ""
        self.body_markdown = source_markdown

        # Auto-translate empty fields and stale fields that still mirror PT content.
        if _needs_translation(self.title, self.title_en):
            translated = _translate_with_libretranslate(self.title or '', 'en')
            if translated and translated.strip() and translated.strip() != (self.title or '').strip():
                self.title_en = translated
        if _needs_translation(self.summary, self.summary_en):
            translated = _translate_with_libretranslate(self.summary or '', 'en')
            if translated and translated.strip() and translated.strip() != (self.summary or '').strip():
                self.summary_en = translated
        if _needs_translation(source_markdown, self.body_markdown_en):
            translated = _translate_markdown_preserving_code(source_markdown, 'en')
            if translated and translated.strip() and translated.strip() != source_markdown.strip():
                self.body_markdown_en = translated

        if _needs_translation(self.title, self.title_es):
            translated = _translate_with_libretranslate(self.title or '', 'es')
            if translated and translated.strip() and translated.strip() != (self.title or '').strip():
                self.title_es = translated
        if _needs_translation(self.summary, self.summary_es):
            translated = _translate_with_libretranslate(self.summary or '', 'es')
            if translated and translated.strip() and translated.strip() != (self.summary or '').strip():
                self.summary_es = translated
        if _needs_translation(source_markdown, self.body_markdown_es):
            translated = _translate_markdown_preserving_code(source_markdown, 'es')
            if translated and translated.strip() and translated.strip() != source_markdown.strip():
                self.body_markdown_es = translated

        clean_html = _sanitize_html(render_markdown(source_markdown))
        
        self.body_html = clean_html
        self.body_text = strip_tags(clean_html)

        markdown_en = self.body_markdown_en or ""
        self.body_markdown_en = markdown_en
        self.body_html_en = _sanitize_html(render_markdown(markdown_en)) if markdown_en.strip() else ""

        markdown_es = self.body_markdown_es or ""
        self.body_markdown_es = markdown_es
        self.body_html_es = _sanitize_html(render_markdown(markdown_es)) if markdown_es.strip() else ""
        
        super().save(*args, **kwargs)
        
        # Update SearchVector after save (requires PK)
        # This is a simple approach; for high traffic, consider moving to a signal or DB trigger
        if self.pk:
            Post.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('title', 'summary', 'body_markdown')
            )

    def regenerate_auto_translations(self):
        """Force EN/ES translations to be regenerated via LibreTranslate."""
        self.title_en = ''
        self.summary_en = ''
        self.body_markdown_en = ''
        self.body_html_en = ''

        self.title_es = ''
        self.summary_es = ''
        self.body_markdown_es = ''
        self.body_html_es = ''

        self.save()

    def ensure_language_translation(self, language_code: str):
        """Ensure EN/ES translation exists for display; regenerate if still equal to PT."""
        lang = (language_code or 'pt').lower()
        if lang not in {'en', 'es'}:
            return

        source_title = self.title or ''
        source_summary = self.summary or ''
        source_body = self.body_markdown or ''

        changed = False

        if lang == 'en':
            if _needs_translation(source_title, self.title_en):
                translated = _translate_with_libretranslate(source_title, 'en')
                if translated and translated.strip() != source_title.strip():
                    self.title_en = translated
                    changed = True
            if _needs_translation(source_summary, self.summary_en):
                translated = _translate_with_libretranslate(source_summary, 'en')
                if translated and translated.strip() != source_summary.strip():
                    self.summary_en = translated
                    changed = True
            if _needs_translation(source_body, self.body_markdown_en):
                translated = _translate_markdown_preserving_code(source_body, 'en')
                if translated and translated.strip() != source_body.strip():
                    self.body_markdown_en = translated
                    changed = True
        else:
            if _needs_translation(source_title, self.title_es):
                translated = _translate_with_libretranslate(source_title, 'es')
                if translated and translated.strip() != source_title.strip():
                    self.title_es = translated
                    changed = True
            if _needs_translation(source_summary, self.summary_es):
                translated = _translate_with_libretranslate(source_summary, 'es')
                if translated and translated.strip() != source_summary.strip():
                    self.summary_es = translated
                    changed = True
            if _needs_translation(source_body, self.body_markdown_es):
                translated = _translate_markdown_preserving_code(source_body, 'es')
                if translated and translated.strip() != source_body.strip():
                    self.body_markdown_es = translated
                    changed = True

        if changed:
            self.save()

    def __str__(self):
        return self.title

    def get_translated_content(self, language_code: str) -> dict[str, str]:
        """Return post content for selected language with fallback to PT-BR."""
        lang = (language_code or 'pt').lower()

        if lang == 'en':
            return {
                'title': self.title_en or self.title,
                'summary': self.summary_en or self.summary,
                'body_html': self.body_html_en or self.body_html,
            }

        if lang == 'es':
            return {
                'title': self.title_es or self.title,
                'summary': self.summary_es or self.summary,
                'body_html': self.body_html_es or self.body_html,
            }

        return {
            'title': self.title,
            'summary': self.summary,
            'body_html': self.body_html,
        }


class About(models.Model):
    title = models.CharField(max_length=255, default="Sobre Mim", verbose_name=_("Título"))
    title_en = models.CharField(max_length=255, blank=True, default='', verbose_name=_("Título (Inglês)"))
    title_es = models.CharField(max_length=255, blank=True, default='', verbose_name=_("Título (Espanhol)"))
    body_markdown = models.TextField(verbose_name=_("Conteúdo Markdown"))
    body_markdown_en = models.TextField(blank=True, default='', verbose_name=_("Conteúdo Markdown (Inglês)"))
    body_markdown_es = models.TextField(blank=True, default='', verbose_name=_("Conteúdo Markdown (Espanhol)"))
    body_html = models.TextField(editable=False, verbose_name=_("Conteúdo HTML"))
    body_html_en = models.TextField(editable=False, blank=True, default='', verbose_name=_("Conteúdo HTML (Inglês)"))
    body_html_es = models.TextField(editable=False, blank=True, default='', verbose_name=_("Conteúdo HTML (Espanhol)"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))

    class Meta:
        verbose_name = _("Página Sobre")
        verbose_name_plural = _("Página Sobre")

    def save(self, *args, **kwargs):
        def render_markdown(markdown_source: str) -> str:
            if _looks_like_html(markdown_source):
                return markdown_source
            normalized_markdown = _normalize_mermaid_blocks(
                _normalize_unclosed_code_fences(markdown_source)
            )
            return markdown.markdown(
                normalized_markdown,
                extensions=['extra', 'codehilite', 'toc']
            )

        source_markdown = self.body_markdown or ""
        self.body_markdown = source_markdown

        if _needs_translation(self.title, self.title_en):
            translated = _translate_with_libretranslate(self.title or '', 'en')
            if translated and translated.strip() and translated.strip() != (self.title or '').strip():
                self.title_en = translated
        if _needs_translation(self.title, self.title_es):
            translated = _translate_with_libretranslate(self.title or '', 'es')
            if translated and translated.strip() and translated.strip() != (self.title or '').strip():
                self.title_es = translated

        if _needs_translation(source_markdown, self.body_markdown_en):
            translated = _translate_markdown_preserving_code(source_markdown, 'en')
            if translated and translated.strip() and translated.strip() != source_markdown.strip():
                self.body_markdown_en = translated
        if _needs_translation(source_markdown, self.body_markdown_es):
            translated = _translate_markdown_preserving_code(source_markdown, 'es')
            if translated and translated.strip() and translated.strip() != source_markdown.strip():
                self.body_markdown_es = translated

        clean_html = _sanitize_html(render_markdown(source_markdown))
        
        self.body_html = clean_html
        markdown_en = self.body_markdown_en or ""
        self.body_markdown_en = markdown_en
        self.body_html_en = _sanitize_html(render_markdown(markdown_en)) if markdown_en.strip() else ""

        markdown_es = self.body_markdown_es or ""
        self.body_markdown_es = markdown_es
        self.body_html_es = _sanitize_html(render_markdown(markdown_es)) if markdown_es.strip() else ""

        super().save(*args, **kwargs)

    def ensure_language_translation(self, language_code: str):
        lang = (language_code or 'pt').lower()
        if lang not in {'en', 'es'}:
            return

        changed = False
        source_title = self.title or ''
        source_body = self.body_markdown or ''

        if lang == 'en':
            if _needs_translation(source_title, self.title_en):
                translated = _translate_with_libretranslate(source_title, 'en')
                if translated and translated.strip() != source_title.strip():
                    self.title_en = translated
                    changed = True
            if _needs_translation(source_body, self.body_markdown_en):
                translated = _translate_markdown_preserving_code(source_body, 'en')
                if translated and translated.strip() != source_body.strip():
                    self.body_markdown_en = translated
                    changed = True
        else:
            if _needs_translation(source_title, self.title_es):
                translated = _translate_with_libretranslate(source_title, 'es')
                if translated and translated.strip() != source_title.strip():
                    self.title_es = translated
                    changed = True
            if _needs_translation(source_body, self.body_markdown_es):
                translated = _translate_markdown_preserving_code(source_body, 'es')
                if translated and translated.strip() != source_body.strip():
                    self.body_markdown_es = translated
                    changed = True

        if changed:
            self.save()

    def get_translated_content(self, language_code: str) -> dict[str, str]:
        lang = (language_code or 'pt').lower()
        if lang == 'en':
            return {
                'title': self.title_en or self.title,
                'body_html': self.body_html_en or self.body_html,
            }
        if lang == 'es':
            return {
                'title': self.title_es or self.title,
                'body_html': self.body_html_es or self.body_html,
            }
        return {
            'title': self.title,
            'body_html': self.body_html,
        }

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
