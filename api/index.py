import os
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

app = Flask(__name__)

# --- CONFIGURACIÓN DE MONGODB ---
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = 'temperatura_db'
COLLECTION_NAME = 'lecturas'

try:
    if not MONGO_URI:
        raise ValueError("La variable de entorno MONGO_URI no está configurada.")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    client.admin.command('ping') 
    print("Conexión a MongoDB Atlas inicializada correctamente.")
except Exception as e:
    print(f"ERROR CRÍTICO: {e}")

# --- RUTA PARA SENSOR (POST) Y GRAFANA (GET) ---
@app.route('/api/index', methods=['POST', 'GET']) # <-- AHORA ACEPTA AMBOS
def manejar_temperatura():
    
    # 1. SI ES GET: Devolvemos datos a Grafana
    if request.method == 'GET':
        try:
            # Buscamos las últimas 100 lecturas, de más reciente a más antigua
            # Eliminamos el campo '_id' porque da problemas con JSON
            registros = list(collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(100))
            return jsonify(registres), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # 2. SI ES POST: Recibimos datos del ESP32 (Tu código original)
    if request.method == 'POST':
        try:
            data = request.json
            if not data or 'temperatura' not in data:
                return jsonify({"error": "Falta temperatura"}), 400
            
            temperatura_float = float(data.get('temperatura'))
            tz_utc_plus_1 = timezone(timedelta(hours=1))
            
            registro = {
                "temperatura": temperatura_float,
                "timestamp": datetime.now(tz_utc_plus_1),
                "device_ip": request.remote_addr
            }
            
            collection.insert_one(registro)
            return jsonify({"mensaje": "OK"}), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
