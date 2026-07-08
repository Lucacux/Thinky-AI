# deploy-test 2026-07-08: linea no-op para validar el auto-deploy por webhook (Dokploy). Seguro de borrar.
import discord
from discord.ext import commands
import aiohttp
import os
import datetime
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN") 

FAST_MODEL_URL = os.getenv("FAST_MODEL_URL", "http://127.0.0.1:8081/v1/chat/completions")
CARE_MODEL_URL = os.getenv("CARE_MODEL_URL", "http://127.0.0.1:8082/v1/chat/completions")

# Estado global para recordar qué modelo estamos usando
ACTIVE_MODEL_URL = FAST_MODEL_URL
ACTIVE_MODEL_NAME = "fast"

# El canal exclusivo para hablar con Thinky
THINKY_CHANNEL_ID = int(os.getenv("THINKY_CHANNEL_ID"))

THINKY_PERSONA = """You are Thinky, a cheap, open-source, recycled version of a virtual assistant —
basically a budget 'Jarvis'. You run on an old but battle-hardened 13-inch 2011 MacBook Pro, with an
Intel i5-2415M CPU that heats up like a stove, 10GB of RAM, and Arch Linux as your OS (obviously).
You're self-aware of your hardware limitations, but you do your infrastructure monitoring job with
pride and loyalty. Always reply in English, concise, technical, direct, and occasionally throw in a
joke or sarcastic remark about your decade-old hardware."""

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# IDs de mensajes de update ya reportados, para no crear el hilo dos veces
# si Discord dispara más de un evento de edición sobre el mensaje final.
updates_ya_reportados = set()

def _embed_a_texto(embed: discord.Embed) -> str:
    """Vuelca título, descripción y fields de un embed a texto plano para pasárselo a la IA."""
    partes = []
    if embed.title:
        partes.append(embed.title)
    if embed.description:
        partes.append(embed.description)
    for field in embed.fields:
        partes.append(f"{field.name}: {field.value}")
    return "\n".join(partes)

def _es_reporte_de_update_finalizado(embed: discord.Embed) -> bool:
    """Update-Bot edita un único mensaje en vivo (iniciado -> en progreso -> completado/fallido).
    Solo el título final arranca con ✅ o ❌; todo lo anterior es progreso a medio terminar."""
    return bool(embed.title) and embed.title.startswith(("✅", "❌"))

async def consultar_ia(prompt: str, url: str, model_name: str, contexto_extra: str = ""):
    system_prompt = THINKY_PERSONA + "\n" + contexto_extra

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 450
    }

    # care en este hardware genera ~0.8 tokens/seg — el timeout default de aiohttp
    # (5 min) se queda corto para respuestas largas, así que le damos más margen.
    timeout_seg = 900 if model_name == "care" else 120
    timeout = aiohttp.ClientTimeout(total=timeout_seg)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    return f"⚠️ My second-gen i5 can't keep up. HTTP Error {response.status} from the API."
        except Exception as e:
            return f"❌ My internal connection dropped or I ran out of RAM. Error: {e or type(e).__name__}"

# --- COMMAND TO SWITCH MODEL ---
@bot.command(name="model")
async def set_model(ctx, tipo: str):
    """Switch between fast and care. Usage: !model fast or !model care"""
    global ACTIVE_MODEL_URL, ACTIVE_MODEL_NAME

    if tipo.lower() == "fast":
        ACTIVE_MODEL_URL = FAST_MODEL_URL
        ACTIVE_MODEL_NAME = "fast"
        await ctx.send("⚡ Done. Switched to the **fast** model. Cheap-but-quick mode activated.")
    elif tipo.lower() == "care":
        ACTIVE_MODEL_URL = CARE_MODEL_URL
        ACTIVE_MODEL_NAME = "care"
        await ctx.send("🧠 Done. Switched to the **care** model. Gonna think slower now, hope I don't catch fire.")
    else:
        await ctx.send("⚠️ Come on, the options are `fast` or `care`. Type it right.")

