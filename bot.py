import os
import random
import asyncio
from animeflv import AnimeFLV
import PyBypass as bypasser
import requests
from mimetypes import guess_extension
from yarl import URL
from aiohttp import ClientSession, ClientResponseError
from pyrogram import Client, filters

# Configuración de Pyrogram
api_id = '11029886'
api_hash = '4e74899bfd41879c6a4b48cf6a07f456'
bot_token = '6184630791:AAEmzSRImou2w8IaSDGqu4EDSBiSWXcgqME'

app = Client("anime_downloader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Configuración de descargas
DOWNLOAD_FOLDER = "./downloads"
MAX_RETRIES = 5
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Obtener extensión del archivo
def get_file_extension(url: str) -> str:
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get("Content-Type", "")
        return guess_extension(content_type.split(";")[0].strip()) or ""
    except requests.RequestException as e:
        print(f"Error obteniendo el Content-Type: {e}")
        return ""

# Función para descargar un solo archivo
async def download_file(url: str, session: ClientSession, file_path: str):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_any():
                            f.write(chunk)
                    print(f"{file_path} descargado.")
                    return file_path
                else:
                    print(f"Error en descarga: código de estado {resp.status}")
        except ClientResponseError as e:
            print(f"Error en respuesta del servidor: {e}")
        except Exception as e:
            print(f"Error en descarga: {e}")

        retries += 1
        print(f"Reintentando descarga ({retries}/{MAX_RETRIES}) para {url}")
    print(f"Descarga fallida después de {MAX_RETRIES} intentos para {url}")
    return None

# Función para descargar múltiples episodios
async def download_episodes(bypassed_urls):
    downloaded_files = []
    async with ClientSession() as session:
        tasks = []
        for url, filename in bypassed_urls:
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            tasks.append(download_file(url, session, file_path))
        downloaded_files = await asyncio.gather(*tasks)
    return [file for file in downloaded_files if file]

# Obtener enlaces de descarga de la serie y pasarlos por el bypass
async def get_bypassed_links(series_name):
    with AnimeFLV() as api:
        elements = api.search(series_name)
        if not elements:
            return None, None
        info = api.get_anime_info(elements[0].id)
        bypassed_links = []

        for episode in info.episodes:
            links = api.get_links(elements[0].id, episode.id)
            for link in links:
                if link.server.lower() == "stape":
                    try:
                        # Aplicar bypass para obtener el enlace final y el nombre de archivo
                        bypassed_url, filename = bypasser.bypass(link.url)
                        bypassed_links.append((bypassed_url, filename))
                    except Exception as e:
                        print(f"Error en bypass de {link.url}: {e}")
                    break
        return bypassed_links, elements[0].title

# Comando del bot para descargar una serie
@app.on_message(filters.command("download"))
async def download_series(client, message):
    series_name = message.text.split(" ", 1)[-1]
    await message.reply(f"Buscando y descargando la serie: {series_name}")

    # Obtener enlaces de descarga con bypass aplicado
    bypassed_links, title = await get_bypassed_links(series_name)
    if not bypassed_links:
        await message.reply("No se encontraron episodios para esta serie.")
        return

    # Descargar todos los episodios
    await message.reply(f"Iniciando descarga de {len(bypassed_links)} episodios de {title}")
    downloaded_files = await download_episodes(bypassed_links)

    # Subir todos los archivos a Telegram
    if downloaded_files:
        await message.reply(f"Subiendo {len(downloaded_files)} episodios de {title} a Telegram.")
        for file_path in downloaded_files:
            try:
                await client.send_video(message.chat.id, video=file_path, caption=f"{title}")
            except Exception as e:
                await message.reply(f"Error al subir {file_path}: {e}")
    else:
        await message.reply("Ocurrió un problema en la descarga de los episodios.")

    # Limpiar archivos descargados
    for file in downloaded_files:
        os.remove(file)

# Ejecutar el bot
if __name__ == "__main__":
    app.run()