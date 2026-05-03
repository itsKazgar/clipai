#!/usr/bin/env python3
"""
CLIP.AI — demo_live.py
Real Twitch IRC chat reader + any AI agent for hype detection.

Usage:
  # Anthropic Claude
  python3 demo_live.py xqc --agent claude --api-key sk-ant-...

  # OpenAI / OpenRouter / Kimi / any OpenAI-compatible endpoint
  python3 demo_live.py xqc --agent openrouter --api-key sk-or-... --model mistralai/mistral-7b-instruct
  python3 demo_live.py xqc --agent kimi      --api-key ...       --model moonshot-v1-8k
  python3 demo_live.py xqc --agent openai    --api-key sk-...    --model gpt-4o-mini

  # Ollama (local, no key needed)
  python3 demo_live.py xqc --agent ollama --model hermes3
  python3 demo_live.py xqc --agent ollama --model llama3.2
  python3 demo_live.py xqc --agent ollama --model mistral

  # Keywords only, no AI
  python3 demo_live.py xqc --agent none --keywords "clip that,lets go"

  # Demo mode (no real stream needed)
  python3 demo_live.py --demo --agent ollama --model hermes3
"""

import argparse
import socket
import threading
import time
import sys
import json
import re
import random
from collections import deque
from datetime import datetime

# ── optional deps — imported lazily so missing ones only error if used ────────
def _import(name):
    try:
        return __import__(name)
    except ImportError:
        return None

requests = _import("requests")

# ── ANSI colours ──────────────────────────────────────────────────────────────
R = "\033[0m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
DIM     = "\033[2m"
BOLD    = "\033[1m"
MAGENTA = "\033[95m"

def ts():
    return datetime.now().strftime("%H:%M:%S")

def log(color, tag, msg):
    print(f"{DIM}{ts()}{R}  {color}{tag:<18}{R} {msg}")

# ── AI AGENT BACKENDS ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a stream clipping AI agent. You watch Twitch/Kick chat in real time.
Given a batch of recent chat messages, decide if this moment is worth clipping.

Respond with ONLY valid JSON — no markdown, no explanation:
{
  "clip": true or false,
  "score": 0.0-10.0,
  "label": "one of: hype_moment | funny_moment | clutch_play | world_record | fail_moment | wholesome | no_clip",
  "reason": "one short sentence"
}

Clip if: chat is going crazy, lots of caps, hype words, rapid repeat messages, "clip that", poggers, etc.
Don't clip if: chat is calm, normal conversation, nothing interesting happening."""


def call_claude(messages, api_key, model="claude-haiku-4-5-20251001"):
    """Anthropic Claude API."""
    if not requests:
        raise RuntimeError("pip install requests")
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 200,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": messages}],
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def call_openai_compat(messages, api_key, model, base_url="https://api.openai.com/v1"):
    """OpenAI, OpenRouter, Kimi, Together, Groq — all use the same format."""
    if not requests:
        raise RuntimeError("pip install requests")
    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # OpenRouter needs this
            "HTTP-Referer": "https://itskazgar.github.io/clipai",
            "X-Title": "CLIP.AI",
        },
        json={
            "model": model,
            "max_tokens": 200,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": messages},
            ],
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_ollama(messages, model="hermes3", host="http://localhost:11434"):
    """Local Ollama — no API key needed."""
    if not requests:
        raise RuntimeError("pip install requests")
    resp = requests.post(
        f"{host}/api/chat",
        json={
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": messages},
            ],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


# Agent router — maps --agent flag to a callable(chat_text) -> raw_string
AGENT_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "kimi":       "https://api.moonshot.cn/v1",
    "together":   "https://api.together.xyz/v1",
    "groq":       "https://api.groq.com/openai/v1",
    "openai":     "https://api.openai.com/v1",
}

