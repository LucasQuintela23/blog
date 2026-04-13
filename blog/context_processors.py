from typing import Dict


SUPPORTED_POST_LANGUAGES = {"pt", "en", "es"}


UI_LABELS: Dict[str, Dict[str, str]] = {
    "pt": {
        "nav_articles": "Artigos",
        "nav_about": "Sobre",
        "nav_contact": "Contato",
        "search_placeholder": "Buscar...",
        "latest_posts": "Últimas Publicações",
        "categories": "Categorias",
        "tags": "Palavras-Chave",
        "read_article": "Ler artigo",
        "no_posts": "Nenhum post encontrado.",
        "search_no_results": "Nenhuma informação encontrada",
        "back_to_list": "Voltar à lista",
        "about_last_update": "Última atualização",
    },
    "en": {
        "nav_articles": "Articles",
        "nav_about": "About",
        "nav_contact": "Contact",
        "search_placeholder": "Search...",
        "latest_posts": "Latest Posts",
        "categories": "Categories",
        "tags": "Keywords",
        "read_article": "Read article",
        "no_posts": "No posts found.",
        "search_no_results": "No information found",
        "back_to_list": "Back to list",
        "about_last_update": "Last update",
    },
    "es": {
        "nav_articles": "Artículos",
        "nav_about": "Sobre",
        "nav_contact": "Contacto",
        "search_placeholder": "Buscar...",
        "latest_posts": "Últimas Publicaciones",
        "categories": "Categorías",
        "tags": "Palabras clave",
        "read_article": "Leer artículo",
        "no_posts": "No se encontraron publicaciones.",
        "search_no_results": "No se encontró información",
        "back_to_list": "Volver a la lista",
        "about_last_update": "Última actualización",
    },
}


def get_selected_language(request):
    lang = (request.GET.get("lang") or "pt").lower()
    return lang if lang in SUPPORTED_POST_LANGUAGES else "pt"


def ui_labels(request):
    lang = get_selected_language(request)
    return {
        "selected_language": lang,
        "ui_labels": UI_LABELS[lang],
    }
