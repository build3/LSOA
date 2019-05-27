def update_draft_media(draft_observation, image, video):
    """Updates media for draft observation.
    
    Args:
        draft_observation(`Observation`): Draft observation to update.
        image(str or File or None): `original_image` from request. It can file or path in string.
        video(str or File or None): `video` from request. It can file or path in string.
    """
    # This is needed to update video or original_image when one of them is already set
    # and user want to change to the opposite.
    if draft_observation:
        if draft_observation.video and image:
            draft_observation.video = None
            draft_observation.save()

        if draft_observation.original_image and video:
            draft_observation.original_image = None
            draft_observation.save()


def reset_media(draft_observation, image, video):
    """Reset `video` and `original_image` for `Observation`.

    Args:
        draft_observation(`Observation`): Draft observation to update.
        image(str or File or None): `original_image` from request. It can file or path in string.
        video(str or File or None): `video` from request. It can file or path in string.
    """
    if not image and not video:
        draft_observation.video = None
        draft_observation.original_image = None
        draft_observation.save()


def remove_key_from_session(request, key):
    """
    Removes key from session and returns it value. If key does not exist None is returned.
    
    Args:
        request(HttpRequest) - Request object containing session.
        key(str): One of session keys
    """
    if key in request.session:
        value = request.session[key]
    
        del request.session[key]
        request.session.modified = True

        return value
    else:
        return None
