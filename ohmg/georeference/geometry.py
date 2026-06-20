import math
from typing import List, Tuple

import numpy as np
from django.contrib.gis.geos import LineString


def azimuth_from_coords(coords: List[Tuple[float, float]]) -> float:
    """Calculate the least-squares slope of the input coordinates, return
    as degrees relative to the x axis."""

    x_coords = [i[0] for i in coords]
    y_coords = [i[1] for i in coords]
    x_diff = x_coords[-1] - x_coords[0]
    y_diff = y_coords[-1] - y_coords[0]

    # handle cases where the fit line would be horizontal or vertical,
    # as well as an issue where passing all 0s to np.polyfit (e.g. all
    # of the x values are 0, even though there are different y values)
    # raises an exception
    if len(set(x_coords)) == 1:
        if y_diff > 0:
            azimuth = 0
        else:
            azimuth = 180
    elif len(set(y_coords)) == 1:
        if x_diff > 0:
            azimuth = 90
        else:
            azimuth = 270
    # now handle all other cases by calculating the slope
    else:
        slope, intercept = np.polyfit(x_coords, y_coords, 1)

        # this is the angle from 0 axis
        angle = math.degrees(math.atan(slope))

        # now convert the angle to degrees from north by comparing
        # the first and last set of coords to determine the general
        # orientation of the fit line
        x_diff = coords[-1][0] - coords[0][0]
        y_diff = coords[-1][1] - coords[0][1]

        # orientation: ne
        if x_diff > 0 and y_diff > 0:
            azimuth = 90 - angle
        # orientation: se
        elif x_diff > 0 and y_diff < 0:
            azimuth = 90 + abs(angle)
        # orientation: sw
        elif x_diff < 0 and y_diff < 0:
            azimuth = 270 - angle
        # orientation: nw
        elif x_diff < 0 and y_diff > 0:
            azimuth = 270 + abs(angle)

    return azimuth


def extend_vector(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    distance: float,
) -> Tuple[float, float]:
    """https://math.stackexchange.com/a/3346108 (credit to Oliver Roche)
    takes the two input points, which represent a vector, and creates a
    third point that would extend that vector by the given distance."""

    x1, y1 = p1
    x2, y2 = p2
    rise = y2 - y1
    run = x2 - x1

    norm = math.sqrt((run**2) + (rise**2))

    # if negative coords are used norm will be 0.0, silently return original point
    if norm == 0.0:
        return (x2, y2)

    x3 = x2 + distance * (run / norm)
    y3 = y2 + distance * (rise / norm)

    return (x3, y3)


def extend_linestring(linestring: LineString, distance: int = 10) -> LineString:
    """takes the input GEOS LineString and extends it in both directions
    (following the trajectory of each end segment) by the given distance."""

    coord_list = list(linestring.coords)

    new_start = extend_vector(coord_list[1], coord_list[0], distance)
    new_end = extend_vector(coord_list[-2], coord_list[-1], distance)

    coord_list.insert(0, new_start)
    coord_list.append(new_end)

    return LineString(coord_list)
