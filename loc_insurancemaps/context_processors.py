from georeference.utils import full_reverse

def loc_info(request):

    try:
        user = request.user
    except AttributeError:
        user = None
    if user and user.is_authenticated:
        user_info = {
            'is_authenticated': True,
            'name': user.username,
            # 'profile': full_reverse("profile_detail", args=(user.username, )),
        }
    else:
        user_info = {
            'is_authenticated': False
        }
    return {
        'navbar_params': {
            'USER': user_info
        }
    }
