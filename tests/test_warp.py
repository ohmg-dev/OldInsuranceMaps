import math

from django.test import tag
from osgeo import gdal

from ohmg.georeference.georeferencer import Georeferencer

from .base import OHMGTestCase


@tag("warp")
class HelmertTransformationTestCase(OHMGTestCase):
    def test_helmert_transformation_calculations(self):
        """This test runs through 8 permutations of GCPs, and makes
        sure that the calculations used to set up the helmert
        transformations return the right values for every permutation.
        """

        # assume an image with these dimensions
        img_width, img_height = 5, 8  # noqa: F841

        # inner (smallest) angle for a 3,4,5 triangle
        theta_345 = math.degrees(math.asin(3 / 5))

        # variables that define positions and expected values to test
        data_matrix = [
            (0, 2.5, 0, -0.5, 3),
            (2, 1.5, 90 - theta_345, 2.1, 2.2),
            (2.5, 0, 90, 3, 0.5),
            (2, -1.5, 90 + theta_345, 2.7, -1.4),
            (0, -2.5, 180, 0.5, -3),
            (-2, -1.5, 270 - theta_345, -2.1, -2.2),
            (-2.5, 0, 270, -3, -0.5),
            (-2, 1.5, 270 + theta_345, -2.7, 1.4),
        ]

        # GCP 1 stays constant
        # GCP 2's image coords stay constant while the geo coords move
        # clockwise around the origin.
        gcp1 = gdal.GCP(0, 0, 0, 1, 6)
        for gcpx, gcpy, target_rotation, x_offset, y_offset in data_matrix:
            # note 1. GCP args are: geo x, geo y, geo z (not used), img x, img y
            # note 2: img y uses inverse y axis (per GCP convention)
            # note 3: The distance between img GCPs is 5 which creates a 3,4,5
            # triangle during rotated permutations of the test (helpful)
            # note 4: All geo GCP coords halve the dimensions of the triangle
            # so scale is .5
            gcp2 = gdal.GCP(gcpx, gcpy, 0, 1, 1)

            g = Georeferencer(crs="EPSG:3857", transformation="helmert", gcps_gdal=[gcp1, gcp2])

            scale = g._calculate_scale()
            self.assertEqual(scale, 0.5)
            rotation = g._calculate_rotation(img_height=img_height)
            self.assertEqual(rotation, target_rotation)

            dx, dy = g._calculate_helmert_offsets(scale=scale, rotation=rotation)
            self.assertAlmostEqual(dx, x_offset)
            self.assertAlmostEqual(dy, y_offset)
