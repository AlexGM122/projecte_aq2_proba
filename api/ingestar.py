import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# La inicialización de la app de Flask debe ocurrir antes de la conexión a DB.
app = Flask(__name__)

# --- CONFIGURACIÓN DE MONGODB ---

# Vercel inyectará la cadena de conexión desde las Variables de Entorno.
# Esto es esencial para la seguridad y para que funcione 24/7.
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = 'temperatura_db'
COLLECTION_NAME = 'lecturas'

# Conexión Global a MongoDB
# Usar una conexión global (fuera de la función) mejora el rendimiento en Serverless.
try:
    if not MONGO_URI:
        # Esto solo se ejecutaría si no configuraste la variable en Vercel.
        raise ValueError("La variable de entorno MONGO_URI no está configurada.")
        
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Intenta una operación simple para verificar la conexión al inicio (frío start)
    client.admin.command('ping') 
    print("Conexión a MongoDB Atlas inicializada correctamente.")

except (ConnectionFailure, OperationFailure, ValueError) as e:
    print(f"ERROR CRÍTICO: Fallo en la conexión/autenticación de MongoDB: {e}")
    # En un entorno Serverless, una conexión fallida al inicio provocará un fallo de la función.
    # En la práctica, la función Serverless se reiniciará en el siguiente intento.


# --- RUTA PRINCIPAL DE INGESTA DE DATOS ---
# Vercel enruta automáticamente las peticiones POST a la ruta de la carpeta (api/ingestar)
# a esta función.
@app.route('/api/ingestar', methods=['POST'])
def ingestar_temperatura():
    """Recibe la temperatura del ESP32 vía HTTP POST y la guarda en MongoDB Atlas."""
    
    # 1. Obtener datos del cuerpo JSON
    try:
        data = request.json
    except Exception:
        return jsonify({"error": "Formato JSON inválido"}), 400

    if not data or 'temperatura' not in data:
        return jsonify({"error": "Falta el campo 'temperatura' en la petición"}), 400

    temperatura_str = data.get('temperatura')

    # 2. Validación de Datos y Conversión
    try:
        temperatura_float = float(temperatura_str)
    except ValueError:
        return jsonify({"error": f"Valor de temperatura inválido: {temperatura_str}"}), 400

    # 3. Preparar Documento
    registro = {
        "temperatura": temperatura_float,
        "timestamp": datetime.now(timezone.utc),
        "device_ip": request.remote_addr # IP pública del dispositivo/red
    }

    # 4. Guardar en MongoDB Atlas
    try:
        collection.insert_one(registro)
        # El código de estado 201 significa "Creado" (recurso guardado)
        return jsonify({"mensaje": "Datos guardados correctamente", "status": "OK"}), 201
    
    except Exception as e:
        # Captura de errores de inserción o timeout de MongoDB
        print(f"ERROR DE INSERCIÓN: {e}")
        return jsonify({"error": "Fallo al guardar en la base de datos", "details": str(e)}), 500
