# CLIP.AI

> AI-powered stream clipping. Watch your favorite streamers and auto-save the best moments as shareable video clips.

**[Live Demo](https://itsKazgar.github.io/clipai)** · **[$CLIP on pump.fun](https://pump.fun/coin/AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump)**

```
 ██████╗██╗     ██╗██████╗      █████╗ ██╗
██╔════╝██║     ██║██╔══██╗    ██╔══██╗██║
██║     ██║     ██║██████╔╝    ███████║██║
██║     ██║     ██║██╔═══╝     ██╔══██║██║
╚██████╗███████╗██║██║         ██║  ██║██║
 ╚═════╝╚══════╝╚═╝╚═╝         ╚═╝  ╚═╝╚═╝
```

---

## What it does

CLIP.AI watches a live stream and automatically clips the best moments — hype plays, funny fails, clutch moments — and saves them as `.mp4` files you can share anywhere.

- **Autopilot** — Claude AI + Whisper listen to audio and chat, score moments 1–10, and clip anything above a threshold automatically
- **Keyword triggers** — type words like `clip that` or `lets go` and it clips the last 60 seconds instantly
- **Manual mode** — full CLI control to clip exact timestamps with custom labels
- **Token gated** — hold 1,000 $CLIP on Solana to unlock (or use `--demo` to try for free)

---

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/download.html) — for extracting clips from the stream buffer
- [streamlink](https://streamlink.github.io/) — for capturing the live stream

Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows — download from https://ffmpeg.org/download.html
```

---

## Install

```bash
git clone https://github.com/itsKazgar/clipai
cd clipai
pip install -r requirements.txt
```

---

## Quick start (no token needed)

```bash
# Try it with --demo — no $CLIP required
python src/clipai.py watch twitch.tv/xqc --autopilot --demo

# With keyword triggers
python src/clipai.py watch twitch.tv/xqc --autopilot --keywords "clip that,lets go" --demo

# With a specific AI prompt
python src/clipai.py watch kick.com/streamer --autopilot --prompt "funny moments and fails" --demo
```

Clips are saved to `./clips/` as `.mp4` files.

---

## Setup (full mode)

**Step 1 — Get an Anthropic API key**

Sign up at [console.anthropic.com](https://console.anthropic.com) and create an API key.

```bash
python src/clipai.py config --api-key YOUR_ANTHROPIC_KEY
```

**Step 2 — Get $CLIP and link your wallet**

Buy $CLIP on [pump.fun](https://pump.fun/coin/AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump) — you need 1,000 to unlock full mode.

```bash
python src/clipai.py config --wallet YOUR_SOLANA_WALLET_ADDRESS
```

**Step 3 — Clip**

```bash
python src/clipai.py watch twitch.tv/streamer --autopilot
```

---

## Usage

### Autopilot mode
AI watches the stream and clips automatically. Best for long sessions where you don't want to babysit it.

```bash
python src/clipai.py watch twitch.tv/streamer --autopilot
python src/clipai.py watch twitch.tv/streamer --autopilot --prompt "clutch plays and insane moments"
python src/clipai.py watch twitch.tv/streamer --autopilot --keywords "clip that,no way,lets go"
```

### Manual mode
You control when to clip. Good for when you're watching along and want specific moments.

```bash
python src/clipai.py watch twitch.tv/streamer --manual
```

Commands inside manual mode:
```
c              → clip last 60 seconds
c 30           → clip last 30 seconds
c 120 180      → clip from 2:00 to 3:00
l clutch play  → label the next clip "clutch play"
q              → quit
```

### Other commands
```bash
# See supported platforms
python src/clipai.py platforms

# Check your config
python src/clipai.py config --show
```

---

## Real-time Whisper transcription (optional)

By default autopilot uses a simulated feed. To enable real audio transcription, install the Whisper dependencies:

```bash
pip install openai-whisper sounddevice
```

Then run without `--demo` — `whisper_module.py` will automatically kick in and transcribe the stream audio in real time, feeding it to Claude for analysis.

> Note: Whisper `base` model runs fine on CPU. Use `small` or `medium` for better accuracy at the cost of speed.

---

## Supported platforms

| Platform | Example URL |
|----------|-------------|
| Twitch | `twitch.tv/streamer` |
| YouTube | `youtube.com/watch?v=...` |
| Kick | `kick.com/streamer` |
| Rumble | `rumble.com/streamer` |
| TikTok Live | `tiktok.com/@streamer/live` |
| PumpFun | `pumpfun.io/streamer` |

Platform support depends on streamlink. Run `streamlink --plugins` to see everything available.

---

## Output

Clips are saved to `./clips/` (or whatever you set with `--output`) as `.mp4` files:

```
clips/
  clip_clutch_play_20250501_143022.mp4
  clip_funny_fail_20250501_143455.mp4
  clip_hype_moment_20250501_144102.mp4
```

---

## $CLIP token

CLIP.AI is token-gated by $CLIP on Solana. Hold 1,000 $CLIP in your wallet to unlock full mode. Balance is verified via Solana RPC on every launch.

Contract: `AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump`

Buy on [pump.fun](https://pump.fun/coin/AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump)

No token? Use `--demo` to try everything for free.

---

## How it works

1. **streamlink** captures the live stream into a rolling `.ts` buffer on disk
2. **Whisper** (optional) transcribes the audio in 15-second chunks
3. **Claude AI** reads the transcript + chat, scores moments, and triggers clips when score ≥ 7
4. **ffmpeg** extracts the relevant segment from the buffer and saves it as `.mp4`
5. You get a folder full of shareable clips

---

## License

MIT — do whatever you want with it.

---

*Built with Claude AI · Whisper · streamlink · ffmpeg · powered by $CLIP*
