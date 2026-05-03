#!/usr/bin/env python3
"""
CLIP.AI — Enhanced Demo Mode
Connects to real Twitch chat, detects hype moments, logs what would be clipped.
No streamlink or ffmpeg needed — just: pip install anthropic
"""
import os, sys, json, time, socket, threading, queue, argparse, re
from datetime import datetime
from pathlib import Path
from collections import deque

try:
    import anthropic
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

VERSION = "1.0.0"
CONFIG_PATH = Path.home() / ".clipai" / "config.json"
C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","w":"\033[97m","d":"\033[90m","b":"\033[1m","x":"\033[0m"}
def c(k, t): return C.get(k, "") + t + C["x"]

HYPE_WORDS = [
    "clip that","clip it","clippp","cliiip",
    "pog","poggers","pogchamp",
    "omg","oh my god","wtf","no way","no wayyyy",
    "lets go","letsgo","let's go","LGOOO","lgoooo",
    "insane","insanee","actually insane",
    "bro","broo","brooo",
    "he did it","she did it","they did it",
    "world record","wr","new record",
    "clutch","clutchhh",
    "gg","actual","unreal","sheesh","nahh","nah bro",
    "highlight","stream highlight",
    "i cant","i cannot","i can't",
    "KEKW","LULW","OMEGALUL","COPIUM","Pog","PogU",
    "monkaS","monkaW","NOTED","EZ","Clap",
]

SPAM_PATTERN = re.compile(r'(.)\1{4,}')  # detects AAAAA or !!!!!

def banner():
    print(c("c", """
 ██████╗██╗     ██╗██████╗      █████╗ ██╗
██╔════╝██║     ██║██╔══██╗    ██╔══██╗██║
██║     ██║     ██║██████╔╝    ███████║██║
██║     ██║     ██║██╔═══╝     ██╔══██║██║
╚██████╗███████╗██║██║         ██║  ██║██║
 ╚═════╝╚══════╝╚═╝╚═╝         ╚═╝  ╚═╝╚═╝"""))
    print(c("d", f"  AI stream clipping · v{VERSION} · live demo mode\n"))


class TwitchChat:
    """Anonymous Twitch IRC reader — no login needed."""
    def __init__(self, channel):
        self.channel = channel.lower().strip().split("/")[-1]
        self.q = queue.Queue()
        self.running = False
        self._sock = None

    def start(self):
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        try:
            self._sock = socket.socket()
            self._sock.connect(("irc.chat.twitch.tv", 6667))
            self._sock.settimeout(10)
            self._sock.send(b"NICK justinfan99999\r\n")
            self._sock.send(b"USER justinfan99999 0 * :justinfan\r\n")
            self._sock.send(f"JOIN #{self.channel}\r\n".encode())
            buf = ""
            while self.running:
                try:
                    data = self._sock.recv(4096).decode("utf-8", errors="ignore")
                    buf += data
                    while "\r\n" in buf:
                        line, buf = buf.split("\r\n", 1)
                        if "PRIVMSG" in line:
                            # parse: :user!user@user.tmi.twitch.tv PRIVMSG #channel :message
                            parts = line.split("PRIVMSG", 1)
                            if len(parts) == 2:
                                user_part = parts[0].split("!")[0].lstrip(":")
                                msg = parts[1].split(":", 1)[-1].strip()
                                self.q.put((user_part, msg))
                        elif line.startswith("PING"):
                            self._sock.send(b"PONG :tmi.twitch.tv\r\n")
                except socket.timeout:
                    continue
        except Exception as e:
            self.q.put(("SYSTEM", f"Chat disconnected: {e}"))

    def stop(self):
        self.running = False
        if self._sock:
            try: self._sock.close()
            except: pass

    def get(self, timeout=0.1):
        try: return self.q.get(timeout=timeout)
        except queue.Empty: return None


class HypeDetector:
    """Tracks chat velocity and hype signals to score clip-worthiness."""
    def __init__(self, window=20):
        self.window = window
        self.messages = deque(maxlen=200)
        self.timestamps = deque(maxlen=200)
        self.last_clip = 0
        self.clip_cooldown = 45  # seconds between auto-clips

    def add(self, msg):
        self.messages.append(msg.lower())
        self.timestamps.append(time.time())

    def velocity(self):
        """Messages per second in the last window seconds."""
        now = time.time()
        recent = sum(1 for t in self.timestamps if now - t < self.window)
        return recent / self.window

    def hype_score(self):
        """0-10 score based on chat velocity + hype word frequency."""
        now = time.time()
        recent_msgs = [m for m, t in zip(self.messages, self.timestamps) if now - t < self.window]
        if not recent_msgs: return 0

        # velocity score (0-5)
        vel = self.velocity()
        vel_score = min(5, vel * 3)

        # hype word score (0-3)
        hype_hits = sum(1 for m in recent_msgs if any(h in m for h in HYPE_WORDS))
        hype_score = min(3, hype_hits * 0.5)

        # spam/caps score (0-2) — caps lock = hype
        caps_hits = sum(1 for m in recent_msgs if m != m.lower() and len(m) > 3)
        caps_score = min(2, caps_hits * 0.3)

        return round(vel_score + hype_score + caps_score, 1)

    def should_clip(self):
        return (
            time.time() - self.last_clip > self.clip_cooldown and
            self.hype_score() >= 6
        )

    def mark_clipped(self):
        self.last_clip = time.time()


class AIAnalyzer:
    """Uses Claude to label the clip based on recent chat."""
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if AI_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def label_moment(self, recent_chat, keywords=None):
        if not self.client:
            return self._guess(recent_chat)
        prompt = (
            "You are analyzing Twitch chat to label a viral stream moment.\n"
            "Based on this chat, respond with ONLY a JSON object like:\n"
            '{"label":"clutch_play","reason":"Chat exploding with hype","score":9}\n\n'
            f"Recent chat:\n{chr(10).join(recent_chat[-20:])}"
        )
        if keywords:
            prompt += f"\n\nKeywords triggered: {', '.join(keywords)}"
        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            text = msg.content[0].text.strip()
            # strip markdown fences if present
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except:
            return self._guess(recent_chat)

    def _guess(self, recent_chat):
        joined = " ".join(recent_chat[-15:]).lower()
        if any(w in joined for w in ["clutch","insane","skill","record","wr"]):
            return {"label":"clutch_play","reason":"Insane skill moment","score":10}
        if any(w in joined for w in ["lol","kekw","lulw","funny","fail","died"]):
            return {"label":"funny_moment","reason":"Chat laughing hard","score":8}
        if any(w in joined for w in ["lets go","lgooo","hype","pog","poggers"]):
            return {"label":"hype_moment","reason":"Peak hype in chat","score":9}
        return {"label":"highlight","reason":"Chat going crazy","score":7}


class ClipLogger:
    """Saves a clip log file so users can see what was detected."""
    def __init__(self, channel, output_dir="./clips"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = self.output_dir / f"clip_log_{channel}_{ts}.txt"
        self.clips = []
        self.log_path.write_text(f"CLIP.AI Session Log — {channel} — {datetime.now()}\n{'='*60}\n\n")

    def log(self, label, reason, score, chat_sample, timestamp):
        entry = {
            "time": timestamp,
            "label": label,
            "reason": reason,
            "score": score,
            "chat_sample": chat_sample[-5:],
        }
        self.clips.append(entry)
        with open(self.log_path, "a") as f:
            f.write(f"[{timestamp}] Score {score}/10 — {label}\n")
            f.write(f"  Reason: {reason}\n")
            f.write(f"  Chat:   {' | '.join(chat_sample[-3:])}\n")
            f.write(f"  → Would save: clip_{label}_{timestamp.replace(':','-')}.mp4\n\n")

    def summary(self):
        return self.clips, self.log_path


def run_demo(channel, keywords=None, prompt=None, api_key=None, max_clips=10):
    chat = TwitchChat(channel)
    hype = HypeDetector()
    ai = AIAnalyzer(api_key)
    logger = ClipLogger(channel)

    print(c("c", f"  [>] Connecting to twitch.tv/{channel}..."))
    chat.start()
    time.sleep(2)

    print(c("g", f"  [✓] Live chat connected"))
    if keywords: print(c("d", f"  [>] Keywords: {', '.join(keywords)}"))
    if prompt:   print(c("d", f"  [>] Prompt: {prompt}"))
    print(c("d",  f"  [>] Clips will be logged to: {logger.log_path.name}"))
    print(c("d",  "  [>] Ctrl+C to stop\n"))
    print(c("d",  "  " + "─"*50))

    clips_saved = 0
    recent_chat = []
    session_start = time.time()

    try:
        while clips_saved < max_clips:
            item = chat.get(timeout=0.5)
            if item:
                user, msg = item
                if user == "SYSTEM":
                    print(c("r", f"\n  [!] {msg}"))
                    break

                recent_chat.append(msg)
                hype.add(msg)

                # print chat message
                score = hype.hype_score()
                score_color = "g" if score >= 7 else "y" if score >= 4 else "d"
                bar = "█" * int(score) + "░" * (10 - int(score))
                print(f"  {c('d', user[:12].ljust(12))} {c('w', msg[:60])}")

                # keyword trigger
                kw_hit = []
                if keywords:
                    for kw in keywords:
                        if kw.lower() in msg.lower():
                            kw_hit.append(kw)

                if kw_hit:
                    print(c("y", f"\n  [!] Keyword hit: {', '.join(kw_hit)}"))
                    ts = datetime.now().strftime("%H:%M:%S")
                    result = ai.label_moment(recent_chat, kw_hit)
                    print(c("g", f"  [AI] Score {result['score']}/10 — {result['label']}: {result['reason']}"))
                    print(c("g", f"  [✓] clip_{result['label']}_{ts.replace(':','-')}.mp4 logged"))
                    logger.log(result["label"], result["reason"], result["score"], recent_chat.copy(), ts)
                    clips_saved += 1
                    hype.mark_clipped()
                    print(c("d", "  " + "─"*50))

                # hype auto-trigger
                elif hype.should_clip():
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(c("y", f"\n  [!] Hype spike detected! Score: {score}/10"))
                    result = ai.label_moment(recent_chat)
                    print(c("g", f"  [AI] {result['label']}: {result['reason']}"))
                    print(c("g", f"  [✓] clip_{result['label']}_{ts.replace(':','-')}.mp4 logged"))
                    logger.log(result["label"], result["reason"], result["score"], recent_chat.copy(), ts)
                    clips_saved += 1
                    hype.mark_clipped()
                    print(c("d", "  " + "─"*50))

    except KeyboardInterrupt:
        pass
    finally:
        chat.stop()
        clips, log_path = logger.summary()
        elapsed = int(time.time() - session_start)
        print(c("c", f"\n\n  [✓] Session ended — {elapsed}s — {len(clips)} moments detected"))
        print(c("d", f"  [✓] Full log saved: {log_path}"))
        if clips:
            print(c("c", "\n  Top moments:"))
            for cl in sorted(clips, key=lambda x: x["score"], reverse=True)[:3]:
                print(c("g", f"    {cl['score']}/10 — {cl['label']} at {cl['time']}"))
        print(c("d", "\n  Install streamlink + ffmpeg to save real .mp4 files\n"))


def main():
    p = argparse.ArgumentParser(description="CLIP.AI Demo — real Twitch chat, no ffmpeg needed")
    p.add_argument("channel", help="Twitch channel name e.g. xqc")
    p.add_argument("--keywords", default="", help='e.g. "clip that,lets go"')
    p.add_argument("--prompt",   default="", help='e.g. "funny moments"')
    p.add_argument("--max-clips", type=int, default=10)
    args = p.parse_args()

    banner()

    data = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    api_key = data.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")

    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []

    print(c("d", f"  Channel   {c('c', args.channel)}"))
    print(c("d", f"  AI        {c('g', 'Claude' if api_key else 'heuristic (no API key)')}"))
    print(c("d", f"  Mode      {c('y', 'LIVE DEMO — logs clips, no video saved')}"))
    print()

    run_demo(args.channel, keywords=keywords, prompt=args.prompt, api_key=api_key, max_clips=args.max_clips)


if __name__ == "__main__":
    main()
