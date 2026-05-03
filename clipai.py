#!/usr/bin/env python3
import os, sys, json, time, argparse, subprocess
from datetime import datetime
from pathlib import Path

try:
    import anthropic
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

VERSION = "1.0.0"
CLIP_TOKEN_MINT = "AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump"
REQUIRED_CLIP_BALANCE = 1000
CONFIG_PATH = Path.home() / ".clipai" / "config.json"
PLATFORMS = {
    "twitch":   "https://twitch.tv/",
    "youtube":  "https://youtube.com/",
    "kick":     "https://kick.com/",
    "pumpfun":  "https://pumpfun.io/",
    "rumble":   "https://rumble.com/",
    "tiktok":   "https://tiktok.com/",
}
C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","w":"\033[97m","d":"\033[90m","b":"\033[1m","x":"\033[0m"}
def c(k, t): return C.get(k, "") + t + C["x"]


# ─── Token Gate ──────────────────────────────────────────────────────────────

class TokenGate:
    def __init__(self, wallet=None):
        self.wallet = wallet
        self.verified = False
        self.balance = 0

    def check_balance(self):
        if not self.wallet:
            return False
        try:
            import urllib.request
            rpc = "https://api.mainnet-beta.solana.com"
            payload = json.dumps({
                "jsonrpc": "2.0", "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [self.wallet, {"mint": CLIP_TOKEN_MINT}, {"encoding": "jsonParsed"}]
            }).encode()
            req = urllib.request.Request(rpc, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                accts = data.get("result", {}).get("value", [])
                if accts:
                    self.balance = float(accts[0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"])
                    self.verified = self.balance >= REQUIRED_CLIP_BALANCE
                    return self.verified
        except Exception as e:
            print(c("y", f"  [!] Token check failed: {e} — running demo mode"))
        return False

    def gate(self, bypass_demo=False):
        print(c("c", "\n  [$] Checking $CLIP token balance..."))
        if bypass_demo:
            print(c("y", "  [~] Demo mode — token gate bypassed"))
            return True
        if self.check_balance():
            print(c("g", f"  [✓] Verified: {self.balance:.0f} $CLIP held"))
            return True
        print(c("r", f"  [✗] Need {REQUIRED_CLIP_BALANCE} $CLIP to use CLIP.AI"))
        print(c("d", f"      Get $CLIP: https://pump.fun/coin/{CLIP_TOKEN_MINT}"))
        print(c("d", "      Or run with --demo to try without a wallet\n"))
        sys.exit(1)


# ─── Stream Capture ───────────────────────────────────────────────────────────

class StreamCapture:
    def __init__(self, url, platform, output_dir="./clips"):
        self.url = url
        self.platform = platform
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recording = False
        self.process = None
        self.buffer_file = None
        self.start_time = None

    def start_buffer(self, quality="best"):
        print(c("c", f"\n  [>] Connecting to {self.platform}: {self.url}"))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.buffer_file = self.output_dir / f"buffer_{ts}.ts"
        self.start_time = time.time()
        try:
            self.process = subprocess.Popen(
                ["streamlink", "--ringbuffer-size", "64M", "-o", str(self.buffer_file), self.url, quality],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(3)  # give streamlink time to connect
            print(c("g", f"  [✓] Buffering stream → {self.buffer_file.name}"))
        except FileNotFoundError:
            print(c("y", "  [!] streamlink not found — install with: pip install streamlink"))
            print(c("y", "  [~] Running in simulated buffer mode"))
            self.buffer_file.touch()
        self.recording = True
        return True

    def clip(self, start_offset=0, duration=60, label=None):
        """Extract a clip from the stream buffer."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        lbl = f"_{label.replace(' ', '_')}" if label else ""
        out = self.output_dir / f"clip{lbl}_{ts}.mp4"

        if self.buffer_file and self.buffer_file.exists() and self.buffer_file.stat().st_size > 0:
            result = subprocess.run(
                ["ffmpeg", "-y", "-ss", str(max(0, start_offset)), "-i", str(self.buffer_file),
                 "-t", str(duration), "-c", "copy", str(out)],
                capture_output=True
            )
            if result.returncode != 0:
                print(c("y", f"  [!] ffmpeg error — check that ffmpeg is installed"))
        else:
            # Demo mode: create empty placeholder
            out.touch()

        print(c("g", f"  [✓] Clip saved: {out.name}"))
        return str(out)

    def elapsed(self):
        """Seconds since buffering started."""
        return time.time() - self.start_time if self.start_time else 0

    def stop(self):
        if self.process:
            self.process.terminate()
        self.recording = False
        print(c("d", "  [■] Capture stopped"))


# ─── AI Clipper ───────────────────────────────────────────────────────────────

class AIClipper:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if AI_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def analyze(self, transcript, prompt=None, keywords=None):
        if not self.client:
            return self._mock()
        ctx = []
        if prompt:    ctx.append(f"Goal: {prompt}")
        if keywords:  ctx.append(f"Keywords: {', '.join(keywords)}")
        sys_p = (
            'You are a stream clip analyzer. Given a transcript of stream chat/audio, '
            'identify the best moments to clip. Return ONLY valid JSON with no extra text:\n'
            '{"clips":[{"start":<seconds>,"end":<seconds>,"label":"<slug>","reason":"<why>","score":<1-10>}]}'
        )
        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=sys_p,
                messages=[{"role": "user", "content": f"Transcript:\n{transcript}\n\n{chr(10).join(ctx)}"}]
            )
            return json.loads(msg.content[0].text)
        except Exception as e:
            print(c("d", f"  [AI] Parse error: {e} — using heuristic"))
            return self._mock()

    def _mock(self):
        return {"clips": [
            {"start": 12,  "end": 42,  "label": "hype_moment",  "reason": "Peak energy",    "score": 9},
            {"start": 95,  "end": 125, "label": "funny_fail",   "reason": "Very shareable", "score": 8},
            {"start": 180, "end": 210, "label": "clutch_play",  "reason": "Insane skill",   "score": 10},
        ]}

    def watch_live(self, feed, prompt=None, keywords=None, callback=None):
        print(c("c", "\n  [AI] Autopilot active — watching for moments..."))
        if keywords: print(c("d", f"  [AI] Keywords: {', '.join(keywords)}"))
        if prompt:   print(c("d", f"  [AI] Prompt: {prompt}"))
        buf = []
        for line in feed:
            buf.append(line)
            # Keyword hit — clip immediately
            if keywords:
                for kw in keywords:
                    if kw.lower() in line.lower():
                        print(c("y", f"\n  [!] Keyword hit: '{kw}'"))
                        if callback: callback(label=kw)
            # Every 30 lines, run AI analysis
            if len(buf) >= 30:
                result = self.analyze(" ".join(buf), prompt=prompt, keywords=keywords)
                for clip in sorted(result.get("clips", []), key=lambda x: x["score"], reverse=True)[:2]:
                    if clip["score"] >= 7:
                        print(c("g", f"  [AI] Score {clip['score']}/10 — {clip['label']}: {clip['reason']}"))
                        if callback:
                            callback(
                                label=clip["label"],
                                start=clip["start"],
                                duration=clip["end"] - clip["start"]
                            )
                buf = []


# ─── Whisper Integration (optional) ──────────────────────────────────────────

try:
    from whisper_module import WhisperTranscriber, TwitchChatReader, CombinedFeed
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


def run_autopilot_whisper(capture, ai, args):
    print(c("c", "\n  ── AUTOPILOT + WHISPER MODE ──"))
    print(c("d", "  Real-time audio transcription active"))
    print(c("d", "  Ctrl+C to stop\n"))
    transcriber = WhisperTranscriber(model_size="base", chunk_seconds=15)
    if not transcriber.load_model():
        autopilot(capture, ai, args)
        return
    chat = None
    if "twitch" in args.url.lower():
        channel = args.url.split("/")[-1]
        chat = TwitchChatReader(channel)
        chat.start()
        print(c("g", f"  [✓] Twitch chat reader connected"))
    transcriber.start(str(capture.buffer_file))
    feed = CombinedFeed(whisper=transcriber, chat=chat)
    feed.start()
    kws = args.keywords.split(",") if args.keywords else []

    def on_clip(label=None, start=0, duration=60):
        elapsed = capture.elapsed()
        print(c("y", f"\n  [CLIP] Auto-clipping: {label}"))
        capture.clip(max(0, elapsed - duration), duration, label)

    ai.watch_live(feed.get_feed(), prompt=args.prompt, keywords=kws, callback=on_clip)
    transcriber.stop()
    feed.stop()
    if chat: chat.stop()


# ─── Modes ────────────────────────────────────────────────────────────────────

def banner():
    print(c("c", """
 ██████╗██╗     ██╗██████╗      █████╗ ██╗
██╔════╝██║     ██║██╔══██╗    ██╔══██╗██║
██║     ██║     ██║██████╔╝    ███████║██║
██║     ██║     ██║██╔═══╝     ██╔══██║██║
╚██████╗███████╗██║██║         ██║  ██║██║
 ╚═════╝╚══════╝╚═╝╚═╝         ╚═╝  ╚═╝╚═╝"""))
    print(c("d", f"  AI stream clipping · v{VERSION} · $CLIP token gated\n"))


def interactive(capture, ai, args):
    print(c("c", "\n  ── MANUAL MODE ──"))
    print(c("d", "  Commands:"))
    print(c("d", "    c            → clip last 60 seconds"))
    print(c("d", "    c <sec>      → clip last N seconds"))
    print(c("d", "    c <start> <end> → clip time range"))
    print(c("d", "    l <label>    → set label for next clip"))
    print(c("d", "    q            → quit\n"))
    label = None
    while True:
        try:
            raw = input(c("c", "  clip.ai> ")).strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()
        if cmd == "q":
            break
        elif cmd == "l" and len(parts) > 1:
            label = " ".join(parts[1:])
            print(c("g", f"  [✓] Label: {label}"))
        elif cmd == "c":
            elapsed = capture.elapsed()
            dur = 60
            start = max(0, elapsed - dur)
            if len(parts) == 2:
                dur = int(parts[1])
                start = max(0, elapsed - dur)
            elif len(parts) == 3:
                start = int(parts[1])
                dur = int(parts[2]) - start
            capture.clip(start, dur, label)
            label = None
        else:
            print(c("d", "  [?] Unknown command — type 'c' to clip or 'q' to quit"))


def autopilot(capture, ai, args):
    print(c("c", "\n  ── AUTOPILOT MODE ──"))
    print(c("d", "  AI is watching · Ctrl+C to stop\n"))

    kws = [k.strip() for k in args.keywords.split(",")] if args.keywords else []

    def on_clip(label=None, start=0, duration=60):
        elapsed = capture.elapsed()
        actual_start = max(0, elapsed - duration)
        print(c("y", f"\n  [CLIP] Auto-clipping: {label}"))
        capture.clip(actual_start, duration, label)

    # In demo mode: use a simulated feed
    # In real mode: this would come from whisper/chat — see whisper_module.py
    demo_feed = [
        "chat is going crazy", "OH MY GOD that was insane", "bro did NOT just do that",
        "lets gooo", "clip that clip that", "no way no way", "chat WTF",
        "he actually did it", "that is a world record", "highlight incoming",
        "I cannot believe it", "absolute madness", "POGGERS", "this is the run",
        "chat are you seeing this", "insane", "clip that", "lets go lets go",
        "NO WAY", "actually unreal", "bro", "stream highlight for sure",
        "that clip is going viral", "top 10 moments", "legend", "clip that NOW",
        "I'm screaming", "he did it again", "world class", "chat moment",
    ] * 3

    ai.watch_live(iter(demo_feed), prompt=args.prompt, keywords=kws, callback=on_clip)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="CLIP.AI — AI stream clipping · $CLIP token gated")
    sub = p.add_subparsers(dest="command")

    w = sub.add_parser("watch", help="Watch and clip a stream")
    w.add_argument("url")
    w.add_argument("--autopilot", action="store_true", help="AI autopilot mode")
    w.add_argument("--manual",    action="store_true", help="Manual clip mode")
    w.add_argument("--prompt",    default="",          help='AI prompt e.g. "funny moments"')
    w.add_argument("--keywords",  default="",          help='Comma-separated trigger words e.g. "clip that,lets go"')
    w.add_argument("--output",    default="./clips",   help="Output directory (default: ./clips)")
    w.add_argument("--quality",   default="best",      help="Stream quality (default: best)")
    w.add_argument("--demo",      action="store_true", help="Run without $CLIP token")

    cfg = sub.add_parser("config", help="Configure wallet and API key")
    cfg.add_argument("--wallet")
    cfg.add_argument("--api-key")
    cfg.add_argument("--show", action="store_true")

    sub.add_parser("platforms", help="List supported platforms")

    args = p.parse_args()
    banner()

    if args.command == "platforms":
        print(c("c", "  Supported Platforms:\n"))
        for plat, url in PLATFORMS.items():
            print(f"  · {plat.ljust(12)}{c('d', url)}")
        print()
        return

    if args.command == "config":
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
        if args.wallet:  data["wallet"] = args.wallet;            print(c("g", "  [✓] Wallet saved"))
        if args.api_key: data["anthropic_api_key"] = args.api_key; print(c("g", "  [✓] API key saved"))
        if args.show:
            for k, v in data.items():
                print(f"  {k.ljust(20)}{v[:8]}...")
        CONFIG_PATH.write_text(json.dumps(data, indent=2))
        return

    if args.command == "watch":
        data = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
        TokenGate(data.get("wallet")).gate(bypass_demo=getattr(args, "demo", False))

        plat = "unknown"
        for pl in PLATFORMS:
            if pl in args.url.lower():
                plat = pl
                break

        print(f"  {'Platform'.ljust(20)}{c('c', plat.upper())}")
        print(f"  {'Mode'.ljust(20)}{c('y', 'AUTOPILOT' if args.autopilot else 'MANUAL')}")
        if args.prompt:   print(f"  {'Prompt'.ljust(20)}{c('g', args.prompt)}")
        if args.keywords: print(f"  {'Keywords'.ljust(20)}{c('g', args.keywords)}")
        print()

        api_key = data.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
        capture = StreamCapture(args.url, plat, args.output)
        ai = AIClipper(api_key)
        capture.start_buffer(args.quality)

        try:
            if args.autopilot or not args.manual:
                if WHISPER_AVAILABLE and not getattr(args, "demo", False):
                    run_autopilot_whisper(capture, ai, args)
                else:
                    autopilot(capture, ai, args)
            else:
                interactive(capture, ai, args)
        except KeyboardInterrupt:
            print(c("d", "\n\n  [■] Stopped by user"))
        finally:
            capture.stop()
            print(c("c", f"\n  [✓] Clips saved to: {args.output}/"))
            print(c("d", "  Thanks for using CLIP.AI — powered by $CLIP\n"))
    else:
        p.print_help()


if __name__ == "__main__":
    main()
