from .models import Volume

def loc_info(request):

    return {
        "volume_ct": Volume.objects.all().count(),
    }