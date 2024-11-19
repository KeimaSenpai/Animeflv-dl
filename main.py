import asyncio
import os
import time
import cv2
from pyrogram import Client, filters
from modules.animeflv import AnimeFLV
from modules.download import download_files

# Configuración del bot de Telegram
api_id = '11029886'
api_hash = '4e74899bfd41879c6a4b48cf6a07f456'
# bot_token = '5868896372:AAGqKjVCQmr0YFwa6sv-8qjjVvPUBq_UST4'
bot_token = '5998213610:AAHUfeee08ryYWrRhLJ0yI8SL8F0RQu0wKs'

# Ruta de la carpeta de descargas
DOWNLOAD_FOLDER = "./downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# Crear instancia del cliente de Pyrogram
app = Client("uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Diccionario para almacenar el contexto de búsqueda de cada usuario
user_search_context = {}

# Función para extraer una miniatura del video usando OpenCV
def extract_thumbnail_opencv(video_path, output_path, time=50):
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(fps * time)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = cap.read()
        if success:
            cv2.imwrite(output_path, frame)
            return output_path
        cap.release()
    except Exception as e:
        print(f"Error extrayendo thumbnail de {video_path}: {e}")
    return None

def get_video_metadata(video_path):
    """Obtiene la duración, ancho y alto del video usando OpenCV."""
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Obtener ancho y alto
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Obtener FPS y número total de frames para calcular la duración
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = int(total_frames / fps) if fps > 0 else 0
        
        cap.release()
        return {
            "duration": duration,
            "width": width,
            "height": height
        }
    except Exception as e:
        print(f"Error obteniendo metadata del video {video_path}: {e}")
        return None


# Comando /start
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("¡Hola! Soy tu bot de anime. Usa el comando /download para buscar un anime.\n\nv1.0")

# Comando /search
@app.on_message(filters.command("search"))
async def download(client, message):
    await message.reply("Por favor, envíame el nombre del anime que deseas buscar.")
    user_search_context[message.from_user.id] = {"stage": "waiting_for_anime_name"}

# Comando /up para iniciar el proceso de descarga y subida
@app.on_message(filters.command("up"))
async def upload_video(client, message):
    await message.reply("Por favor, envíame la URL del episodio que deseas descargar y subir.")
    user_search_context[message.from_user.id] = {"stage": "waiting_for_upload"}


# Funciones de utilidad para el formato
def format_size(size):
    """Convierte bytes a formato legible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f}{unit}"
        size /= 1024.0
    return f"{size:.2f}TB"

def format_time(seconds):
    """Convierte segundos a formato legible."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.0f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

# Función de callback para actualizar el progreso de descarga
async def download_progress_callback(client, message_id, chat_id, filename, current, total, start_time):
    try:
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        if total == 0:
            percentage = 0
        else:
            percentage = (current * 100) / total
        
        # Calcular velocidad y tiempo estimado
        speed = current / elapsed_time if elapsed_time > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0
        
        # Crear barra de progreso
        bar_length = 10
        filled_length = int(percentage * bar_length / 100)
        bar = '◆' * filled_length + '◇' * (bar_length - filled_length)
        
        # Formatear tamaños
        current_size = format_size(current)
        total_size = format_size(total)
        speed_str = format_size(speed) + "/s"
        
        text = (
            f"📥 Descargando archivo\n\n"
            f"🔖 Nombre: {filename}\n"
            f"┌ Progreso: {percentage:.1f}%\n"
            f"├ [{bar}]\n"
            f"├ {current_size} / {total_size}\n"
            f"├ Velocidad: {speed_str}\n"
            f"└ Tiempo restante: {format_time(eta)}"
        )
        time.sleep(2)
        await client.edit_message_text(chat_id, message_id, text)
    except Exception as e:
        print(f"Error en progress_callback: {e}")

# Función de callback para actualizar el progreso de subida
async def upload_progress_callback(client, message_id, chat_id, filename, current, total, start_time):
    try:
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        if total == 0:
            percentage = 0
        else:
            percentage = (current * 100) / total
        
        # Calcular velocidad y tiempo estimado
        speed = current / elapsed_time if elapsed_time > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0
        
        # Crear barra de progreso
        bar_length = 10
        filled_length = int(percentage * bar_length / 100)
        bar = '◆' * filled_length + '◇' * (bar_length - filled_length)
        
        # Formatear tamaños
        current_size = format_size(current)
        total_size = format_size(total)
        speed_str = format_size(speed) + "/s"
        
        text = (
            f"📤 Subiendo a Telegram\n\n"
            f"🔖 Nombre: {filename}\n"
            f"┌ Progreso: {percentage:.1f}%\n"
            f"├ [{bar}]\n"
            f"├ {current_size} / {total_size}\n"
            f"├ Velocidad: {speed_str}\n"
            f"└ Tiempo restante: {format_time(eta)}"
        )
        time.sleep(2)
        await client.edit_message_text(chat_id, message_id, text)
    except Exception as e:
        print(f"Error en progress_callback: {e}")

# Manejo de mensajes de texto
@app.on_message(filters.text & filters.incoming)
async def handle_text_message(client, message):
    user_id = message.from_user.id

    # Manejo de búsqueda de anime
    if user_id in user_search_context and user_search_context[user_id]["stage"] == "waiting_for_anime_name":
        anime_name = message.text
        api = AnimeFLV()
        elements = api.find_anime(anime_name)
        
        if elements:
            user_search_context[user_id] = {"stage": "waiting_for_selection", "results": elements}
            result_message = "Resultados de búsqueda:\n\n" + "\n".join(
                f"{i + 1}. {element['title']}" for i, element in enumerate(elements)
            )
            await message.reply(result_message + "\n\nPor favor, responde con el número del anime que deseas ver los enlaces.")
        else:
            await message.reply("No se encontraron resultados para ese nombre. Inténtalo con otro nombre.")

    # Manejo de selección de anime
    elif user_id in user_search_context and user_search_context[user_id]["stage"] == "waiting_for_selection":
        try:
            selection_index = int(message.text) - 1
            elements = user_search_context[user_id]["results"]
            if 0 <= selection_index < len(elements):
                selected_anime = elements[selection_index]
                api = AnimeFLV()
                anime_details = api.anime_details(selected_anime['url'])
                
                all_urls = []
                for episode_url in anime_details['chapters']:
                    episode_details = api.chapter_details(episode_url)
                    selected_url = next(
                        (video['url'] for video in episode_details['urls'] if video['name'].lower() == 'stape'), 
                        None
                    )
                    if selected_url:
                        all_urls.append(f"Episodio {episode_details['title']}: {selected_url}")

                if all_urls:
                    for bloque in dividir_en_bloques(all_urls, 25):
                        await message.reply("\n".join(bloque))
                    await message.reply(
                        "Para descargar algún episodio, usa el comando /up y envía el enlace del episodio que desees."
                    )
                else:
                    await message.reply("No se encontraron enlaces de Streamtape para los episodios.")
                del user_search_context[user_id]
            else:
                await message.reply("Selección inválida. Por favor, envía el número correcto.")
        except ValueError:
            await message.reply("Por favor, envía un número válido.")
        except Exception as e:
            await message.reply(f"Ocurrió un error: {str(e)}")

    # Manejo de subida de video
    elif user_id in user_search_context and user_search_context[user_id]["stage"] == "waiting_for_upload":
        url = message.text
        progress_message = await message.reply("Iniciando la descarga del video...")
        start_time = time.time()

        try:
            # Callback para la descarga
            async def download_progress(filename, current, total, start_time):
                await download_progress_callback(
                    client, 
                    progress_message.id,
                    message.chat.id,
                    filename,
                    current,
                    total,
                    start_time
                )

            # Descargar el archivo
            downloaded_files = await download_files([url], progress_callback=download_progress)
            
            if not downloaded_files:
                await message.reply("❌ Error: No se pudo completar la descarga.")
                return

            for file_path in downloaded_files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    
                    # Preparar la miniatura
                    thumbnail_path = os.path.join(DOWNLOAD_FOLDER, f"{os.path.splitext(filename)[0]}_thumb.jpg")
                    extract_thumbnail_opencv(file_path, thumbnail_path)
                    
                    # Obtener metadata
                    video_metadata = get_video_metadata(file_path)
                    
                    # Mensaje de progreso para la subida
                    upload_progress_msg = await message.reply("Preparando la subida a Telegram...")
                    upload_start_time = time.time()

                    try:
                        # Subir el archivo con progreso
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=file_path,
                            thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
                            duration=video_metadata.get("duration") if video_metadata else None,
                            width=video_metadata.get("width") if video_metadata else None,
                            height=video_metadata.get("height") if video_metadata else None,
                            caption=f"✅ {filename}",
                            progress=lambda current, total: asyncio.run(upload_progress_callback(
                                client,
                                upload_progress_msg.id,
                                message.chat.id,
                                filename,
                                current,
                                total,
                                upload_start_time
                            ))
                        )
                        # await message.reply(f"✅ Archivo subido exitosamente: {filename}")
                    
                    except Exception as e:
                        await message.reply(f"❌ Error al subir {filename}: {str(e)}")
                    
                    finally:
                        # Limpieza de archivos
                        try:
                            os.remove(file_path)
                            if os.path.exists(thumbnail_path):
                                os.remove(thumbnail_path)
                        except Exception as e:
                            print(f"Error al eliminar archivos temporales: {e}")

            await message.reply("✅ Proceso completado")
            del user_search_context[user_id]

        except Exception as e:
            await message.reply(f"❌ Error durante el proceso: {str(e)}")

# Función para dividir la lista en bloques de tamaño específico
def dividir_en_bloques(lista, n):
    for i in range(0, len(lista), n):
        yield lista[i:i + n]

# Iniciar el bot
if __name__ == "__main__":
    print('Bot Iniciado')
    app.run()
