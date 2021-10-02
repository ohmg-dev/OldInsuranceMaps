import os
import copy
import json
import logging
from PIL import Image, ImageDraw, ImageFilter

from guardian.shortcuts import get_perms, get_objects_for_user

from django.conf import settings
from django.core import management
from django.urls import reverse
from django.template import loader
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.middleware import csrf

from geonode.base.utils import ManageResourceOwnerPermissions
from geonode.utils import resolve_object, build_social_links
from geonode.security.views import _perms_info_json
from geonode.documents.models import Document
from geonode.documents.views import _resolve_document, document_detail, document_download
from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.base.models import Link
from geonode.monitoring import register_event
from geonode.monitoring.models import EventType

from georeference.tasks import (
    split_image_as_task,
    georeference_document_as_task,
)
from .models import GCPGroup, SplitSession
from .splitter import Splitter
from .georeferencer import Georeferencer, get_path_variant
from .utils import (
    document_as_iiif_resource,
    document_as_iiif_canvas,
    document_as_iiif_manifest,
    mapserver_add_layer,
    mapserver_remove_layer,
)

logger = logging.getLogger("geonode.georeference.views")

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this document.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")

def _resolve_document_complete(request, docid):

    document = None
    try:
        document = _resolve_document(
            request,
            docid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
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

    if document is None:
        return HttpResponse(
            'An unknown error has occured.',
            content_type="text/plain",
            status=401
        )

    else:
        return document

class SummaryView(View):

    def get(self, request, docid):
        pass

class SplitView(View):

    def get(self, request, docid):
        """
        Returns the splitting interface for this document.
        """

        document = _resolve_document_complete(request, docid)

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

        im_rgb = Image.open(document.doc_file)
        width, height = im_rgb.size

        base = settings.SITEURL.rstrip("/")
        # iiif_info_url = base + reverse('document_info', args=(document.id,))
        # iiif_manifest_url = base + reverse('document_manifest', args=(document.id,))
        download_url = base + reverse('document_download', args=(document.id,))
        process_url = base + reverse('split_view', args=(document.id,))

        try:
            sesh = SplitSession.objects.get(document=document)
            divisions = sesh.divisions
            cut_lines = sesh.cut_lines
        except SplitSession.DoesNotExist:
            divisions, cut_lines = None, None

        svelte_params = {
            "title": document.title,
            "imgwidth": width,
            "imgheight": height,
            "divisions": divisions,
            "cut_lines": cut_lines,
            "doc_url": download_url,
            "process_url": process_url,
            "csrftoken": csrf.get_token(request),
        }

        context_dict = {
            "svelte_params": svelte_params,
            "resource": document,


            ## unclear at this point if any of the following will be necessary once
            ## permissions are properly implemented throughout the app, so they are
            ## just commented out for now.
            # 'access_token': access_token,
            # 'perms_list': perms_list,
            # 'permissions_json': permissions_json,
            # 'group': group,
            # 'metadata': metadata,
            # 'imgwidth': width,
            # 'imgheight': height,

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

        return render(
            request,
            "georeference/split_interface.html",
            context=context_dict)

    def post(self, request, docid):

        document = _resolve_document_complete(request, docid)


        body = json.loads(request.body)
        cut_lines = body.get("lines", [])

        dryrun = body.get("dryrun", False)

        splitter = Splitter(document=document)
        divs = splitter.generate_divisions(cut_lines)

        if dryrun is True:
            return JsonResponse({"success": True, "polygons": divs})

        res = split_image_as_task.apply_async(
            (docid, cut_lines, request.user.pk), queue="update"
        )

        redirect_url = reverse('document_detail', kwargs={'docid': docid}) + "#georeference"

        return JsonResponse({"success":True, "redirect_to": redirect_url})


class TrimView(View):

    def get(self, request):
        pass

    def post(self, request):
        pass

class GeoreferenceView(View):

    def get(self, request, docid):
        """
        Returns the georeferencing interface for this document.
        """

        document = _resolve_document_complete(request, docid)
        if not isinstance(document, Document):
            return document

        try:
            gcp_group = GCPGroup.objects.get(document=document)
            incoming_gcps = gcp_group.as_geojson
            incoming_transformation = gcp_group.transformation
        except GCPGroup.DoesNotExist:
            incoming_gcps, incoming_transformation = None, None

        # get the iiif info for the document file
        base = settings.SITEURL.rstrip("/")
        iiif_info_url = base + reverse('document_info', args=(document.id,))
        iiif_manifest_url = base + reverse('document_manifest', args=(document.id,))
        download_url = base + reverse('document_download', args=(document.id,))

        permission_manager = ManageResourceOwnerPermissions(document)
        permission_manager.set_owner_permissions_according_to_workflow()

        # Call this first in order to be sure "perms_list" is correct
        permissions_json = _perms_info_json(document)

        im_rgb = Image.open(document.doc_file)
        width, height = im_rgb.size

        username = request.user.username
        if username == "":
            username = "<anonymous>"

        georeference_url = base + reverse('georeference_view', kwargs={"docid": docid})

        preview_layer = mapserver_add_layer(get_path_variant(document.doc_file.path, "VRT"))

        # placeholders to be refactored/set elsewhere
        map_center = [-10291143, 3673446] # could be replaced with region extent

        svelte_params = {
            "IMG_WIDTH": width,
            "IMG_HEIGHT": height,
            "DOC_URL": download_url,
            "DOC_ID": docid,
            "CSRFTOKEN": csrf.get_token(request),
            "USERNAME": username,
            "SUBMIT_URL": georeference_url,
            "MAP_CENTER": map_center,
            "INCOMING_GCPS": incoming_gcps,
            "INCOMING_TRANSFORMATION": incoming_transformation,
            "MAPSERVER_ENDPOINT": settings.MAPSERVER_ENDPOINT,
            "MAPSERVER_LAYERNAME": preview_layer,
            "MAPBOX_API_KEY": settings.MAPBOX_API_KEY,
        }

        context_dict = {
            'resource': document,
            'svelte_params': svelte_params,
            'permissions_json': permissions_json,
            'iiif_info_url': iiif_info_url,
            'iiif_manifest_url': iiif_manifest_url,
            'download_url': download_url,
        }

        return render(
            request,
            "georeference/georeference_interface.html",
            context=context_dict)

    def post(self, request, docid):
        """
        Runs the georeferencing process for this document.
        """

        if request.body:
            body = json.loads(request.body)
        else:
            return JsonResponse({
                "status": "error",
                "message": "not enough information."
            })

        docid = body.get("docid")
        document = _resolve_document_complete(request, docid)
        if not isinstance(document, Document):
            return document

        gcp_geojson = body.get("gcp_geojson", {})
        transformation = body.get("transformation", "poly1")

        # determine whether this is change to GCPs during editing or it's the
        # completion of the georeferencing process.
        operation = body.get("operation", "preview")

        response = {
            "status": "",
            "message": ""
        }

        # if preview mode, modify/create the vrt for this map.
        # the vrt layer should already served to the interface via mapserver,
        # and it will be automatically reloaded there.
        if operation == "preview":

            # prepare Georeferencer object
            g = Georeferencer(epsg_code=3857)
            g.load_gcps_from_geojson(gcp_geojson)
            g.set_transformation(transformation)
            try:
                out_path = g.georeference(
                    document.doc_file.path,
                    out_format="VRT",
                )
                response["status"] = "success"
                response["message"] = "all good"
            except Exception as e:
                print("exception caught")
                print(e)
                response["status"] = "fail"
                response["message"] = str(e)

        # if submission, save updated/new GCPs, run warp to create GeoTiff.
        elif operation == "submit":

            # saving the gcps like this will create the full group and its
            # connection to the document, which will be utilized during
            # GeoreferenceSession.run(), called in the task below.
            GCPGroup().save_from_geojson(gcp_geojson, document, transformation)

            georeference_document_as_task.apply_async(
                (docid, request.user.pk),
                queue="update"
            )

        elif operation == "cleanup":

            mapserver_remove_layer(document.doc_file.path)

            response["status"] = "success"
            response["message"] = "all good"
            response["redirect_to"] = "/layers"

        return JsonResponse(response)

def iiif2_endpoint(request, docid, iiif_object_requested):
    """ create a iiif v2 manifest, canvas, resource, or info.json object for a
    document image. info.json is not possible if an IIIF server is not enabled.
    """

    IIIF_SERVER_ENABLED = getattr(settings, "IIIF_SERVER_ENABLED", False)

    document = _resolve_document_complete(request, docid)
    if not isinstance(document, Document):
        return document

    if iiif_object_requested == "manifest":
        return JsonResponse(document_as_iiif_manifest(
            document,
            iiif_server=IIIF_SERVER_ENABLED,
        ))

    elif iiif_object_requested == "canvas":
        return JsonResponse(document_as_iiif_canvas(
            document,
            iiif_server=IIIF_SERVER_ENABLED,
        ))

    elif iiif_object_requested == "resource":
        return JsonResponse(document_as_iiif_resource(
            document,
            iiif_server=IIIF_SERVER_ENABLED,
        ))

    elif iiif_object_requested == "info":
        # if there is a iiif server set up, then this will redirect to that url
        # to supply the info.json generated there.
        if IIIF_SERVER_ENABLED is True:
            fname = os.path.basename(document.doc_file.name)
            info_url = f"{settings.IIIF_SERVER_LOCATION}/iiif/2/{fname}/info.json"
            return redirect(info_url)

        # if there is no iiif server, info.json is not supported.
        # see: https://github.com/IIIF/api/issues/1983
        else:
            return JsonResponse({
                "status": "not implemented",
                "message": "info.json is not available without a IIIF server."
            })

    else:
        return HttpResponse(
            loader.render_to_string(
                "404.html", context={
                }, request=request), status=404)
