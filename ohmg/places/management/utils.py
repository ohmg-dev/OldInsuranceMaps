from ohmg.loc_insurancemaps.models import Volume
from ohmg.places.models import Place

def reset_volume_counts(verbose=False):

    if verbose:
        print("set all Place volume counts to 0")
    Place.objects.all().update(volume_count=0, volume_count_inclusive=0)
    if verbose:
        print("done")

    for volume in Volume.objects.all():
        if verbose:
            print(volume)
        volume.update_place_counts()
