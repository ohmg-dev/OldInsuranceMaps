import logging
from PIL import Image, ImageDraw, ImageFilter

from guardian.shortcuts import get_perms, get_objects_for_user

from django.shortcuts import render
from django.views import View
from django.db.models import F
from django.conf import settings
from django.urls import reverse
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.utils.translation import ugettext as _
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied, ObjectDoesNotExist
from django.core import serializers

from geonode.base.utils import ManageResourceOwnerPermissions
from geonode.base.models import Region
from geonode.utils import resolve_object, build_social_links
from geonode.security.views import _perms_info_json
from geonode.documents.models import Document
from geonode.documents.views import _resolve_document
from geonode.documents.enumerations import DOCUMENT_TYPE_MAP
from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.monitoring import register_event
from geonode.monitoring.models import EventType

from .models import Volume, Sheet
from .utils import parsers
from .utils.importer import Importer
from .api import APIConnection

logger = logging.getLogger("geonode.lc_insurancemaps.views")

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this document.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")

def _resolve_item(request, docdoi, loc_type=None, **kwargs):

    item = None
    try:
        item = resolve_object(
                request,
                Document,
                {'doi': docdoi},
                permission='base.view_resourcebase',
                permission_msg=_PERMISSION_MSG_VIEW,
                **kwargs
            )
    except Http404:
        return HttpResponse(
            loader.render_to_string(
                '404.html', context={
                }, request=request), status=404)

    except PermissionDenied:
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _("You are not allowed to view this document.")}, request=request), status=403)

    if item is None:
        return HttpResponse(
            'An unknown error has occured.',
            content_type="text/plain",
            status=401
        )

    else:
        return item

def item_detail(request, docdoi, loc_type=None):
    """
    The view that presents the image chopping interface.
    """

    document = _resolve_item(request, docdoi, loc_type=loc_type)

    permission_manager = ManageResourceOwnerPermissions(document)
    permission_manager.set_owner_permissions_according_to_workflow()

    # Add metadata_author or poc if missing
    document.add_missing_metadata_author_or_poc()

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != document.owner and not request.user.is_superuser:
        Document.objects.filter(
            id=document.id).update(
            popular_count=F('popular_count') + 1)

    metadata = document.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(document)

    perms_list = get_perms(
        request.user,
        document.get_self_resource()) + get_perms(request.user, document)

    group = None
    if document.group:
        try:
            group = GroupProfile.objects.get(slug=document.group.name)
        except ObjectDoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    IMGTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'image']

    context_dict = {
        'access_token': access_token,
        'resource': document,
        'perms_list': perms_list,
        'permissions_json': permissions_json,
        'group': group,
        'metadata': metadata,
        'imgtypes': IMGTYPES,
    }

    # if settings.SOCIAL_ORIGINS:
    #     context_dict["social_links"] = build_social_links(
    #         request, document)

    # if getattr(settings, 'EXIF_ENABLED', False):
    #     try:
    #         from geonode.documents.exif.utils import exif_extract_dict
    #         exif = exif_extract_dict(document)
    #         if exif:
    #             context_dict['exif_data'] = exif
    #     except Exception:
    #         logger.error("Exif extraction failed.")
    #
    # if request.user.is_authenticated:
    #     if getattr(settings, 'FAVORITE_ENABLED', False):
    #         from geonode.favorite.utils import get_favorite_info
    #         context_dict["favorite_info"] = get_favorite_info(request.user, document)

    register_event(request, EventType.EVENT_VIEW, document)

    template = "documents/document_detail.html"
    if loc_type == "volume":
        template = "lc/volume_detail.html"
    elif loc_type == "sheet":
        template = "lc/sheet_detail.html"

    return render(
        request,
        template,
        context=context_dict)

class VolumeDetail(View):

    def get(self, request, volumeid):

        try:
            vol = Volume.objects.get(pk=volumeid)
        except Volume.DoesNotExist:
            i = Importer()
            vol = i.import_volume(volumeid)
            if vol is None:
                raise Http404

        context_dict = {
            "svelte_params": {
                "VOLUME": vol.to_json(),
            }
        }
        return render(
            request,
            "lc/volume_summary.html",
            context=context_dict
        )

class SimpleAPI(View):

    def get(self, request):
        qtype = request.GET.get("t", None)
        state = request.GET.get("s", None)
        city = request.GET.get("c", None)

        i = Importer(delay=0, verbose=True)

        ## returns a list of all cities with volumes in this state
        if qtype == "cities":
            city_list = i.get_city_list_by_state(state)
            missing = []
            for i in city_list:
                try:
                    reg = Region.objects.get(name__iexact=i[0])
                except Region.DoesNotExist:
                    missing.append(i)

            return JsonResponse(city_list, safe=False)

        ## return a list of all volumes in a city
        elif qtype == "volumes":

            city = parsers.unsanitize_name(state, city)
            volumes = i.get_volume_list_by_city(city, state)
            # for volume in volumes:
            #     volume["url"] = reverse("volume_summary", args=(volume["identifier"],))

            return JsonResponse(volumes, safe=False)
        
        else:
            return JsonResponse({})