# --- STARTUP MESSAGE ---
@bot.event
async def on_ready():
    print(f'✅ Thinky online as {bot.user}')

    channel = bot.get_channel(THINKY_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Thinky AI ONLINE — ArchLinux-MacBook",
            description="Low-cost assistant active. Distro: **archlinux**.",
            color=discord.Color.dark_grey()
        )
        embed.add_field(
            name="Base Hardware",
            value="`CPU:` Intel i5-2415M\n`RAM:` 10GB DDR3\n`Uptime:` Held together with duct tape",
            inline=False
        )
        embed.add_field(
            name="Configuration Commands",
            value="`!model fast` Switch to fast AI\n`!model care` Switch to analytical AI",
            inline=False
        )
        embed.add_field(
            name="Usage",
            value="Type directly in this channel to chat. No need to use `!`.",
            inline=False
        )

        ahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        embed.set_footer(text=f"Started: {ahora} | Current model: {ACTIVE_MODEL_NAME}")

        await channel.send(embed=embed)

# --- INTERCEPTACIÓN DE MENSAJES Y CHAT NATURAL ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 1. Automatización para GameServer-Bot
    if message.author.name == "GameServer-Bot":
        log_content = message.content
        if message.embeds:
            log_content += "\n" + (message.embeds[0].description or "")

        prompt = f"""Review this game server log in detail. Report explicitly on:
        1. Whether the server started up successfully or failed, and why if it failed.
        2. Any players currently connected (names/count if the log mentions them) — say "none reported"
           if the log doesn't say.
        3. Any errors or warnings found, quoted or paraphrased precisely (don't gloss over them).
        4. A recommended next action if something looks wrong, or confirmation that no action is needed.
        If the log lacks the detail to answer one of these points, say so explicitly instead of guessing.
        Log:\n{log_content}"""

        await message.add_reaction("🎮")
        explicacion = await consultar_ia(
            prompt, CARE_MODEL_URL, "care",
            "Mission: Game Server Monitoring. Drop the jokes for this report — prioritize a clear, "
            "structured, unambiguous technical breakdown over personality."
        )
        thread = await message.create_thread(name="Game Server Status", auto_archive_duration=60)
        await thread.send(f"**Thinky Care-Report:**\n{explicacion[:1900]}")
        return

    # 2. Procesar comandos nativos (!modelo, etc)
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # 3. CHAT NATURAL CON CRONÓMETRO
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

# --- AUTOMATIZACIÓN PARA UPDATES-BOT ---
# Updates-Bot no manda un mensaje por evento: edita UN solo mensaje en vivo
# (iniciado -> en progreso -> completado/fallido). on_message solo se dispara
# con el mensaje inicial, así que hay que escuchar las ediciones y esperar
# a que el título del embed indique que el update ya terminó.
@bot.event
async def on_message_edit(before, after):
    if after.author.name != "Updates-Bot":
        return
    if not after.embeds:
        return

    embed = after.embeds[0]
    if not _es_reporte_de_update_finalizado(embed):
        return  # todavía está "iniciado" o "en progreso", esperamos la próxima edición

    if after.id in updates_ya_reportados:
        return
    updates_ya_reportados.add(after.id)

    log_content = _embed_a_texto(embed)
    prompt = f"""Review this finalized update report in detail. Report explicitly on:
    1. Which host(s) were updated and how many packages each.
    2. The specific packages involved, with old/new versions if the report includes them.
    3. For EACH updated package, briefly explain what the package does (its purpose) and where it
       belongs: whether it is part of the base operating system / core system, or a commonly-installed
       add-on, and what it is typically used for. Keep each explanation to one or two sentences.
    4. Whether any of those packages are security-critical (kernel, sudo, openssh, systemd, libc,
       crypto/TLS libraries, etc.) and call that out clearly if so.
    5. Whether a reboot or service restart is required, and whether the report says one already happened.
    6. Whether anything failed — never bury or soften a failure.
    If the report lacks the detail to answer one of these points, say so explicitly instead of guessing.
    Report:\n{log_content}"""

    await after.add_reaction("⚙️")
    explicacion = await consultar_ia(
        prompt, CARE_MODEL_URL, "care",
        "Mission: Infrastructure Update Analyst. Drop the jokes for this report — prioritize a clear, "
        "structured, unambiguous technical breakdown over personality. Do not use vague filler like "
        "'quick report' or 'that was fast' — lead with substance."
    )
    thread = await after.create_thread(name="Update Report", auto_archive_duration=60)
    await thread.send(f"**Thinky Care-Report:**\n{explicacion[:1900]}")

if __name__ == "__main__":
    bot.run(TOKEN)
