import os
import uuid
import json
import logging
from osgeo import gdal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.db import models


logger = logging.getLogger(__name__)


class GCP(models.Model):
    class Meta:
        verbose_name = "GCP"
        verbose_name_plural = "GCPs"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pixel_x = models.IntegerField(null=True, blank=True)
    pixel_y = models.IntegerField(null=True, blank=True)
    geom = models.PointField(null=True, blank=True, srid=4326)
    note = models.CharField(null=True, blank=True, max_length=255)
    gcp_group = models.ForeignKey("GCPGroup", on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True, editable=False, null=False, blank=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="created_by",
        on_delete=models.CASCADE,
    )
    last_modified = models.DateTimeField(auto_now=True, editable=False, null=False, blank=False)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="modified_by",
        on_delete=models.CASCADE,
    )


class GCPGroup(models.Model):
    TRANSFORMATION_CHOICES = (
        ("tps", "tps"),
        ("poly1", "poly1"),
        ("poly2", "poly2"),
        ("poly3", "poly3"),
    )

    class Meta:
        verbose_name = "GCP Group"
        verbose_name_plural = "GCP Groups"

    crs_epsg = models.IntegerField(null=True, blank=True)
    transformation = models.CharField(
        null=True,
        blank=True,
        choices=TRANSFORMATION_CHOICES,
        max_length=20,
    )

    def __str__(self):
        if self.doc:
            return self.doc.title
        else:
            return str(self.pk)

    @property
    def gcps(self):
        return GCP.objects.filter(gcp_group=self)

    @property
    def gdal_gcps(self):
        gcp_list = []
        for gcp in self.gcps:
            geom = gcp.geom.clone()
            geom.transform(self.crs_epsg)
            p = gdal.GCP(geom.x, geom.y, 0, gcp.pixel_x, gcp.pixel_y)
            gcp_list.append(p)
        return gcp_list

    @property
    def as_geojson(self):
        geo_json = {"type": "FeatureCollection", "features": []}

        for gcp in self.gcps:
            coords = json.loads(gcp.geom.geojson)["coordinates"]
            newcoords = [coords[1], coords[0]]
            # see note on this variable in settings.py
            if settings.SWAP_COORDINATE_ORDER is True:
                newcoords = coords
            geo_json["features"].append(
                {
                    "type": "Feature",
                    "properties": {
                        "id": str(gcp.pk),
                        "image": [gcp.pixel_x, gcp.pixel_y],
                        "username": gcp.last_modified_by.username,
                        "note": gcp.note,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": newcoords,
                    },
                }
            )
        return geo_json

    def as_points_file(self):
        content = "mapX,mapY,pixelX,pixelY,enable\n"
        for gcp in self.gcps:
            geom = gcp.geom.clone()
            geom.transform(self.crs_epsg)
            # pixel_y must be inverted b/c qgis puts origin at top left corner
            content += f"{geom.x},{geom.y},{gcp.pixel_x},-{gcp.pixel_y},1\n"

        return content

    def save_from_geojson(self, geojson, region, transformation=None):
        group = region.gcp_group if region.gcp_group else GCPGroup.objects.create()

        group.crs_epsg = 3857  # don't see this changing any time soon...
        group.transformation = transformation
        group.save()

        gcps_new, gcps_mod, gcps_del = 0, 0, 0

        # first remove any existing gcps that have been deleted
        for gcp in group.gcps:
            if str(gcp.id) not in [i["properties"].get("id") for i in geojson["features"]]:
                gcps_del += 0
                gcp.delete()

        for feature in geojson["features"]:
            id = feature["properties"].get("id", str(uuid.uuid4()))
            username = feature["properties"].get("username")
            user = get_user_model().objects.get(username=username)
            gcp, created = GCP.objects.get_or_create(
                id=id, defaults={"gcp_group": group, "created_by": user}
            )
            if created:
                gcps_new += 1

            pixel_x = feature["properties"]["image"][0]
            pixel_y = feature["properties"]["image"][1]
            new_pixel = (pixel_x, pixel_y)
            old_pixel = (gcp.pixel_x, gcp.pixel_y)
            lng = feature["geometry"]["coordinates"][0]
            lat = feature["geometry"]["coordinates"][1]

            new_geom = Point(lat, lng, srid=4326)

            # only update the point if one of its coordinate pairs have changed,
            # this also triggered when new GCPs have None for pixels and geom.
            if (
                new_pixel != old_pixel
                or not new_geom.equals(gcp.geom)
                or gcp.note != feature["properties"]["note"]
            ):
                gcp.note = feature["properties"]["note"]
                gcp.pixel_x = new_pixel[0]
                gcp.pixel_y = new_pixel[1]
                gcp.geom = new_geom
                gcp.last_modified_by = user
                gcp.save()
                if not created:
                    gcps_mod += 1
        gcps_ct = len(geojson["features"])
        logger.info(
            f"GCPGroup {group.pk} | GCPs ct: {gcps_ct}, new: {gcps_new}, mod: {gcps_mod}, del: {gcps_del}"
        )
        group.save()
        return group


