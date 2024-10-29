from mimetypes import guess_extension
import os
from animeflv import AnimeFLV
import PyBypass as bypasser
import random
import requests
import yarl
import asyncio
from aiohttp import ClientResponseError, ClientSession

# Carpeta de descargas
LOCAL_DL = "./downloads"
os.makedirs(LOCAL_DL, exist_ok=True)

MAX_RETRIES = 5  # Número máximo de reintentos

def cursor_arriba(n=1):
    print(f'\33[{n}A', end='')

def get_file_extension(url: str) -> str:
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get("Content-Type", "")
        extension = guess_extension(content_type.split(";")[0].strip())
        return extension if extension else ""
    except requests.RequestException as e:
        print(f"Error obteniendo el Content-Type: {e}")
        return ""

def get_name(url, resp) -> str:
    try:
        filename: str = resp.headers["Content-Disposition"]
        filename = filename.split("filename=")[1].strip().replace('"', "")
    except KeyError:
        filename = yarl.URL(url).name.strip() or str(random.randint(1000000, 9999999999))

    if '.' not in filename.split('/')[-1]:
        extension = get_file_extension(url)
        if extension:
            filename += extension
    return filename

def get_size(resp) -> int:
    try:
        return int(resp.headers.get("Content-Length", 0))
    except (TypeError, ValueError):
        return 0

def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024

async def download_file(url: str, session: ClientSession, progress_callback=None):

    retries = 0
    filename = None
    bypassed = False

    # Bypass si es Streamtape
    if "streamtape.com" in url:
        try:
            bypassed_link, filename = bypasser.bypass(url)
            url = bypassed_link
            bypassed = True
        except Exception as e:
            print(f"Error al aplicar bypass para {url}: {e}")
            return

    while retries < MAX_RETRIES:
        try:
            file_path = os.path.join(LOCAL_DL, filename) if filename else None
            start_byte = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0
            headers = {'Range': f'bytes={start_byte}-'} if start_byte else {}

            async with session.get(url, headers=headers) as resp:
                if resp.status in range(200, 300) or resp.status == 206:
                    if not filename and not bypassed:
                        filename = get_name(url, resp)
                        file_path = os.path.join(LOCAL_DL, filename)

                    size = get_size(resp) + start_byte if start_byte else get_size(resp)
                    cbytes = start_byte

                    with open(file_path, "ab" if start_byte else "wb") as f:
                        async for chunk in resp.content.iter_any():
                            cbytes += len(chunk)
                            f.write(chunk)
                            percent = int(cbytes / size * 100) if size else 0
                            downloaded_size = format_size(cbytes)
                            total_size = format_size(size)

                            if progress_callback:
                                progress_callback(filename, percent, downloaded_size, total_size)

                            print(f"{filename} - {percent}% ({downloaded_size}/{total_size})           ")
                            cursor_arriba()
                        print(f"{filename} descargado.                                                 ")
                    return
                else:
                    print(f"Error en la descarga: código de estado {resp.status}")
        except ClientResponseError as e:
            print(f"Error en la respuesta del servidor: {e}")
        except Exception as e:
            print(f"Error durante la descarga: {e}")

        retries += 1
        print(f"Reintentando descarga ({retries}/{MAX_RETRIES}) para {url}")

    print(f"Descarga fallida después de {MAX_RETRIES} intentos para {url}")

async def download_files(urls, progress_callback=None):
    if isinstance(urls, str):
        urls = [urls]

    async with ClientSession() as session:
        tasks = [download_file(url, session, progress_callback=progress_callback) for url in urls]
        await asyncio.gather(*tasks)


async def main():
    with AnimeFLV() as api:
        elements = api.search(input('Name: '))
        for i, element in enumerate(elements):
            print(f"{i}, {element.title}")
        try:
            selection = int(input('Selecciona: '))
            info = api.get_anime_info(elements[selection].id)
            anime_title = elements[selection].title  # Nombre del anime para el archivo .txt
            info.episodes.reverse()

            all_urls = []  # Lista para guardar todas las URLs de los episodios

            # Recorrer todos los episodios
            for j, episode in enumerate(info.episodes):
                print(f'\nEpisodio {j + 1} | ID del episodio - {episode.id}')
                serie = elements[selection].id
                capitulo = episode.id
                results = api.get_links(serie, capitulo)

                # Filtrar para obtener solo el enlace de Streamtape (o el servidor deseado)
                selected_url = None
                for result in results:
                    if result.server.lower() == 'stape':  # Cambia 'stape' si deseas otro servidor
                        selected_url = result.url
                        break

                if selected_url:
                    all_urls.append(selected_url)  # Agregar la URL a la lista antes de pasarla a la función url_bypasser
                    await download_files(urls=selected_url)
                else:
                    print("Enlace de Streamtape no encontrado para este episodio.")


        except Exception as e:
            print(e)

# Ejecutar el script
asyncio.run(main())
