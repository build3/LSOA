def has_current_observation(request):
    return {
        'has_current_observation': request.session.get('course') or request.session.get(
            'grouping') or request.session.get('context_tags')
    }
