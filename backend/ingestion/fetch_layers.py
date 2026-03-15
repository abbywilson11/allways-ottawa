import requests
import geopandas as gpd
import os
from io import BytesIO

DATASETS = {
    'sidewalks': 'https://opendata.ottawa.ca/datasets/ottawa::sidewalk-network.geojson',
    'pedestrian_network': 'https://opendata.ottawa.ca/datasets/ottawa::pedestrian-network.geojson',
    'pathways': 'https://opendata.ottawa.ca/datasets/ottawa::pathways.geojson',
    'cycling_network': 'https://opendata.ottawa.ca/datasets/ottawa::cycling-network.geojson',
    'parks_greenspace': 'https://opendata.ottawa.ca/datasets/ottawa::parks-and-greenspace.geojson',
    'traffic_collisions': 'https://opendata.ottawa.ca/datasets/ottawa::traffic-crash-data.geojson',
    'benches': 'https://opendata.ottawa.ca/datasets/ottawa::benches.geojson',
    'washrooms': 'https://opendata.ottawa.ca/datasets/ottawa::public-washrooms.geojson',
    'libraries': 'https://opendata.ottawa.ca/datasets/ottawa::ottawa-public-library-branches.geojson',
    'community_centres': 'https://opendata.ottawa.ca/datasets/ottawa::community-social-support-programs.geojson',
    'recreation_facilities': 'https://opendata.ottawa.ca/datasets/ottawa::recreation-facility.geojson',
}

SAVE_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw')

def fetch_dataset(name, url):
    """Download a GeoJSON dataset and save it locally."""
    print(f'Fetching {name}...')
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        gdf = gpd.read_file(BytesIO(response.content))
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        out_path = os.path.join(SAVE_DIR, f'{name}.geojson')
        gdf.to_file(out_path, driver='GeoJSON')
        print(f'  Saved {len(gdf)} features to {out_path}')
        return gdf
    except Exception as e:
        print(f'  ERROR fetching {name}: {e}')
        return None

def fetch_all():
    os.makedirs(SAVE_DIR, exist_ok=True)
    results = {}
    for name, url in DATASETS.items():
        results[name] = fetch_dataset(name, url)
    return results

if __name__ == '__main__':
    fetch_all()
    print('Done! All datasets saved to data/raw/')