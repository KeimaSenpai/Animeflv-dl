import os
import math
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import PyBypass as bypasser

# Importamos la clase AnimeFLV del script original
from modules.animeflv import AnimeFLV  # Asume que el script anterior está en anime_scraper.py

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class AnimeTelegramBot:
    def __init__(self, token):
        self.token = token
        self.anime_client = AnimeFLV()
        self.current_search_results = {}
        self.current_anime_chapters = {}
        self.current_chapter_details = {}

    async def start(self, update: Update, context):
        await update.message.reply_text(
            "¡Bienvenido! Envía el nombre de un anime para buscar. "
            "Ejemplo: /buscar Naruto"
        )

    async def buscar_anime(self, update: Update, context):
        query = ' '.join(context.args) if context.args else update.message.text.replace('/buscar ', '')
        
        if not query:
            await update.message.reply_text("Por favor, ingresa el nombre de un anime para buscar.")
            return

        resultados = self.anime_client.find_anime(query)
        
        if not resultados:
            await update.message.reply_text("No se encontraron animes.")
            return

        # Guardar resultados para referencia posterior
        user_id = update.effective_user.id
        self.current_search_results[user_id] = resultados

        # Crear botones de resultados con paginación
        keyboard = self.create_anime_keyboard(resultados, 0)
        await update.message.reply_text(
            f"Resultados de búsqueda para '{query}' (Página 1):", 
            reply_markup=keyboard
        )

    def create_anime_keyboard(self, resultados, pagina):
        items_por_pagina = 5
        total_paginas = math.ceil(len(resultados) / items_por_pagina)
        
        inicio = pagina * items_por_pagina
        fin = inicio + items_por_pagina
        resultados_pagina = resultados[inicio:fin]

        keyboard = [
            [InlineKeyboardButton(anime['title'], callback_data=f"anime_{anime['id']}")]
            for anime in resultados_pagina
        ]

        # Botones de navegación
        navegacion = []
        if pagina > 0:
            navegacion.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"pagina_{pagina-1}"))
        if pagina < total_paginas - 1:
            navegacion.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"pagina_{pagina+1}"))
        
        if navegacion:
            keyboard.append(navegacion)

        return InlineKeyboardMarkup(keyboard)

    async def callback_handler(self, update: Update, context):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id

        if data.startswith('pagina_'):
            pagina = int(data.split('_')[1])
            keyboard = self.create_anime_keyboard(self.current_search_results[user_id], pagina)
            await query.message.edit_text(
                f"Resultados de búsqueda (Página {pagina + 1}):", 
                reply_markup=keyboard
            )
        
        elif data.startswith('anime_'):
            anime_id = int(data.split('_')[1])
            anime = next(a for a in self.current_search_results[user_id] if a['id'] == anime_id)
            
            try:
                detalles = self.anime_client.anime_details(anime['url'])
                capitulos = detalles['chapters']
                
                # Guardar capítulos para referencia posterior
                self.current_anime_chapters[user_id] = capitulos
                self.current_chapter_details[user_id] = {}

                # Enviar capítulos en grupos de 12
                await self.enviar_capitulos(query.message, capitulos, 0)

            except Exception as e:
                logger.error(f"Error obteniendo detalles del anime: {e}")
                await query.message.reply_text("Hubo un error al obtener los capítulos.")
        
        elif data.startswith('capitulos_'):
            pagina = int(data.split('_')[1])
            capitulos = self.current_anime_chapters[user_id]
            await self.enviar_capitulos(query.message, capitulos, pagina)
        
        elif data.startswith('ver_capitulo_'):
            capitulo_url = data.split('ver_capitulo_')[1]
            
            # Obtener detalles del capítulo si no los tenemos
            if capitulo_url not in self.current_chapter_details[user_id]:
                detalles_capitulo = self.anime_client.chapter_details(capitulo_url)
                self.current_chapter_details[user_id][capitulo_url] = detalles_capitulo
            else:
                detalles_capitulo = self.current_chapter_details[user_id][capitulo_url]
            
            # Generar texto de enlaces
            texto_enlaces = f"📺 Capítulo: {detalles_capitulo['title']}\n\n"
            for source in detalles_capitulo['urls']:
                try:
                    if source['name'] == 'mega':
                        texto_enlaces += f"🔗 MEGA: {source['url']}\n"
                    elif source['name'] == 'yu':
                        texto_enlaces += f"🔗 YourUpload: {source['url']}\n"
                    elif source['name'] == 'stape':
                        try:
                            url_stape_bypassed = bypasser.bypass(source['url'])
                            texto_enlaces += f"🔗 Stape: {url_stape_bypassed}\n"
                        except Exception as e:
                            logger.error(f"Error al bypasear Stape: {e}")
                            texto_enlaces += f"🔗 Stape (Error): {source['url']}\n"
                except Exception as e:
                    logger.error(f"Error procesando enlace: {e}")

            # Crear keyboard solo con botón de volver
            keyboard = [[InlineKeyboardButton("🔙 Volver a Capítulos", callback_data=f"capitulos_0")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                texto_enlaces, 
                reply_markup=reply_markup
            )

    async def enviar_capitulos(self, message, capitulos, pagina):
        capitulos_por_pagina = 12
        total_paginas = math.ceil(len(capitulos) / capitulos_por_pagina)
        
        inicio = pagina * capitulos_por_pagina
        fin = inicio + capitulos_por_pagina
        capitulos_pagina = capitulos[inicio:fin]

        # Crear botones de capítulos con opción de ver enlaces
        keyboard = []
        for i, capitulo in enumerate(capitulos_pagina, 1):
            keyboard.append([
                InlineKeyboardButton(
                    f"Capítulo {inicio + i}", 
                    callback_data=f"ver_capitulo_{capitulo}"
                )
            ])

        # Botones de navegación de capítulos
        navegacion = []
        if pagina > 0:
            navegacion.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"capitulos_{pagina-1}"))
        if pagina < total_paginas - 1:
            navegacion.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"capitulos_{pagina+1}"))
        
        if navegacion:
            keyboard.append(navegacion)

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.edit_text(
            f"Capítulos del Anime (Página {pagina + 1}):\nSelecciona un capítulo para ver sus enlaces.", 
            reply_markup=reply_markup
        )

def main():
    # Reemplaza 'TU_TOKEN_AQUI' con tu token de Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN', '5868896372:AAEDsAJFASvW6JSH0NxiD1pGhH5q1mTc8GM')
    
    # Crear la aplicación
    application = Application.builder().token(token).build()
    
    # Instanciar el bot
    anime_bot = AnimeTelegramBot(token)
    
    # Registrar handlers
    application.add_handler(CommandHandler('start', anime_bot.start))
    application.add_handler(CommandHandler('buscar', anime_bot.buscar_anime))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anime_bot.buscar_anime))
    application.add_handler(CallbackQueryHandler(anime_bot.callback_handler))
    
    # Iniciar el bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()