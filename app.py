# app.py
from fastapi import FastAPI
import threading
import os
# from dotenv import load_dotenv

# Cargar variables de entorno desde .env
# load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bot online v1.0.1"}

def run_bot():
    os.system('python main.py')  # Ejecuta el bot en un proceso separado

@app.on_event("startup")
def startup_event():
    # Ejecuta el bot en un hilo separado cuando la API se inicia
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True  # Daemon para que no bloquee el cierre de la aplicación
    bot_thread.start()