def build_agent(args):
    """Return a callable: agent(chat_text: str) -> dict with clip/score/label/reason."""
    agent_name = args.agent.lower()

    def parse(raw):
        # Strip markdown code fences if model added them
        raw = re.sub(r"```[a-z]*", "", raw).strip().strip("`").strip()
        try:
            return json.loads(raw)
        except Exception:
            # Try to extract JSON object if model added prose around it
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return json.loads(m.group())
            raise ValueError(f"Could not parse JSON from: {raw[:120]}")

    if agent_name == "claude":
        model = args.model or "claude-haiku-4-5-20251001"
        def agent(text):
            return parse(call_claude(text, args.api_key, model))

    elif agent_name == "ollama":
        model = args.model or "hermes3"
        host  = args.ollama_host or "http://localhost:11434"
        def agent(text):
            return parse(call_ollama(text, model, host))

    elif agent_name in AGENT_BASE_URLS:
        base_url = AGENT_BASE_URLS[agent_name]
        default_models = {
            "openrouter": "mistralai/mistral-7b-instruct",
            "kimi":       "moonshot-v1-8k",
            "together":   "meta-llama/Llama-3-8b-chat-hf",
            "groq":       "llama3-8b-8192",
            "openai":     "gpt-4o-mini",
        }
        model = args.model or default_models[agent_name]
        def agent(text):
            return parse(call_openai_compat(text, args.api_key, model, base_url))

    elif agent_name == "none":
        # Keyword-only mode — no AI
        agent = None

    else:
        print(f"{RED}Unknown agent: {agent_name}{R}")
        print(f"Valid: claude, openai, openrouter, kimi, together, groq, ollama, none")
        sys.exit(1)

    return agent


# ── TWITCH IRC ────────────────────────────────────────────────────────────────

class TwitchIRC:
    def __init__(self, channel, on_message):
        self.channel = channel.lower().lstrip("#")
        self.on_message = on_message
        self._sock = None
        self._running = False

    def connect(self):
        self._sock = socket.socket()
        self._sock.connect(("irc.chat.twitch.tv", 6667))
        self._sock.settimeout(300)
        # Anonymous login — no OAuth needed
        self._send("PASS oauth:clipai_demo_anonymous")
        self._send("NICK justinfan" + str(random.randint(10000, 99999)))
        self._send(f"JOIN #{self.channel}")
        log(GREEN, "[IRC]", f"joined #{self.channel}")

    def _send(self, msg):
        self._sock.send((msg + "\r\n").encode("utf-8"))

    def listen(self):
        self._running = True
        buf = ""
        while self._running:
            try:
                data = self._sock.recv(2048).decode("utf-8", errors="ignore")
                if not data:
                    break
                buf += data
                while "\r\n" in buf:
                    line, buf = buf.split("\r\n", 1)
                    if line.startswith("PING"):
                        self._send("PONG :tmi.twitch.tv")
                        continue
                    # Parse PRIVMSG
                    m = re.match(r":(\w+)!\w+@\S+ PRIVMSG #\S+ :(.*)", line)
                    if m:
                        self.on_message(m.group(1), m.group(2))
            except socket.timeout:
                self._send("PING :tmi.twitch.tv")
            except Exception as e:
                log(RED, "[IRC]", f"error: {e}")
                break

    def stop(self):
        self._running = False
        if self._sock:
            try: self._sock.close()
            except: pass


# ── HYPE ENGINE ───────────────────────────────────────────────────────────────

HYPE_WORDS = {
    "clip that", "clip it", "clipped", "poggers", "pog", "pogchamp",
    "omg", "no way", "lets go", "lgooo", "insane", "clutch", "sheesh",
    "world record", "unreal", "kekw", "lulw", "omegalul", "wtf", "gg",
    "actually", "he did it", "she did it", "first try", "flawless",
}

class HypeEngine:
    def __init__(self, keywords=None):
        self.score = 0.0
        self.keywords = set(k.lower().strip() for k in (keywords or []))
        self.window = deque(maxlen=60)   # last 60 messages
        self.msg_times = deque(maxlen=60)
        self._lock = threading.Lock()

    def push(self, user, msg):
        with self._lock:
            text = msg.lower()
            self.window.append((user, msg))
            self.msg_times.append(time.time())

            # velocity bonus (msgs in last 5s)
            now = time.time()
            recent = sum(1 for t in self.msg_times if now - t < 5)
            velocity_bonus = min(1.0, recent / 10)

            # keyword match
            hype = any(w in text for w in HYPE_WORDS)
            kw   = any(k in text for k in self.keywords) if self.keywords else False
            caps = len(msg) > 4 and msg == msg.upper()

            delta = 0.0
            if kw:    delta += 2.5
            if hype:  delta += 1.2
            if caps:  delta += 0.8
            delta += velocity_bonus * 0.5

            self.score = min(10.0, self.score + delta)
            return kw, hype, caps, recent

    def decay(self):
        with self._lock:
            self.score = max(0.0, self.score - 0.3)

    def snapshot(self):
        """Return last N messages as formatted string for AI."""
        with self._lock:
            msgs = list(self.window)[-30:]
        return "\n".join(f"{u}: {m}" for u, m in msgs)

    def reset_score(self):
        with self._lock:
            self.score = max(0.0, self.score - 4.0)