def set_upload_location(instance, filename):
    """this function has to return the location to upload the file"""
    return os.path.join(f"{instance.type}s", filename)


# class LayerSetCategory(models.Model):
#     class Meta:
#         verbose_name_plural = "Set Categories"

#     slug = models.CharField(max_length=50)
#     description = models.CharField(max_length=200, null=True, blank=True)
#     display_name = models.CharField(max_length=50)

#     def __str__(self):
#         return self.display_name if self.display_name else self.slug


# class LayerSet(models.Model):
#     map = models.ForeignKey(
#         "core.map",
#         null=True,
#         blank=True,
#         on_delete=models.CASCADE,
#         related_name="layerset_old",
#     )
#     category = models.ForeignKey(
#         LayerSetCategory,
#         on_delete=models.PROTECT,
#         blank=True,
#         null=True,
#     )
#     multimask = models.JSONField(null=True, blank=True)
#     mosaic_geotiff = models.FileField(
#         upload_to="mosaics",
#         null=True,
#         blank=True,
#         max_length=255,
#         storage=OverwriteStorage(),
#     )
#     mosaic_json = models.FileField(
#         upload_to="mosaics",
#         null=True,
#         blank=True,
#         max_length=255,
#         storage=OverwriteStorage(),
#     )
#     extent = ArrayField(
#         models.FloatField(),
#         size=4,
#         null=True,
#         blank=True,
#     )

#     def __str__(self):
#         return f"{self.map} - {self.category}"

#     def layer_display_list(self):
#         """For display in the admin interface only."""
#         li = [
#             f"<li><a href='/admin/core/layer/{i.pk}/change'>{i}</a></li>" for i in self.layers.all()
#         ]
#         return mark_safe("<ul>" + "".join(li) + "</ul>")

#     layer_display_list.short_description = "Layers"

#     @property
#     def mosaic_cog_url(self):
#         """return the public url to the mosaic COG for this annotation set. If
#         no COG exists, return None."""
#         url = None
#         if self.mosaic_geotiff:
#             url = settings.MEDIA_HOST.rstrip("/") + self.mosaic_geotiff.url
#         return url

#     @property
#     def mosaic_json_url(self):
#         """return the public url to the mosaic JSON for this annotation set. If
#         no mosaic JSON exists, return None."""
#         url = None
#         if self.mosaic_json:
#             url = settings.MEDIA_HOST.rstrip("/") + self.mosaic_json.url
#         return url

#     @property
#     def multimask_extent(self):
#         """Calculate an extent based on all layers in this layerset's
#         multimask. If there is no multimask, return None."""
#         extent = None
#         if self.multimask:
#             feature_polygons = []
#             for v in self.multimask.values():
#                 poly = Polygon(v["geometry"]["coordinates"][0])
#                 feature_polygons.append(poly)
#             if len(feature_polygons) > 0:
#                 extent = MultiPolygon(feature_polygons, srid=4326).extent
#         return extent

#     @property
#     def multimask_geojson(self):
#         if self.multimask:
#             multimask_geojson = {"type": "FeatureCollection", "features": []}
#             for layer, geojson in self.multimask.items():
#                 geojson["properties"] = {"layer": layer}
#                 multimask_geojson["features"].append(geojson)
#             return multimask_geojson
#         else:
#             return None

#     def validate_multimask_geojson(self, multimask_geojson):
#         errors = []
#         for feature in multimask_geojson["features"]:
#             lyr = feature["properties"]["layer"]
#             try:
#                 geom_str = json.dumps(feature["geometry"])
#                 g = GEOSGeometry(geom_str)
#                 if not g.valid:
#                     logger.warning(f"{self} | invalid mask: {lyr} - {g.valid_reason}")
#                     errors.append((lyr, g.valid_reason))
#             except Exception as e:
#                 logger.warning(f"{self} | improper GeoJSON in multimask")
#                 errors.append((lyr, e))
#         return errors

#     def update_multimask_from_geojson(self, multimask_geojson):
#         errors = self.validate_multimask_geojson(multimask_geojson)
#         if errors:
#             return errors

#         if multimask_geojson["features"]:
#             self.multimask = {}
#             for feature in multimask_geojson["features"]:
#                 self.multimask[feature["properties"]["layer"]] = feature
#         else:
#             self.multimask = None
#         self.save(update_fields=["multimask"])

