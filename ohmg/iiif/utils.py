from osgeo import gdal, osr

from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import Polygon

from ohmg.core.models import Layer
from ohmg.core.utils import full_reverse
from ohmg.georeference.georeferencer import Georeferencer


class IIIFResource:
    def __init__(self, layerid):
        self.layerid = layerid
        self.layer = Layer.objects.get(pk=layerid)
        self.region = self.layer.region
        self.document = self.region.document

        self.d_width, self.d_height = self.document.image_size

    def get_selector(self, trim=False):
        ## create coordinates for the selector
        coords_str = [
            f"{int(i[0])},{self.d_height-int(i[1])}" for i in self.region.boundary.coords[0]
        ]

        ## next step is to look for the multimask for this layer if one exists, and then
        ## transform it back to the selector coordinates.
        mm = self.layer.layerset2.multimask
        if mm and self.layer.slug in mm and trim:
            wgs84 = osr.SpatialReference()
            wgs84.ImportFromEPSG(4326)

            coords = mm[self.layer.slug]["geometry"]["coordinates"][0]
            ct = CoordTransform(SpatialReference("WGS84"), SpatialReference("EPSG:3857"))
            polygon = Polygon(coords)
            polygon.transform(ct)

            g = Georeferencer(
                crs=f"EPSG:{self.region.gcpgroup.crs_epsg}",
                transformation=self.region.gcpgroup.transformation,
                gcps_geojson=self.region.gcpgroup.as_geojson,
            )
            in_path = g.warp(self.region.file.path, return_gcps_vrt=True)
            ds = gdal.Open(in_path)
            transformer = gdal.Transformer(
                # Source datasource
                None,
                # Target datasource
                ds,
                # Transformer options that are ultimately passed to 'GDALCreateGenImgProjTransformer2()'
                # https://gdal.org/api/gdal_alg.html#_CPPv432GDALCreateGenImgProjTransformer212GDALDatasetH12GDALDatasetHPPc
                [
                    ## need to update this, different number if thin plate spline
                    "MAX_GCP_ORDER=1",
                ],
            )
            transposed, status = transformer.TransformPoints(False, polygon.coords[0])
            coords_str = [f"{i[0]},{i[1]}" for i in transposed]

        coords_join = " ".join(coords_str)

        return {
            "id": full_reverse("iiif_selector_view", args=(self.layerid,)),
            "type": "SpecificResource",
            "source": {
                "id": self.document.iiif_info,
                "type": "ImageService2",
                "height": self.d_height,
                "width": self.d_width,
            },
            "selector": {
                "type": "SvgSelector",
                "value": f'<svg><polygon points="{coords_join}" /></svg>',
            },
        }

    def get_gcps(self):
        extent = self.region.boundary.extent
        xmin, ymin, xmax, ymax = extent

        if self.region.gcpgroup.transformation == "poly1":
            transformation = {"type": "polynomial", "options": {"order": 1}}
        elif self.region.gcpgroup.transformation == "tps":
            transformation = {
                "type": "thinPlateSpline",
            }
        else:
            raise Exception("invalid transformation", self.region.gcpgroup.transformation)

        return {
            "id": full_reverse("iiif_gcps_view", args=(self.layerid,)),
            "type": "FeatureCollection",
            "transformation": transformation,
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "resourceCoords": [
                            i["properties"]["image"][0] + xmin,
                            i["properties"]["image"][1] + (self.d_height - ymax),
                        ],
                    },
                    "geometry": i["geometry"],
                }
                for i in self.region.gcpgroup.as_geojson["features"]
            ],
        }

    def get_resource(self, trim=False):
        ## Ok, getting an extent or envelope from the region boundary produces cartesian x,y
        ## with 0,0 at the bottom left. However, the stored image GCP coords are with 0,0 at
        ## top left. Translating the GCP image coords is performed like this:
        ## 1) get the extent of the region, and from that the minX and maxY
        ##   Min X: This is added to the GCP x coord to "push" it the proper distance from the origin,
        ##          such that the GCP coord from the small region is now translated to the source doc
        ##   Max Y: The max Y is cartesion TOP of the small region, but this number needs to be
        ##          SUBTRACTED from the source height of the document, to get the distance from the
        ##          top of the small region to the top of the source document. Then, this distance
        ##          is added to the GCP x coord to "push" it down the proper distance from the top
        ##          of the source document

        return {
            "id": full_reverse("iiif_resource_view", args=(self.layerid,)),
            "type": "Annotation",
            "@context": [
                "http://iiif.io/api/extension/georef/1/context.json",
                "http://iiif.io/api/presentation/3/context.json",
            ],
            "label": str(self.layer),
            "created": self.region.created.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "modified": self.region.last_updated.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "creator": self.layer.get_creators(),
            "motivation": "georeferencing",
            ## Technically, these could be just be the urls to each resolvable endpoint,
            ## instead of actually embedding the data here
            "target": self.get_selector(),
            "body": self.get_body(),
        }
