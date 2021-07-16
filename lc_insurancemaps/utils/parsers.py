import pytz
from datetime import datetime

from .enumerations import STATE_CHOICES

def full_capitalize(in_str):
    return " ".join([i.capitalize() for i in in_str.split(" ")])

def parse_location_info(item):

    info = {"city": None, "county": None, "state": None}

    # handle the fact that sometimes each location tag is a dictionary like
    # {'bexar county': 'https://www.loc.gov/search/?at=item&fa=location:bexar+county&fo=json'}
    # while other times each location tag is just a string.
    locations = []
    for l in item['location']:
        if isinstance(l, dict):
            locations.append(list(l.keys())[0])
        else:
            locations.append(l)

    # elaborate parsing of location tags

    # first find the county/parish and remove that from the list
    county_position = None
    for index, l in enumerate(locations):
        l_words = [i.lower() for i in l.split(" ")]
        if "county" in l_words or "parish" in l_words or "counties" in l_words\
          or "census division" in l:
            info["county"] = full_capitalize(l)
            county_position = index
    if county_position is not None:
        del locations[county_position]


    # next compare remaining tags to the title and only the city name
    # should match
    city_position = None
    if not "item" in item:
        print(item['id'])
        raise Exception
    city_seg = item["item"]["title"].split(",")[0].lower()
    if " from " in city_seg:
        title_city = city_seg.split(" from ")[1].lower()
    else:
        title_city = city_seg
    for index, l in enumerate(locations):
        if l == title_city:
            info["city"] = full_capitalize(l)
            city_position = index
    if city_position is not None:
        del locations[city_position]

    # finally the state should be the only remaining tag. check against the
    # list of valid state names
    state_position = None
    for index, l in enumerate(locations):
        if l.lower() in [i[0].lower() for i in STATE_CHOICES]:
            info["state"] = full_capitalize(l)
            state_position = index
    if state_position is not None:
        del locations[state_position]

    # print leftover tags
    if len(locations) > 0:
        msg = f"WARNING: unparsed location tags - {item['id']} - {locations}"
        print(msg)

    return info

def parse_date_info(item):

    month_lookup = {
        1:"JAN.", 2:"FEB.", 3:"MAR.", 4:"APR.", 5:"MAY.", 6:"JUN.",
        7:"JUL.", 8:"AUG.", 9:"SEP.", 10:"OCT.", 11:"NOV.", 12:"DEC."
    }

    info = {"year": None, "month": None}

    date_tag = item.get("date", None)
    if date_tag is None:
        return info

    try:
        dt = datetime.strptime(date_tag, "%Y-%m")
        d = pytz.utc.localize(dt)
        info["datetime"] = d
        info["year"] = d.year
        info["month"] = month_lookup[d.month]
    except ValueError:
        try:
            dt = datetime.strptime(date_tag, "%Y")
            d = pytz.utc.localize(dt)
            info["datetime"] = d
            info["year"] = d.year
        except ValueError:
            print("problem parsing date: " + date_tag)

    return info
