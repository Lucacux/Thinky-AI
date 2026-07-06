# Thinky-AI — Discord bot con inferencia LLM local (llama.cpp en el host)
FROM python:3.13-slim

RUN useradd -m -u 1000 app
WORKDIR /app
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
USER app

# -u = logs en tiempo real en Dokploy
CMD ["python", "-u", "thinky_bot.py"]
