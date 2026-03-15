import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from db import execute_query
from routing.osrm_client import get_routes, extract_waypoints
from routing.scorer import score_route_segment, compute_composite_score
from routing.weights import RouteWeights, PRESETS
from ai.allen import chat_with_allen

load_dotenv()

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'AllWays Ottawa API is running'})

# ─────────────────────────────────────
# ROUTES ENDPOINT
# ─────────────────────────────────────
@app.route('/api/routes', methods=['POST'])
def routes():
    """
    Get 2-3 scored route alternatives between two points.
    Body: { origin: {lat, lng}, destination: {lat, lng}, weights: {...} }
    """
    body = request.get_json()
    if not body:
        return jsonify({'error': 'Request body required'}), 400

    try:
        origin = body['origin']
        dest = body['destination']
        w_dict = body.get('weights', {})
        weights = RouteWeights.from_dict(w_dict)

        osrm_routes = get_routes(origin['lat'], origin['lng'], dest['lat'], dest['lng'])
        if not osrm_routes:
            return jsonify({'error': 'No route found'}), 404

        scored = []
        for i, route in enumerate(osrm_routes[:3]):
            waypoints = extract_waypoints(route)
            sample = waypoints[::5] or waypoints[:1]
            seg_scores = [score_route_segment(lat, lng) for lat, lng in sample]
            composite = compute_composite_score(seg_scores, weights)
            n = len(seg_scores)
            avg_scores = {k: round(sum(s[k] for s in seg_scores)/n, 3) for k in seg_scores[0]}
            scored.append({
                'id': i,
                'geometry': route['geometry'],
                'distance_m': route['distance'],
                'duration_s': route['duration'],
                'composite_score': composite,
                'scores': avg_scores,
            })

        scored.sort(key=lambda r: r['composite_score'], reverse=True)
        return jsonify({'routes': scored})

    except KeyError as e:
        return jsonify({'error': f'Missing field: {e}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────
# ALLEN AI ENDPOINT
# ─────────────────────────────────────
@app.route('/api/allen', methods=['POST'])
def allen():
    """
    Send a message to Allen and get routing weights + explanation.
    Body: { message: string, conversation_history: [{role, content}] }
    """
    body = request.get_json()
    user_message = body.get('message', '')
    history = body.get('conversation_history', [])
    if not user_message:
        return jsonify({'error': 'message required'}), 400
    try:
        result = chat_with_allen(user_message, history)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────
# LAYERS ENDPOINT
# ─────────────────────────────────────
@app.route('/api/layers/<layer_name>')
def get_layer(layer_name):
    """Return a PostGIS table as GeoJSON for the map overlay."""
    ALLOWED = ['sidewalks','pedestrian_network','pathways','cycling_network',
               'parks_greenspace','benches','washrooms','libraries',
               'community_centres','recreation_facilities','transit_stops']
    if layer_name not in ALLOWED:
        return jsonify({'error': 'Unknown layer'}), 404
    rows = execute_query(
        f"SELECT ST_AsGeoJSON(geom) as geojson FROM {layer_name} LIMIT 5000"
    )
    features = [{'type':'Feature','geometry':json.loads(r['geojson']),'properties':{}} for r in rows]
    return jsonify({'type':'FeatureCollection','features':features})

# ─────────────────────────────────────
# GEOCODING ENDPOINT
# ─────────────────────────────────────
@app.route('/api/geocode')
def geocode():
    """Convert an address string to lat/lng using Nominatim (OpenStreetMap)."""
    import requests as req
    address = request.args.get('q', '')
    if not address:
        return jsonify({'error': 'q parameter required'}), 400
    r = req.get(
        'https://nominatim.openstreetmap.org/search',
        params={'q': f'{address}, Ottawa, Ontario', 'format':'json', 'limit':1},
        headers={'User-Agent': 'AllWaysOttawa/1.0'}
    )
    results = r.json()
    if not results:
        return jsonify({'error': 'Address not found'}), 404
    return jsonify({'lat': float(results[0]['lat']), 'lng': float(results[0]['lon'])})

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5001))
    app.run(debug=True, port=port)