from django.conf import settings

def loc_info(request):

    return {
        'newsletter_enabled': settings.ENABLE_NEWSLETTER,
    }