#     def save(self, *args, **kwargs):
#         extents = self.layers.all().values_list("extent", flat=True)
#         layer_extents = []
#         for extent in extents:
#             if extent:
#                 poly = Polygon().from_bbox(extent)
#                 layer_extents.append(poly)
#         if layer_extents:
#             combined = MultiPolygon(layer_extents)
#             self.extent = combined.extent

#         return super(self.__class__, self).save(*args, **kwargs)

#     def generate_mosaic_vrt(self):
#         """A helpful reference from the BPLv used during the creation of this method:
#         https://github.com/bplmaps/atlascope-utilities/blob/master/new-workflow/atlas-tools.py
#         """

#         gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
#         gdal.SetConfigOption("GDAL_TIFF_INTERNAL_MASK", "YES")

#         multimask_geojson = self.multimask_geojson
#         multimask_file_name = f"multimask-{self.category.slug}-{self.map.identifier}"
#         multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
#         with open(multimask_file, "w") as out:
#             json.dump(multimask_geojson, out, indent=1)

#         trim_list = []
#         layer_extent_polygons = []
#         for feature in multimask_geojson["features"]:
#             layer_name = feature["properties"]["layer"]

#             layer = Layer.objects.get(slug=layer_name)
#             if not layer.file:
#                 raise Exception(f"no layer file for this layer {layer_name}")

#             if layer.extent:
#                 extent_poly = Polygon.from_bbox(layer.extent)
#                 layer_extent_polygons.append(extent_poly)

#             gcp_group = layer.region.gcp_group
#             g = Georeferencer(
#                 crs=f"EPSG:{gcp_group.crs_epsg}",
#                 transformation=gcp_group.transformation,
#                 gcps_geojson=gcp_group.as_geojson,
#             )
#             in_path = g.warp(layer.region.file.path, return_vrt=True)

#             trim_name = os.path.basename(in_path).replace(".vrt", "_trim.vrt")
#             out_path = os.path.join(settings.TEMP_DIR, trim_name)

#             wo = gdal.WarpOptions(
#                 format="VRT",
#                 dstSRS="EPSG:3857",
#                 cutlineDSName=multimask_file,
#                 cutlineLayer=multimask_file_name,
#                 cutlineWhere=f"layer='{layer_name}'",
#                 cropToCutline=True,
#                 # srcAlpha = True,
#                 # dstAlpha = True,
#                 # creationOptions= [
#                 #     'COMPRESS=JPEG',
#                 # ]
#                 # creationOptions= [
#                 #     'COMPRESS=DEFLATE',
#                 #     'PREDICTOR=2',
#                 # ]
#             )
#             gdal.Warp(out_path, in_path, options=wo)
#             print("warped")

#             trim_list.append(out_path)

#         if len(layer_extent_polygons) > 0:
#             multi = MultiPolygon(layer_extent_polygons, srid=4326)

#         bounds = multi.transform(3857, True).extent
#         vo = gdal.BuildVRTOptions(
#             resolution="highest",
#             outputSRS="EPSG:3857",
#             outputBounds=bounds,
#             separate=False,
#         )
#         print("building vrt")

#         mosaic_vrt = os.path.join(
#             settings.TEMP_DIR, f"{self.map.identifier}-{self.category.slug}.vrt"
#         )
#         gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)

#         return mosaic_vrt

#     def generate_mosaic_cog(self):
#         start = datetime.now()

#         mosaic_vrt = self.generate_mosaic_vrt()

#         print("building final geotiff")

#         to = gdal.TranslateOptions(
#             format="COG",
#             creationOptions=[
#                 "BIGTIFF=YES",
#                 "COMPRESS=JPEG",
#                 "TILING_SCHEME=GoogleMapsCompatible",
#             ],
#         )

#         mosaic_tif = mosaic_vrt.replace(".vrt", ".tif")
#         gdal.Translate(mosaic_tif, mosaic_vrt, options=to)

#         existing_file_path = None
#         if self.mosaic_geotiff:
#             existing_file_path = self.mosaic_geotiff.path

#         file_name = f"{self.map.identifier}-{self.category.slug}__{datetime.now().strftime('%Y-%m-%d')}__{random_alnum(6)}.tif"

#         with open(mosaic_tif, "rb") as f:
#             self.mosaic_geotiff.save(file_name, File(f))

#         os.remove(mosaic_tif)
#         if existing_file_path:
#             os.remove(existing_file_path)

#         print(f"completed - elapsed time: {datetime.now() - start}")

#     def generate_mosaic_json(self, trim_all=False):
#         def write_trim_feature_cache(feature, file_path):
#             with open(file_path, "w") as f:
#                 json.dump(feature, f, indent=2)

#         def read_trim_feature_cache(file_path):
#             with open(file_path, "r") as f:
#                 feature = json.load(f)
#             return feature

#         logger.info(f"{self.vol.identifier} | generating mosaic json")

