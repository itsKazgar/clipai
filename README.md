# CLIP.AI v2

> AI-powered stream clipping. Watches live streams, detects hype moments, saves shareable clips automatically.

**[Live Demo](https://itsKazgar.github.io/clipai)** · **[$CLIP on pump.fun](https://pump.fun/coin/AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump)**

---

## Try it right now (no token needed)

```bash
git clone https://github.com/itsKazgar/clipai
cd clipai
pip install -r requirements.txt
python3 demo_live.py xqc --keywords "clip that,lets go"
```

Connects to real Twitch chat instantly. No ffmpeg, no API key, no wallet needed.

---

## What's new in v2

- **Multi-LLM** — Claude, OpenAI, Gemini, Ollama, Hermes3, LLaMA, Mistral
- **Auto vertical crop** — 9:16 for TikTok, Reels, Shorts
- **Whisper subtitles** — burned in with timestamps, 3 styles
- **Basic effects** — fade in/out, intro card
- **One-click export** — YouTube, TikTok, Twitter/X, Discord
- **OBS plugin** — use OBS replay buffer instead of streamlink
- **Live dashboard** — real-time hype meter, chat feed, clip log
- **Community prompts** — shared library of clip prompts, upvoting
- **Clip gallery** — log every session, browse top moments

---

## Requirements

- Python 3.9+
- ffmpeg — for post-processing (optional for demo)
- streamlink — for stream capture (optional if using OBS)

```bash
# Ubuntu / Debian / WSL
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# then
pip install streamlink
```

---

## Install

```bash
git clone https://github.com/itsKazgar/clipai
cd clipai
pip install -r requirements.txt
```

---

## Quick start

```bash
# Demo — real Twitch chat, no token needed
python3 demo_live.py xqc
python3 demo_live.py xqc --keywords "clip that,lets go"
python3 demo_live.py xqc --prompt "funny moments"

# Full autopilot (needs streamlink + ffmpeg)
python3 src/clipai.py watch twitch.tv/xqc --autopilot --demo

# v2 full featured
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --demo
```

---

## Full setup

```bash
# Anthropic API key (Claude)
python3 src/clipai_v2.py config --api-key YOUR_KEY

# Or use a different LLM
python3 src/clipai_v2.py config --llm ollama
python3 src/clipai_v2.py config --llm openai --openai-key YOUR_KEY
python3 src/clipai_v2.py config --llm gemini --gemini-key YOUR_KEY

# Solana wallet for $CLIP token gate
python3 src/clipai_v2.py config --wallet YOUR_WALLET
```

---

## Usage

### Autopilot
```bash
# Basic
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot

# With prompt from library
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --prompt 1

# With keywords
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --keywords "clip that,lets go"

# With post-processing
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --vertical --subtitles --effects

# Export straight to socials
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --export youtube,discord

# Use Ollama locally (no API key needed)
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --llm ollama

# Use OBS replay buffer
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --obs
```

### Manual mode
```bash
python3 src/clipai_v2.py watch twitch.tv/xqc --manual
```### Community
```bash
# Browse prompt library
python3 src/clipai_v2.py prompts

# Open community menu
python3 src/clipai_v2.py community
```

### OBS setup
```bash
python3 src/clipai_v2.py obs-setup
```

---

## Supported platforms

| Platform | Status |
|----------|--------|
| Twitch | ✅ Full support |
| Kick | ✅ Full support |
| YouTube Live | ✅ Full support |
| Rumble | ⚠️ Hit or miss |
| TikTok Live | ⚠️ Hit or miss |
| PumpFun | ❌ Not supported |

---

## Supported LLMs

| Provider | How to use |
|----------|-----------|
| Claude (default) | `--llm claude` + Anthropic API key |
| OpenAI / GPT-4o | `--llm openai` + OpenAI API key |
| Gemini | `--llm gemini` + Gemini API key |
| Ollama (local) | `--llm ollama` — runs on your machine, free |
| Hermes3 | `--llm hermes3` — via Ollama |
| LLaMA | `--llm llama` — via Ollama |
| Mistral | `--llm mistral` — via Ollama |

Run any LLM locally with Ollama: https://ollama.com

---

## Post-processing flags

| Flag | What it does |
|------|-------------|
| `--vertical` | Auto crop to 9:16 for TikTok/Reels/Shorts |
| `--subtitles` | Burn in Whisper subtitles with timestamps |
| `--effects` | Add fade in/out and intro card |
| `--subtitle-style tiktok` | Style: tiktok, minimal, bold |

---

## Social export

```bash
# Discord webhook
python3 src/clipai_v2.py config --discord-webhook YOUR_WEBHOOK_URL

# Then export automatically
python3 src/clipai_v2.py watch twitch.tv/xqc --autopilot --export discord
```

YouTube and TikTok require API approval from their developer portals.

---

## $CLIP token

Hold 1,000 $CLIP on Solana to unlock full mode.
Contract: `AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump`
Buy on [pump.fun](https://pump.fun/coin/AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump)

Use `--demo` to try everything free.

---

## How it works

1. streamlink (or OBS) captures the stream into a rolling buffer
2. Whisper transcribes audio in 15-second chunks
3. Your chosen LLM scores moments and triggers clips at 7+/10
4. ffmpeg cuts the clip and saves as .mp4
5. Post-processing crops, adds subtitles and effects
6. One-click export sends it to your socials

---

MIT · Claude · Whisper · streamlink · ffmpeg · OBS · $CLIP
