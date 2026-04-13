from typing import Literal, TypedDict

from django.http import HttpRequest


LanguageCode = Literal["pt", "en", "es"]


class LabelsDict(TypedDict):
    nav_articles: str
    nav_about: str
    nav_contact: str
    search_placeholder: str
    latest_posts: str
    categories: str
    tags: str
    read_article: str
    no_posts: str
    search_no_results: str
    back_to_list: str
    about_last_update: str
    on_this_page: str
    footer_rights: str


class UiLabelsContext(TypedDict):
    selected_language: LanguageCode
    ui_labels: LabelsDict


SUPPORTED_POST_LANGUAGES: set[LanguageCode] = {"pt", "en", "es"}


UI_LABELS: dict[LanguageCode, LabelsDict] = {
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
        "on_this_page": "Nesta página",
        "footer_rights": "Todos os direitos reservados.",
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
        "on_this_page": "On this page",
        "footer_rights": "All rights reserved.",
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
        "on_this_page": "En esta página",
        "footer_rights": "Todos los derechos reservados.",
    },
}


def get_selected_language(request: HttpRequest) -> LanguageCode:
    lang = (request.GET.get("lang") or "pt").lower()
    if lang in SUPPORTED_POST_LANGUAGES:
        return lang
    return "pt"


def ui_labels(request: HttpRequest) -> UiLabelsContext:
    lang = get_selected_language(request)
    return {
        "selected_language": lang,
        "ui_labels": UI_LABELS[lang],
    }
