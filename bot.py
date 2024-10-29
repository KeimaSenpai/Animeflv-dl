import os
from pyrogram import Client
from mimetypes import guess_type

# Configuración del bot de Telegram
api_id = '11029886'
api_hash = '4e74899bfd41879c6a4b48cf6a07f456'
bot_token = '6184630791:AAEmzSRImou2w8IaSDGqu4EDSBiSWXcgqME'

# Ruta de la carpeta de descargas
DOWNLOAD_FOLDER = "./downloads"

# ID del chat donde se enviarán los videos
CHAT_ID = '1618347551'  # Puede ser el ID de un grupo, canal o usuario


def is_video_file(filename):
    # Verifica si el archivo es un video
    mime_type, _ = guess_type(filename)
    return mime_type and mime_type.startswith("video")

# Crear instancia del cliente de Pyrogram
app = Client("uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Función de progreso con actualización en Telegram
async def progress(current, total, message):
    percent = (current / total) * 100
    await message.edit_text(f"Progreso de subida: {percent:.2f}%")

# Función para subir videos de la carpeta `downloads`
async def upload_videos():
    # Obtener lista de archivos en la carpeta
    files = [f for f in os.listdir(DOWNLOAD_FOLDER) if os.path.isfile(os.path.join(DOWNLOAD_FOLDER, f))]

    # Subir cada archivo si es de video
    for file in files:
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        if is_video_file(file_path):
            try:
                print(f"Subiendo {file} a Telegram...")
                # Enviar un mensaje de progreso inicial
                progress_message = await app.send_message(CHAT_ID, f"Iniciando subida de {file}...")

                # Subir el video y actualizar el mensaje de progreso
                await app.send_video(
                    CHAT_ID,
                    video=file_path,
                    caption=f"Subido automáticamente: {file}",
                    progress=progress,  # Pasar la función de progreso
                    progress_args=(progress_message,)  # Pasar el mensaje de progreso para editar
                )
                await progress_message.edit_text(f"{file} subido con éxito.")
                print(f"{file} subido con éxito.")
            except Exception as e:
                print(f"Error al subir {file}: {e}")

# Iniciar el bot y subir videos automáticamente al conectarse
@app.on_message()
async def start_upload(client, message):
    # Esperar hasta que el bot esté en línea y luego subir los videos
    await upload_videos()

if __name__ == "__main__":
    app.run()