# ── DEMO MODE — fake chat for testing without a stream ───────────────────────

DEMO_CHAT = [
    ("xqcfan99",    "LETS GOOO"),
    ("pogmaster",   "clip that clip that"),
    ("streamer_lv", "no way bro"),
    ("h4rdcore22",  "KEKW"),
    ("realmike",    "he actually did it"),
    ("noway_tv",    "OMEGALUL"),
    ("clip_this1",  "clip it NOW"),
    ("hypetrain",   "POGGERS POGGERS"),
    ("lurker404",   "insane"),
    ("xqcfan99",    "NO WAY NO WAY NO WAY"),
    ("fasttyper1",  "lets go lets go"),
    ("viewer882",   "world record??"),
    ("gamer_uk",    "LGOOO"),
    ("realmike",    "stream highlight incoming"),
    ("viewer_x",    "first try first try"),
    ("pogmaster",   "clip that omg clip that"),
    ("h4rdcore22",  "SHEESH"),
    ("noway_tv",    "unreal performance"),
    ("clip_this1",  "CLIP IT CLIP IT"),
    ("hypetrain",   "clutch play no way"),
]


# ── MAIN ──────────────────────────────────────────────────────────────────────

def print_banner(agent_name, model, channel, keywords):
    print(f"""
{CYAN}{BOLD}
 ██████╗██╗     ██╗██████╗      █████╗ ██╗
██╔════╝██║     ██║██╔══██╗    ██╔══██╗██║
██║     ██║     ██║██████╔╝    ███████║██║
██║     ██║     ██║██╔═══╝     ██╔══██║██║
╚██████╗███████╗██║██║         ██║  ██║██║
 ╚═════╝╚══════╝╚═╝╚═╝         ╚═╝  ╚═╝╚═╝{R}
""")
    print(f"  {DIM}agent      {R}{CYAN}{agent_name}{R}")
    if model:
        print(f"  {DIM}model      {R}{CYAN}{model}{R}")
    print(f"  {DIM}channel    {R}{CYAN}{channel or 'demo'}{R}")
    if keywords:
        print(f"  {DIM}keywords   {R}{CYAN}{', '.join(keywords)}{R}")
    print(f"  {DIM}threshold  {R}{CYAN}7.5 / 10{R}")
    print()


