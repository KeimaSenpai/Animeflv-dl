import asyncio
import os
import time
import PyBypass as bypasser
from aiohttp import ClientResponseError, ClientSession
# from megaAPI import Mega

LOCAL_DL = "./downloads"
MAX_RETRIES = 5

def get_size(resp) -> int:
    try:
        return int(resp.headers.get("Content-Length", 0))
    except (TypeError, ValueError):
        return 0


async def download_file(url: str, session: ClientSession, progress_callback=None):
    """
    Descarga un archivo desde una URL y muestra el progreso.
    
    Args:
        url (str): URL del archivo a descargar
        session (ClientSession): Sesión aiohttp
        progress_callback (callable): Función de callback para actualizar el progreso
    """
    if "streamtape.com" in url:
        try:
            bypassed_link, filename = bypasser.bypass(url)
        except Exception as e:
            print(f"Error al procesar la URL con PyBypass: {e}")
            return None
    else:
        bypassed_link = url
        # Obtiene el nombre del archivo de la URL y limpia los parámetros
        filename = url.split('/')[-1].split('?')[0]

    retries = 0
    start_time = time.time()
    
    while retries < MAX_RETRIES:
        try:
            file_path = os.path.join(LOCAL_DL, filename)
            start_byte = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            headers = {'Range': f'bytes={start_byte}-'} if start_byte else {}

            async with session.get(bypassed_link, headers=headers) as resp:
                if resp.status in range(200, 300) or resp.status == 206:
                    total_size = get_size(resp) + start_byte if start_byte else get_size(resp)
                    downloaded_size = start_byte

                    with open(file_path, "ab" if start_byte else "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):  # Usar chunks de 8KB
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)

                                # Llamar al callback de progreso si está disponible
                                if progress_callback:
                                    try:
                                        await progress_callback(
                                            filename=filename,
                                            current=downloaded_size,
                                            total=total_size,
                                            start_time=start_time
                                        )
                                    except Exception as e:
                                        print(f"Error en callback de progreso: {e}")

                    print(f"\n{filename} descargado exitosamente.")
                    return file_path
                else:
                    print(f"Error en la descarga: código de estado {resp.status}")
                    
        except asyncio.CancelledError:
            print("Descarga cancelada")
            raise
        except ClientResponseError as e:
            print(f"Error en la respuesta del servidor: {e}")
        except Exception as e:
            print(f"Error durante la descarga: {e}")

        retries += 1
        if retries < MAX_RETRIES:
            print(f"Reintentando descarga ({retries}/{MAX_RETRIES}) para {url}")
            await asyncio.sleep(2 ** retries)  # Espera exponencial entre reintentos
    
    print(f"Descarga fallida después de {MAX_RETRIES} intentos para {url}")
    return None

# ------------------------------------------------------------

async def download_files(urls, progress_callback=None):
    """
    Descarga múltiples archivos mostrando el progreso.
    
    Args:
        urls (str or list): URL o lista de URLs para descargar
        progress_callback (callable): Función de callback para actualizar el progreso
    """
    if isinstance(urls, str):
        urls = [urls]

    if not os.path.exists(LOCAL_DL):
        os.makedirs(LOCAL_DL, exist_ok=True)

    async with ClientSession() as session:
        tasks = []
        for url in urls:
            task = asyncio.create_task(
                download_file(url, session, progress_callback=progress_callback)
            )
            tasks.append(task)
        
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error en tarea de descarga: {e}")
        
        return results