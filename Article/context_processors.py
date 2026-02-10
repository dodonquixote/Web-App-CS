"""
Context processors for Article app.
"""

def language_context(request):
    """Pass current language to all templates."""
    lang = getattr(request, 'language', 'id')
    
    # Normalize jp to ja
    if lang == 'jp':
        lang = 'ja'
    
    # Create URL prefix
    if lang == 'id':
        prefix = ''
    else:
        prefix = f'/{lang}'
    
    return {
        'current_language': lang,
        'lang_prefix': prefix,
    }
