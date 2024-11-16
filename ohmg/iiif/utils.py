import os
import json
#import base64
from PIL import Image

from django.conf import settings
from django.urls import reverse

from ohmg.core.utils import full_reverse

def region_as_iiif_resource(region):
    return {
        "id": full_reverse("iiif_resource_view", args=(region.pk,)),
        "type": "Annotation",
        "@context": [
            "http://iiif.io/api/extension/georef/1/context.json",
            "http://iiif.io/api/presentation/3/context.json",
        ],
        "created": "<timestamp>",
        "modified": "<timestamp>",
        "motivation": "georeferencing",
        "target": ""
    }

## ~~ IIIF support (Old content) ~~

def document_as_iiif_resource(document, iiif_server=False):

    img = Image.open(document.doc_file)
    width, height = img.size

    resource = {
      "@type": "dctypes:Image",
      "width": width,
      "height": height
    }

    if iiif_server is True:
        iiif2_base = f"{settings.IIIF_SERVER_LOCATION}/iiif/2"
        fname = os.path.basename(document.doc_file.name)
        resource["@id"] = f"{iiif2_base}/{fname}/full/max/0/default.jpg",
        resource["service"] = {
            "@context": "http://iiif.io/api/image/2/context.json",
            "@id": f"{iiif2_base}/{fname}",
            "profile": "http://iiif.io/api/image/2/level2.json",
            "protocol": "http://iiif.io/api/image"
        }
    else:
        img_url = settings.SITEURL.rstrip("/") + document.doc_file.url
        resource["@id"] = img_url

    return resource

def document_as_iiif_canvas(document, resource=None, iiif_server=False):

    this_url = reverse('document_canvas', args=(document.id,))
    canvas_id = settings.SITEURL.rstrip("/") + this_url

    if resource is None:
        resource = document_as_iiif_resource(document, iiif_server=iiif_server)

    canvas = {
      "@context": "http://iiif.io/api/presentation/2/context.json",
      "@id": canvas_id,
      "@type": "sc:Canvas",
      "label": "CanvasLabel",
      "width": resource["width"],
      "height": resource["height"],
      "images": [
        {
          "@type": "oa:Annotation",
          "motivation": "sc:painting",
          "on": canvas_id,
          "resource": resource
        }
      ]
    }

    return canvas

def document_as_iiif_manifest(document, canvas=None, iiif_server=False):
    """ creates a manifest for the document's image """

    ## this base64 encoding seems optional, but would probably be good to work in
    # base_url = "http://localhost:8080/cantaloupe/iiii/2/"
    # urlSafeEncodedBytes = base64.urlsafe_b64encode(base_url.encode("utf-8"))
    # urlSafeEncodedStr = str(urlSafeEncodedBytes, "utf-8")

    this_url = reverse('document_manifest', args=(document.id,))
    manifest_id = settings.SITEURL.rstrip("/") + this_url

    if canvas is None:
        canvas = document_as_iiif_canvas(document, iiif_server=iiif_server)

    manifest = {
      "@context": "http://iiif.io/api/presentation/2/context.json",
      "@type": "sc:Manifest",
      "@id": manifest_id,
      "label": document.title,
      "description": "Description.",
      "attribution": "Attribution",
      "thumbnail": document.thumbnail_url,
      "sequences": [
        {
          "@type": "sc:Sequence",
          "canvases": [
            canvas
          ]
        }
      ]
    }

    return manifest

def generate_annotation_template():

    return {
        "@id": "https://bertspaan.nl/iiifmaps/#/?url=https://purl.stanford.edu/vg994wz9415/iiif/manifest",
        "type": "AnnotationPage",
        "@context": [
            "http://geojson.org/geojson-ld/geojson-context.jsonld",
            "http://iiif.io/api/presentation/3/context.json"
        ],
        "items": [
            {
                "type": "Annotation",
                "motivation": "georeference-ground-control-points",
                "target": "https://purl.stanford.edu/vg994wz9415/iiif/manifest",
                "body": {
                    "type": "FeatureCollection",
                    "features": []
                }
            }
        ]
    }

def gcps_as_annotation(gcps):
    """Has not been tested since having been moved here, but should work
    as follows:

    from ohmg.georeference.models import GCPGroup
    
    g = GCPGroup.objects.get(document=document)
    anno = gcps_as_annotation(g.gcps)

    Note that any abrbitrary list of GCP objects can be passed in here.
    """

    ## this template acquisition should be refactored...
    anno_template = generate_annotation_template()
    with open(anno_template, "r") as o:
        anno = json.loads(o.read())

    ## WARNING: the order of the coordinates in the geometry below
    ## may need to be switched. see as_geojson() for example.
    for gcp in gcps:
        gcp_feat = {
            "type": "Feature",
            "properties": {
                "id": str(gcp.pk),
                "pixel": [gcp.pixel_x, gcp.pixel_y]
            },
            "geometry": json.loads(gcp.geom.geojson)
            }
        anno['items'][0]['body']['features'].append(gcp_feat)

    return anno