def run(args):
    agent_name = args.agent.lower()
    model = args.model or ""
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
    channel = args.channel or "demo"

    print_banner(agent_name, model, channel, keywords)

    agent = build_agent(args)
    hype  = HypeEngine(keywords)
    clip_count = [0]
    ai_busy    = [False]

    def maybe_clip(trigger):
        if ai_busy[0]:
            return
        if agent is None:
            # keyword-only — just log it
            clip_count[0] += 1
            log(GREEN, "[✓] CLIP SAVED", f"#{clip_count[0]} — keyword trigger")
            hype.reset_score()
            return

        ai_busy[0] = True
        snapshot = hype.snapshot()

        def ask():
            try:
                prompt = f"Recent chat (last 30 messages):\n{snapshot}\n\nTrigger: {trigger}\n\nShould we clip this moment?"
                result = agent(prompt)
                score = result.get("score", 0)
                label = result.get("label", "unknown")
                reason = result.get("reason", "")
                should_clip = result.get("clip", False)

                if should_clip:
                    clip_count[0] += 1
                    log(YELLOW, "[!] AI DECISION", f"score {score}/10 — {label}")
                    log(GREEN,  "[✓] CLIP SAVED", f"#{clip_count[0]} → {reason}")
                    hype.reset_score()
                else:
                    log(DIM, "[~] AI SKIP", f"score {score}/10 — {reason}")
            except Exception as e:
                log(RED, "[AI ERROR]", str(e))
            finally:
                ai_busy[0] = False

        threading.Thread(target=ask, daemon=True).start()

    def on_message(user, msg):
        kw, is_hype, caps, velocity = hype.push(user, msg)
        score = hype.score

        # Format chat line
        flag = ""
        if kw:      flag = f" {YELLOW}[KW]{R}"
        elif is_hype: flag = f" {MAGENTA}[HYPE]{R}"
        elif caps:  flag = f" {DIM}[CAPS]{R}"

        bar_filled = int(score / 10 * 10)
        bar = f"{GREEN}{'█' * bar_filled}{DIM}{'░' * (10 - bar_filled)}{R}"
        print(f"{DIM}{ts()}{R}  {CYAN}{user:<16}{R} {msg[:80]}{flag}  {bar} {score:.1f}")

        # Keyword trigger — immediate
        if kw:
            log(YELLOW, "[!] KEYWORD HIT", f'"{msg[:40]}" — asking AI...')
            maybe_clip(f'keyword match: "{msg[:40]}"')
            return

        # Hype threshold — AI decides
        if score >= 7.5 and not ai_busy[0]:
            log(YELLOW, "[!] HYPE SPIKE", f"{score:.1f}/10 — {velocity} msgs/5s — asking AI...")
            maybe_clip(f"hype spike {score:.1f}/10, {velocity} msgs in last 5s")

    # Decay loop
    def decay_loop():
        while True:
            time.sleep(2)
            hype.decay()

    threading.Thread(target=decay_loop, daemon=True).start()

    if args.demo:
        log(CYAN, "[~] DEMO MODE", "using fake chat — no real stream needed")
        print()
        try:
            for user, msg in DEMO_CHAT:
                on_message(user, msg)
                time.sleep(0.4 + random.random() * 0.6)
            # Keep running so AI threads finish
            time.sleep(5)
            log(GREEN, "[✓] DEMO DONE", f"{clip_count[0]} clip(s) saved")
        except KeyboardInterrupt:
            pass
        return

    # Real IRC
    log(CYAN, "[>]", f"connecting to twitch IRC for #{channel}...")
    irc = TwitchIRC(channel, on_message)
    try:
        irc.connect()
        log(GREEN, "[✓]", "connected — watching chat")
        print()
        irc.listen()
    except KeyboardInterrupt:
        log(DIM, "[~]", "stopped")
    finally:
        irc.stop()
        print(f"\n  {GREEN}session clips: {clip_count[0]}{R}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="CLIP.AI — watch live chat, let any AI agent decide what to clip",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python3 demo_live.py xqc --agent claude --api-key sk-ant-...
  python3 demo_live.py xqc --agent openrouter --api-key sk-or-... --model mistralai/mistral-7b-instruct
  python3 demo_live.py xqc --agent kimi --api-key ... --model moonshot-v1-8k
  python3 demo_live.py xqc --agent ollama --model hermes3
  python3 demo_live.py xqc --agent none --keywords "clip that,lets go,world record"
  python3 demo_live.py --demo --agent ollama --model llama3.2
        """
    )
    p.add_argument("channel", nargs="?", help="Twitch channel name (e.g. xqc)")
    p.add_argument("--agent", default="ollama",
                   choices=["claude","openai","openrouter","kimi","together","groq","ollama","none"],
                   help="AI backend to use (default: ollama)")
    p.add_argument("--model",      help="Model name (default depends on agent)")
    p.add_argument("--api-key",    help="API key (not needed for ollama/none)")
    p.add_argument("--ollama-host", default="http://localhost:11434",
                   help="Ollama server URL (default: http://localhost:11434)")
    p.add_argument("--keywords",   help='Comma-separated trigger keywords e.g. "clip that,lets go"')
    p.add_argument("--demo",       action="store_true", help="Run with fake chat, no stream needed")
    p.add_argument("--threshold",  type=float, default=7.5, help="Hype score to trigger AI (default 7.5)")

    args = p.parse_args()

    if not args.demo and not args.channel:
        p.error("channel is required unless --demo is used")

    if args.agent not in ("ollama", "none") and not args.api_key:
        p.error(f"--api-key is required for --agent {args.agent}")

    run(args)


if __name__ == "__main__":
    main()
