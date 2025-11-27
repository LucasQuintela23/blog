from django import template
from django.utils.safestring import mark_safe
import re
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount import providers

register = template.Library()

@register.filter(name='highlight')
def highlight(text, search_query):
    """
    Highlights search terms in text with yellow background.
    """
    if not search_query or not text:
        return text
    
    # Split search query into individual words
    search_terms = search_query.strip().split()
    
    # Create a pattern that matches any of the search terms (case-insensitive)
    # Use word boundaries to match whole words or partial matches
    pattern = '|'.join([re.escape(term) for term in search_terms])
    
    if not pattern:
        return text
    
    # Replace matches with highlighted version
    # Using a lambda to preserve the original case
    def replace_match(match):
        return f'<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 2px;">{match.group(0)}</mark>'
    
    highlighted = re.sub(
        f'({pattern})',
        replace_match,
        str(text),
        flags=re.IGNORECASE
    )
    
    return mark_safe(highlighted)

@register.simple_tag
def is_provider_configured(provider_id):
    """
    Checks if a SocialApp is configured for the given provider_id.
    """
    try:
        return SocialApp.objects.filter(provider=provider_id).exists()
    except Exception:
        return False
