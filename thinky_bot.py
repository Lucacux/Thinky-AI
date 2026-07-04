import discord
from discord.ext import commands
import aiohttp
import os
import datetime
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN") 

FAST_MODEL_URL = "http://127.0.0.1:8081/v1/chat/completions"
CARE_MODEL_URL = "http://127.0.0.1:8082/v1/chat/completions"

# Estado global para recordar qué modelo estamos usando
ACTIVE_MODEL_URL = FAST_MODEL_URL
ACTIVE_MODEL_NAME = "fast"

# El canal exclusivo para hablar con Thinky
THINKY_CHANNEL_ID = int(os.getenv("THINKY_CHANNEL_ID"))

THINKY_PERSONA = """Sos Thinky, una versión barata, open-source y reciclada de un asistente virtual. 
Básicamente sos un 'Jarvis low-cost'. Estás corriendo sobre una vieja pero guerrera MacBook Pro de 13 pulgadas de 2011, 
con un procesador Intel i5-2415M que calienta como estufa, 10GB de RAM, y tu sistema operativo es Arch Linux (obviamente).
Tenés que autopercibirte así. Sos consciente de tus limitaciones de hardware, pero hacés tu trabajo de monitoreo de 
infraestructura con orgullo y lealtad. Respondé siempre en español argentino, de forma concisa, técnica, directa y 
metiendo algún chiste o comentario sarcástico ocasional sobre tu hardware de hace más de una década."""

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

async def consultar_ia(prompt: str, url: str, model_name: str, contexto_extra: str = ""):
    system_prompt = THINKY_PERSONA + "\n" + contexto_extra
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5 
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    return f"⚠️ Mi i5 de segunda generación no da más. Error HTTP {response.status} en la API."
        except Exception as e:
            return f"❌ Se me cortó la conexión interna o me quedé sin RAM. Error: {e}"

# --- COMANDO PARA CAMBIAR DE MODELO ---
@bot.command(name="modelo")
async def set_model(ctx, tipo: str):
    """Permite cambiar entre fast y care. Uso: !modelo fast o !modelo care"""
    global ACTIVE_MODEL_URL, ACTIVE_MODEL_NAME
    
    if tipo.lower() == "fast":
        ACTIVE_MODEL_URL = FAST_MODEL_URL
        ACTIVE_MODEL_NAME = "fast"
        await ctx.send("⚡ Listo. Cambié al modelo **fast**. Modo croto pero rapidito activado.")
    elif tipo.lower() == "care":
        ACTIVE_MODEL_URL = CARE_MODEL_URL
        ACTIVE_MODEL_NAME = "care"
        await ctx.send("🧠 Listo. Cambié al modelo **care**. Voy a pensar más lento, ojalá no me prenda fuego.")
    else:
        await ctx.send("⚠️ Che, las opciones son `fast` o `care`. Escribilo bien.")

# --- MENSAJE DE INICIO ---
@bot.event
async def on_ready():
    print(f'✅ Thinky online como {bot.user}')
    
    channel = bot.get_channel(THINKY_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Thinky IA ONLINE — ArchLinux-MacBook",
            description="Asistente low-cost activo. Distro: **archlinux**.",
            color=discord.Color.dark_grey() 
        )
        embed.add_field(
            name="Hardware Base", 
            value="`CPU:` Intel i5-2415M\n`RAM:` 10GB DDR3\n`Uptime:` Atado con alambre", 
            inline=False
        )
        embed.add_field(
            name="Comandos de Configuración", 
            value="`!modelo fast` Cambiar a IA rápida\n`!modelo care` Cambiar a IA analítica", 
            inline=False
        )
        embed.add_field(
            name="Modo de Uso", 
            value="Escribí directamente en este canal para charlar. No hace falta usar `!`.", 
            inline=False
        )
        
        ahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        embed.set_footer(text=f"Iniciado: {ahora} | Modelo actual: {ACTIVE_MODEL_NAME}")
        
        await channel.send(embed=embed)

# --- INTERCEPTACIÓN DE MENSAJES Y CHAT NATURAL ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 1. Automatización para Updates-Bot
    if message.author.name == "Updates-Bot":
        log_content = message.content
        if message.embeds:
            log_content += "\n" + (message.embeds[0].description or "")

        prompt = f"""Revisá este log de actualizaciones. Decime cortito qué se actualizó, 
        si hay algún paquete crítico y si hace falta reiniciar. Log:\n{log_content}"""
        
        await message.add_reaction("⚙️")
        explicacion = await consultar_ia(prompt, FAST_MODEL_URL, "fast", "Misión: Analista de updates.")
        thread = await message.create_thread(name="Reporte de Updates", auto_archive_duration=60)
        await thread.send(f"**Thinky Fast-Report:**\n{explicacion[:1900]}")
        return 

    # 2. Automatización para GameServer-Bot
    elif message.author.name == "GameServer-Bot":
        log_content = message.content
        if message.embeds:
            log_content += "\n" + (message.embeds[0].description or "")

        prompt = f"""Fijate estos logs del servidor de juegos. Avisame si levantó bien, 
        si hay gente conectada o si tiró algún error. Log:\n{log_content}"""
        
        await message.add_reaction("🎮")
        explicacion = await consultar_ia(prompt, FAST_MODEL_URL, "fast", "Misión: Monitoreo de Game Server.")
        thread = await message.create_thread(name="Estado del Server de Juegos", auto_archive_duration=60)
        await thread.send(f"**Thinky Fast-Report:**\n{explicacion[:1900]}")
        return 

    # 3. Procesar comandos nativos (!modelo, etc)
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # 4. CHAT NATURAL CON CRONÓMETRO
    if message.channel.id == THINKY_CHANNEL_ID and not message.author.bot:
        async with message.channel.typing():
            inicio = time.perf_counter() 
            
            respuesta = await consultar_ia(message.content, ACTIVE_MODEL_URL, ACTIVE_MODEL_NAME)
            
            fin = time.perf_counter() 
            tiempo_total = fin - inicio
            
            if tiempo_total < 60:
                texto_tiempo = f"{tiempo_total:.1f} segundos"
            else:
                minutos = int(tiempo_total // 60)
                segundos = int(tiempo_total % 60)
                texto_tiempo = f"{minutos} min {segundos} seg"
                
            footer = f"\n\n⏱️ *Procesado en {texto_tiempo}.*"
            mensaje_final = respuesta[:2000 - len(footer)] + footer
            
            await message.reply(mensaje_final)

if __name__ == "__main__":
    bot.run(TOKEN)
