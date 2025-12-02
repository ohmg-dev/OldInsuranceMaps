from ohmg.core.models import Map

from .models import Place


def reset_volume_counts(verbose=False):
    if verbose:
        print("set all Place volume counts to 0")
    Place.objects.all().update(volume_count=0, volume_count_inclusive=0)
    if verbose:
        print("done")

    for map in Map.objects.all():
        if verbose:
            print(map)
        map.update_place_counts()
