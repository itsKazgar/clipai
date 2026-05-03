"""
dashboard.py — Terminal dashboard for CLIP.AI
Shows live clip feed, hype meter, session stats
"""
import os, sys, time, threading, json
from pathlib import Path
from datetime import datetime
from collections import deque

C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","d":"\033[90m","b":"\033[1m","x":"\033[0m","bg":"\033[40m"}
def c(k, t): return C.get(k,"") + t + C["x"]

CLEAR = "\033[2J\033[H"
HIDE  = "\033[?25l"
SHOW  = "\033[?25h"

class Dashboard:
    def __init__(self, channel, mode="autopilot"):
        self.channel   = channel
        self.mode      = mode
        self.clips     = []
        self.messages  = deque(maxlen=12)
        self.hype      = 0.0
        self.running   = False
        self.start_time = time.time()
        self.keywords_hit = 0
        self.ai_clips  = 0
        self.lock      = threading.Lock()

    def add_message(self, user, msg):
        with self.lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.messages.append((ts, user[:12], msg[:52]))

    def add_clip(self, label, score, reason, source="ai"):
        with self.lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.clips.append({
                "time": ts, "label": label,
                "score": score, "reason": reason, "source": source
            })
            if source == "keyword":
                self.keywords_hit += 1
            else:
                self.ai_clips += 1

    def set_hype(self, score):
        with self.lock:
            self.hype = min(10.0, max(0.0, score))

    def _hype_bar(self, width=30):
        filled = int((self.hype / 10) * width)
        color = "g" if self.hype >= 7 else "y" if self.hype >= 4 else "d"
        bar = c(color, "█" * filled) + c("d", "░" * (width - filled))
        return f"{bar} {c('b', str(round(self.hype,1)).ljust(4))}/10"

    def _elapsed(self):
        secs = int(time.time() - self.start_time)
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02}"

    def _box(self, title, width=70):
        top = f"┌─ {title} " + "─" * (width - len(title) - 4) + "┐"
        bot = "└" + "─" * (width - 2) + "┘"
        return top, bot, width

    def render(self):
        W = 72
        lines = []
        lines.append(c("c", f"  CLIP.AI  ·  {self.channel}  ·  {self.mode.upper()}  ·  {self._elapsed()}"))
        lines.append(c("d", "  " + "─" * W))

        # hype meter
        lines.append(f"  {c('d','HYPE')}  {self._hype_bar(38)}  {c('d','clips:')} {c('g', str(len(self.clips)))}")
        lines.append(c("d", "  " + "─" * W))

        # stats row
        lines.append(
            f"  {c('d','keyword hits:')} {c('y', str(self.keywords_hit).ljust(4))}  "
            f"{c('d','ai clips:')} {c('g', str(self.ai_clips).ljust(4))}  "
            f"{c('d','total:')} {c('c', str(len(self.clips)))}"
        )
        lines.append(c("d", "  " + "─" * W))

        # live chat
        lines.append(c("d", "  LIVE CHAT"))
        with self.lock:
            msgs = list(self.messages)
        if not msgs:
            lines.append(c("d", "  waiting for chat..."))
        for ts, user, msg in msgs[-8:]:
            lines.append(f"  {c('d',ts)} {c('c',user.ljust(13))} {c('w',msg)}")

        lines.append(c("d", "  " + "─" * W))

        # recent clips
        lines.append(c("d", "  CLIPS"))
        with self.lock:
            recent = list(self.clips[-6:])
        if not recent:
            lines.append(c("d", "  no clips yet..."))
        for cl in reversed(recent):
            score_c = "g" if cl["score"] >= 8 else "y"
            src_c   = "y" if cl["source"] == "keyword" else "c"
            lines.append(
                f"  {c('d',cl['time'])}  "
                f"{c(score_c, str(cl['score']).ljust(2))}/10  "
                f"{c('b', cl['label'].ljust(20))}  "
                f"{c('d', cl['reason'][:28])}"
            )

        lines.append(c("d", "  " + "─" * W))
        lines.append(c("d", "  Ctrl+C to stop  ·  clips saved to ./clips/"))

        return "\n".join(lines)

    def start(self):
        self.running = True
        print(HIDE, end="", flush=True)
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while self.running:
            output = CLEAR + self.render()
            sys.stdout.write(output)
            sys.stdout.flush()
            time.sleep(0.3)

    def stop(self):
        self.running = False
        time.sleep(0.4)
        print(SHOW, end="")
        print(CLEAR)
        print(c("c", f"\n  Session complete — {self._elapsed()}"))
        print(c("g", f"  {len(self.clips)} clips saved\n"))
        if self.clips:
            print(c("d", "  All clips:"))
            for cl in self.clips:
                print(f"  {c('d',cl['time'])}  {c('g',str(cl['score']))}/10  {cl['label']}")
        print()


class SessionLogger:
    """Saves full session data as JSON for the community gallery."""
    def __init__(self, channel, output_dir="./clips"):
        self.channel    = channel
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = self.output_dir / f"session_{channel}_{ts}.json"
        self.data = {
            "channel":  channel,
            "started":  datetime.now().isoformat(),
            "clips":    [],
            "prompts":  [],
            "keywords": [],
        }

    def log_clip(self, label, score, reason, file_path=None):
        self.data["clips"].append({
            "time":      datetime.now().isoformat(),
            "label":     label,
            "score":     score,
            "reason":    reason,
            "file":      str(file_path) if file_path else None,
        })
        self._save()

    def log_prompt(self, prompt):
        self.data["prompts"].append(prompt)
        self._save()

    def _save(self):
        self.path.write_text(json.dumps(self.data, indent=2))

    def summary(self):
        return self.data
