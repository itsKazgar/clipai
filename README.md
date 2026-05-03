> 🔗 **[Live Demo](https://itsKazgar.github.io/clipai)** | **[$CLIP on PumpFun](https://pump.fun/coin/AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump)**

# CLIP.AI
AI-powered stream clipping tool. Token gated by $CLIP on Solana.

## Install
```bash
git clone https://github.com/YOUR_GITHUB/clipai && cd clipai
pip install -r requirements.txt
```

## Usage
```bash
# autopilot
python src/clipai.py watch twitch.tv/streamer --autopilot --demo

# keyword triggers
python src/clipai.py watch kick.com/streamer --autopilot --keywords "clip that,lets go"

# manual mode
python src/clipai.py watch twitch.tv/streamer --manual
```

## Token Gate
Hold 1000 $CLIP on Solana to unlock.
```bash
python src/clipai.py config --wallet YOUR_WALLET
python src/clipai.py config --api-key YOUR_ANTHROPIC_KEY
```

## Platforms
Twitch · YouTube · Kick · PumpFun · Rumble · TikTok Live

## License
MIT
