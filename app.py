import requests
import urllib.parse
import json
import os
from flask import Flask, request, jsonify, render_template, send_file # Se agregó send_file
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN ---
API_KEY = "d563e3c8-9270-44f6-bbaf-b328e2c39ed0" #
ROUTE_URL = "https://graphhopper.com/api/1/route?"
GEO_URL = "https://graphhopper.com/api/1/geocode?"
LOG_FILENAME = "route_history.log"

def get_geocoding(location):
    """Obtiene coordenadas y valida la ubicación."""
    if not location:
        return None
    url = GEO_URL + urllib.parse.urlencode({"q": location, "limit": "1", "key": API_KEY})
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("hits"):
                hit = data["hits"][0]
                return {
                    "lat": hit["point"]["lat"],
                    "lng": hit["point"]["lng"],
                    "full_name": f"{hit.get('name', '')}, {hit.get('state', '')}, {hit.get('country', '')}"
                }
    except: return None
    return None

# --- NUEVA RUTA DE DESCARGA ---
@app.route('/download_logs')
def download_logs():
    """Permite descargar el archivo de historial directamente."""
    if os.path.exists(LOG_FILENAME):
        return send_file(LOG_FILENAME, as_attachment=True)
    else:
        return "El archivo de historial aún no ha sido creado.", 404

# --- EL RESTO DEL CÓDIGO SIGUE IGUAL ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_route', methods=['GET'])
def get_route():
    start_loc = request.args.get('start')
    end_loc = request.args.get('end')
    vehicle = request.args.get('vehicle', 'car') #

    origin = get_geocoding(start_loc)
    destination = get_geocoding(end_loc)

    if not origin or not destination:
        return jsonify({"error": "No se pudo localizar la ciudad"}), 404

    points_str = f"&point={origin['lat']},{origin['lng']}&point={destination['lat']},{destination['lng']}" #
    query_params = urllib.parse.urlencode({"key": API_KEY, "vehicle": vehicle, "locale": "es"})
    
    try:
        resp = requests.get(ROUTE_URL + query_params + points_str)
        if resp.status_code == 200:
            path = resp.json()["paths"][0]
            resultado = {
                "origin": origin["full_name"],
                "destination": destination["full_name"],
                "distance_km": round(path["distance"] / 1000, 2),
                "duration": f"{int(path['time'] / 1000 / 60)} min",
                "instructions": [i["text"] for i in path["instructions"]]
            }
            # Guardar en log
            with open(LOG_FILENAME, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": str(datetime.now()), "data": resultado}, ensure_ascii=False) + "\n")
            return jsonify(resultado)
    except: pass
    return jsonify({"error": "Error al calcular ruta"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)