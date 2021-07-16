import json
import time
import requests
import argparse
from urllib.parse import urlparse, parse_qs
from archive_connections import LOC

if 1 == 2:
    city = "gadsden"
    state = "alabama"

    url = f"https://www.loc.gov/collections/sanborn-maps/?fa=location:{city}|location:{state}&fo=json"

    print(url)

    response = requests.get(url)

    data = json.loads(response.content)

    results = data['results']

    print(f"total results: {len(results)}")

    # there should only ever be one unique title
    titles = set()
    for result in results:
        time.sleep(5)
        result_url = result['url']+"?fo=json"
        print(result_url)
        result = json.loads(requests.get(result_url).content)
        resources = result.pop('resources')
        item = result.pop('item')
        # print(json.dumps(item, indent=2))
        title = item['title']
        titles.add(title)
        print(f"title: {title}")
        print(f"date: {item['date']}")
        for sheet in resources[0]['files']:
            for f in sheet:
                if f['mimetype'] == "image/jp2":
                    print(f['url'])
     
    print(titles)

def download_from_loc_url(url):
    
    o = urlparse(url)
    query = parse_qs(o.query)
    
    base = f"{o.scheme}://{o.netloc}{o.path}"
    print(url)
    result = json.loads(requests.get(base+"?fo=json").content)
    #print(json.dumps(result, indent=2))
    print(result.keys())



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='resource url')
    parser.add_argument('--location', help='location query strings', nargs="*")
    args = parser.parse_args()

    url = args.url
    location_list = args.location

    loc = LOC()
    loc.get_sanborns_by_location(location_list)
    
    # download_from_loc_url(url)