#         multimask_geojson = self.vol.multimask_geojson
#         multimask_file_name = f"multimask-{self.vol.identifier}"
#         multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
#         with open(multimask_file, "w") as out:
#             json.dump(multimask_geojson, out, indent=1)

#         logger.debug(f"{self.vol.identifier} | multimask loaded")
#         logger.info(f"{self.vol.identifier} | iterating and trimming layers")
#         trim_list = []
#         for feature in multimask_geojson["features"]:
#             layer_name = feature["properties"]["layer"]
#             layer = Layer.objects.get(slug=layer_name)
#             if not layer.file:
#                 logger.error(f"{self.vol.identifier} | no layer file for this layer {layer_name}")
#                 raise Exception(f"no layer file for this layer {layer_name}")
#             in_path = layer.file.path

#             layer_dir = os.path.dirname(in_path)
#             file_name = os.path.basename(in_path)
#             logger.debug(f"{self.vol.identifier} | processing layer file {file_name}")

#             file_root = os.path.splitext(file_name)[0]
#             existing_trimmed_tif = glob.glob(f"{layer_dir}/{file_root}*_trim.tif")
#             print(existing_trimmed_tif)

#             feat_cache_path = in_path.replace(".tif", "_trim-feature.json")
#             if os.path.isfile(feat_cache_path):
#                 cached_feature = read_trim_feature_cache(feat_cache_path)
#                 logger.debug(f"{self.vol.identifier} | using cached trim json boundary")
#             else:
#                 cached_feature = None
#                 write_trim_feature_cache(feature, feat_cache_path)

#             unique_id = random_alnum(6)
#             trim_vrt_path = in_path.replace(".tif", f"_{unique_id}_trim.vrt")
#             out_path = trim_vrt_path.replace(".vrt", ".tif")

#             # compare this multimask feature to the cached one for this layer
#             # and only (re)create a trimmed tif if they do not match
#             if feature != cached_feature or trim_all is True:
#                 wo = gdal.WarpOptions(
#                     format="VRT",
#                     dstSRS="EPSG:3857",
#                     cutlineDSName=multimask_file,
#                     cutlineLayer=multimask_file_name,
#                     cutlineWhere=f"layer='{layer_name}'",
#                     cropToCutline=True,
#                     creationOptions=["COMPRESS=LZW", "BIGTIFF=YES"],
#                     resampleAlg="cubic",
#                     dstAlpha=False,
#                     dstNodata="255 255 255",
#                 )
#                 gdal.Warp(trim_vrt_path, in_path, options=wo)

#                 to = gdal.TranslateOptions(
#                     format="GTiff",
#                     bandList=[1, 2, 3],
#                     creationOptions=[
#                         "TILED=YES",
#                         "COMPRESS=LZW",
#                         "PREDICTOR=2",
#                         "NUM_THREADS=ALL_CPUS",
#                         ## the following is apparently in the COG spec but doesn't work??
#                         # "COPY_SOURCE_OVERVIEWS=YES",
#                     ],
#                 )

#                 logger.debug(f"writing trimmed tif {os.path.basename(out_path)}")
#                 gdal.Translate(out_path, trim_vrt_path, options=to)
#                 write_trim_feature_cache(feature, feat_cache_path)

#                 img = gdal.Open(out_path, 1)
#                 if img is None:
#                     logger.warning(
#                         f"{self.vol.identifier} | file was not properly created, omitting: {file_name}"
#                     )
#                     continue
#                 logger.debug(f"{self.vol.identifier} | building overview: {file_name}")
#                 gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
#                 gdal.SetConfigOption("PREDICTOR", "2")
#                 gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
#                 img.BuildOverviews("AVERAGE", [2, 4, 8, 16])

#             else:
#                 logger.debug(f"{self.vol.identifier} | using existing trimmed tif {file_name}")

#             trim_list.append(out_path)

#         trim_urls = [
#             i.replace(os.path.dirname(settings.MEDIA_ROOT), settings.MEDIA_HOST.rstrip("/"))
#             for i in trim_list
#         ]
#         logger.info(f"{self.vol.identifier} | writing mosaic from {len(trim_urls)} trimmed tifs")
#         mosaic_data = MosaicJSON.from_urls(trim_urls, minzoom=14)
#         mosaic_json_path = os.path.join(settings.TEMP_DIR, f"{self.vol.identifier}-mosaic.json")
#         with MosaicBackend(mosaic_json_path, mosaic_def=mosaic_data) as mosaic:
#             mosaic.write(overwrite=True)

#         with open(mosaic_json_path, "rb") as f:
#             self.vol.mosaic_json = File(f, name=os.path.basename(mosaic_json_path))
#             self.vol.save()

#         logger.info(f"{self.vol.identifier} | mosaic created: {os.path.basename(mosaic_json_path)}")
#         return mosaic_json_path
