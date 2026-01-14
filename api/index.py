from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import os

app = Flask(__name__)

# 1. Configuración de MongoDB
# Recuerda configurar MONGODB_URI en las variables de entorno de Vercel
MONGO_URI = os.environ.get("MONGODB_URI", "TU_CADENA_DE_CONEXION_AQUI")
client = MongoClient(MONGO_URI)
db = client['NombreDeTuBaseDeDatos'] # Cambia por tu nombre de DB
coleccion = db['temperaturas']

# 2. Configuración de Zona Horaria (UTC+1)
tz_utc_plus_1 = timezone(timedelta(hours=1))

@app.route('/api/index', methods=['POST'])
def registrar_temperatura():
    try:
        # Recibir el JSON del ESP32
        datos = request.get_json()
        
        if not datos or 'temperatura' not in datos:
            return jsonify({"error": "Faltan datos de temperatura"}), 400

        temperatura = datos['temperatura']
        ahora_local = datetime.now(tz_utc_plus_1)

        # 3. Crear el documento para la base de datos
        registro = {
            "temperatura": float(temperatura),
            "timestamp": ahora_local,  # Mongo lo guardará como Date (UTC)
            "hora_local": ahora_local.strftime("%Y-%m-%d %H:%M:%S"), # Texto fácil de leer
            "device_ip": request.headers.get('X-Forwarded-For', request.remote_addr)
        }

        # 4. Insertar en MongoDB
        coleccion.insert_one(registro)

        print(f"✅ Dato guardado: {temperatura}°C a las {registro['hora_local']}")
        
        return jsonify({
            "status": "success", 
            "mensaje": "Dato guardado correctamente",
            "hora_registrada": registro['hora_local']
        }), 201

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Ruta opcional para ver que el servidor está vivo
@app.route('/', methods=['GET'])
def home():
    return "Servidor EAQ2 funcionando. Esperando datos del ESP32..."
