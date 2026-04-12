from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Post, Tag, Category, About


class SplitMarkdownWidget(forms.Textarea):
    class Media:
        js = ('admin/js/markdown-preview.js',)
        css = {'all': ('admin/css/markdown-preview.css',)}

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        current_class = attrs.get('class', '')
        attrs['class'] = f"{current_class} markdown-editor-input".strip()
        attrs.setdefault('rows', '28')
        attrs['data-markdown-editor'] = 'true'

        textarea = super().render(name, value, attrs, renderer)
        preview_id = f"id_{name}_preview"

        return format_html(
            """
            <div class="markdown-split-editor" data-markdown-split-root="true" data-preview-id="{}">
                <div class="markdown-split-editor__toolbar" data-markdown-toolbar="true"></div>
                <div class="markdown-split-editor__panes">
                    <div class="markdown-split-editor__pane markdown-split-editor__pane--input">
                        <div class="markdown-split-editor__title">Conteudo Markdown</div>
                        {}
                    </div>
                    <div class="markdown-split-editor__pane markdown-split-editor__pane--preview">
                        <div class="markdown-split-editor__title">Previsualizacao em tempo real</div>
                        <div id="{}" class="markdown-live-preview"></div>
                    </div>
                </div>
                <div class="markdown-split-editor__status">
                    <span class="markdown-status__item">Palavras: <strong data-markdown-word-count="true">0</strong></span>
                    <span class="markdown-status__item">Linhas: <strong data-markdown-line-count="true">0</strong></span>
                </div>
            </div>
            """,
            preview_id,
            mark_safe(textarea),
            preview_id,
        )


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'body_markdown': SplitMarkdownWidget(attrs={
                'class': 'vLargeTextField',
                'rows': '28',
                'style': 'font-family: "Courier New", monospace; font-size: 12px;'
            })
        }


class AboutAdminForm(forms.ModelForm):
    class Meta:
        model = About
        fields = '__all__'
        widgets = {
            'body_markdown': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': '20',
                'style': 'font-family: "Courier New", monospace; font-size: 12px;'
            })
        }

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    form = AboutAdminForm
    list_display = ('title', 'updated_at')
    readonly_fields = ('html_preview', 'updated_at')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title',)
        }),
        ('Conteúdo (Markdown)', {
            'fields': ('body_markdown',),
            'description': '<strong>Dicas:</strong> Use **negrito**, *itálico*, `código`, ```bloco de código```, # Títulos, - Listas, ou diagramas: <code>```mermaid<br/>graph TD<br/>A --> B<br/>```</code>'
        }),
        ('Previsualização', {
            'fields': ('html_preview',),
            'classes': ('wide',)
        }),
    )
    
    def html_preview(self, obj):
        from django.utils.html import mark_safe
        return mark_safe(obj.body_html) if obj.body_html else ""
    
    html_preview.short_description = "Pré-visualização HTML (Salvo)"

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title', 'author', 'category', 'status', 'created_at', 'cover_image')
    list_editable = ('status',)
    list_filter = ('status', 'created_at', 'category', 'tags')
    search_fields = ('title', 'summary', 'body_markdown', 'tags__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)
    actions = ('publish_selected', 'unpublish_selected')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'summary', 'author', 'category', 'tags', 'status')
        }),
        ('Conteúdo', {
            'fields': ('body_markdown',),
            'description': 'Use os botoes para inserir markdown e acompanhe a previsualizacao em tempo real no mesmo painel.'
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.action(description='Publicar postagens selecionadas')
    def publish_selected(self, request, queryset):
        updated = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(request, f"{updated} postagem(ns) publicada(s) com sucesso.")

    @admin.action(description='Mover selecionadas para rascunho')
    def unpublish_selected(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f"{updated} postagem(ns) movida(s) para rascunho.")
