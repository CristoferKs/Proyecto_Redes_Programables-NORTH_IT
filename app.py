import requests
import urllib.parse
import json
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# ConfiguraciÃ³n inicial
ROUTE_URL = "https://graphhopper.com/api/1/route?"
GEO_URL = "https://graphhopper.com/api/1/geocode?"
API_KEY = "d563e3c8-9270-44f6-bbaf-b328e2c39ed0" # Reemplazar con la clave obtenida en el Lab [cite: 96, 259]

def get_geocoding(location):
    """Obtiene coordenadas y valida la ubicaciÃ³n[cite: 97, 331]."""
    if not location:
        return None
    
    url = GEO_URL + urllib.parse.urlencode({"q": location, "limit": "1", "key": API_KEY})
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if len(data["hits"]) > 0:
            return {
                "lat": data["hits"][0]["point"]["lat"],
                "lng": data["hits"][0]["point"]["lng"],
                "name": data["hits"][0].get("name", location),
                "full_name": f"{data['hits'][0].get('name', '')}, {data['hits'][0].get('state', '')}, {data['hits'][0].get('country', '')}"
            }
    return None

def log_route(data):
    """Implementa el historial de rutas para auditorÃ­a."""
    with open("route_history.log", "a") as f:
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": data
        }
        f.write(json.dumps(log_entry) + "\n")

@app.route('/get_route', methods=['GET'])
def get_route():
    """Endpoint de la API REST para consumo remoto."""
    start_loc = request.args.get('start')
    end_loc = request.args.get('end')
    vehicle = request.args.get('vehicle', 'car') # Por defecto car [cite: 146, 941]

    # 1. ValidaciÃ³n de entrada 
    if not start_loc or not end_loc:
        return jsonify({"error": "Se requieren ubicaciones de inicio y fin"}), 400

    # 2. GeocodificaciÃ³n
    origin = get_geocoding(start_loc)
    destination = get_geocoding(end_loc)

    if not origin or not destination:
        return jsonify({"error": "No se pudo encontrar una o ambas ubicaciones"}), 404

    # 3. ConstrucciÃ³n de la ruta [cite: 160, 648]
    params = {
        "key": API_KEY,
        "vehicle": vehicle,
        "point": [f"{origin['lat']},{origin['lng']}", f"{destination['lat']},{destination['lng']}"]
    }
    
    # urllib.parse no maneja bien listas repetidas de 'point', se construye manualmente
    points_str = f"&point={origin['lat']},{origin['lng']}&point={destination['lat']},{destination['lng']}"
    base_params = urllib.parse.urlencode({"key": API_KEY, "vehicle": vehicle})
    full_route_url = ROUTE_URL + base_params + points_str

    route_resp = requests.get(full_route_url)
    
    if route_resp.status_code == 200:
        route_data = route_resp.json()
        path = route_data["paths"][0]
        
        result = {
            "origin": origin["full_name"],
            "destination": destination["full_name"],
            "distance_km": round(path["distance"] / 1000, 2),
            "duration": f"{int(path['time']/1000/60)} min",
            "vehicle": vehicle,
            "instructions": [inst["text"] for inst in path["instructions"]]
        }
        
        # Registrar en el historial 
        log_route(result)
        return jsonify(result)
    
    return jsonify({"error": "No se encontrÃ³ conexiÃ³n entre ubicaciones"}), 400

if __name__ == '__main__':
    print("Iniciando servidor de NORTH IT SUPPORT...")
    app.run(debug=True, port=5000)
