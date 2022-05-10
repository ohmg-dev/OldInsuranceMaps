import logging

from loc_insurancemaps.api import CollectionConnection
from loc_insurancemaps.models import Volume
from loc_insurancemaps.utils import LOCParser, filter_volumes_for_use, unsanitize_name

logger = logging.getLogger(__name__)

def import_all_available_volumes(state, apply_filter=True, verbose=False):
    """Preparatory step that runs through all cities in the provided
    state, filters the available volumes for those cities, and then
    imports each one to create a new Volume object."""

    lc = CollectionConnection(delay=0, verbose=verbose)
    cities = lc.get_city_list_by_state(state)

    volumes = []
    for city in cities:
        lc.reset()
        city = unsanitize_name(state, city[0])
        vols = lc.get_volume_list_by_city(city, state)
        if apply_filter is True:
            vols = filter_volumes_for_use(vols)
            volumes += [i for i in vols if i['include'] is True]
        else:
            volumes += vols

    for volume in volumes:
        try:
            Volume.objects.get(pk=volume['identifier'])
        except Volume.DoesNotExist:
            import_volume(volume['identifier'])

def import_volume(identifier):

    try:
        return Volume.objects.get(pk=identifier)
    except Volume.DoesNotExist:
        pass

    lc = CollectionConnection(delay=0, verbose=True)
    response = lc.get_item(identifier)
    if response.get("status") == 404:
        return None

    parsed = LOCParser(item=response['item'], include_regions=True)
    volume_kwargs = parsed.volume_kwargs()

    # add resources to args, not in item (they exist adjacent)
    volume_kwargs["lc_resources"] = response['resources']

    volume = Volume.objects.create(**volume_kwargs)
    volume.regions.set(parsed.regions)

    return volume
