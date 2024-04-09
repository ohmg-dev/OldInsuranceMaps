'''
This is a step toward moving database models from the loc_insurancemaps app into
this content app. At present, these are not Django models or even Django proxy models,
just light-weight objects that are instantiated through the Volume and related
models. This will allow the codebase to slowly evolve before actually changing any
database content and running migrations.

The eventual migration plan is this:

ohmg.loc_insurancemaps.models.Volume        --> content.models.Map
ohmg.loc_insurancemaps.models.Sheet         --> content.models.Resource
ohmg.georeference.models.resources.Document --> content.models.VirtualResource
ohmg.georeference.models.resources.Layer    --> content.models.VirtualResource

new model                                   --> content.models.ItemConfigPreset
    This would allow an extraction of Sanborn-specific properties vs. generic item
    uploads. Still unclear exactly what to call this, or everything that it would have.
'''

import logging

from ohmg.loc_insurancemaps.models import Volume

logger = logging.getLogger(__name__)

class Map:

    def __init__(self, volume_pk):

        self.vol = Volume.objects.get(pk=volume_pk)
