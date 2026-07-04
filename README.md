# 🧠 Thinky-AI

![Thinky-AI Banner](./assets/banner.png)

An AI-powered Discord assistant and infrastructure report aggregator, running local LLM inference on legacy hardware.

## ✨ Key Features

- **AI chat companion:** talk directly in a dedicated channel, with hot-swappable models (`!modelo fast` for quick replies, `!modelo care` for more analytical ones).
- **Automated report aggregation:** listens for messages from other infrastructure bots (`Updates-Bot`, `GameServer-Bot`) and summarizes their logs into a readable thread using the local LLM.
- **Runs entirely on local inference:** no external AI API calls — talks to a local OpenAI-compatible `llama.cpp` server over HTTP.

## 🧰 Stack

- Python
- discord.py
- aiohttp (calls a local `llama.cpp` server's OpenAI-compatible `/v1/chat/completions` endpoint)

## 🚀 Installation

```bash
git clone https://github.com/Lucacux/Thinky-AI.git
cd Thinky-AI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your real values
python thinky_bot.py
```

**Note:** this bot expects one or two `llama.cpp` server instances (OpenAI-compatible `/v1/chat/completions` endpoint) already running locally — by default on `http://127.0.0.1:8081` (fast model) and `http://127.0.0.1:8082` (care model). It does not start or manage those servers itself.

## ⚙️ Environment Variables

See `.env.example` — bot token and the Discord channel where Thinky listens for natural chat.

## 📄 License

Personal infrastructure project — free to use as reference.
