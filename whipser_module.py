"""
whisper_module.py — Real-time Whisper transcription + Twitch chat reader for CLIP.AI

Dependencies:
    pip install openai-whisper sounddevice numpy socket irc
"""

import threading
import queue
import time
import os


# ─── Whisper Transcriber ─────────────────────────────────────────────────────

class WhisperTranscriber:
    """
    Transcribes audio from a stream buffer file in real time using OpenAI Whisper.
    Reads the .ts buffer written by streamlink in chunks.
    """

    def __init__(self, model_size="base", chunk_seconds=15):
        self.model_size = model_size
        self.chunk_seconds = chunk_seconds
        self.model = None
        self.running = False
        self._thread = None
        self._queue = queue.Queue()
        self._buffer_path = None

    def load_model(self):
        try:
            import whisper
            print(f"  [Whisper] Loading model: {self.model_size}...")
            self.model = whisper.load_model(self.model_size)
            print(f"  [Whisper] Model ready")
            return True
        except ImportError:
            print("  [!] openai-whisper not installed. Run: pip install openai-whisper")
            return False
        except Exception as e:
            print(f"  [!] Whisper load failed: {e}")
            return False

    def start(self, buffer_path):
        self._buffer_path = buffer_path
        self.running = True
        self._thread = threading.Thread(target=self._transcribe_loop, daemon=True)
        self._thread.start()

    def _transcribe_loop(self):
        """Read chunks from the buffer file and transcribe."""
        import subprocess
        chunk_num = 0
        while self.running:
            time.sleep(self.chunk_seconds)
            if not self._buffer_path or not os.path.exists(self._buffer_path):
                continue
            # Extract a chunk of audio from the buffer using ffmpeg
            chunk_file = f"/tmp/clip_chunk_{chunk_num}.wav"
            offset = max(0, chunk_num * self.chunk_seconds)
            result = subprocess.run(
                ["ffmpeg", "-y", "-ss", str(offset), "-i", self._buffer_path,
                 "-t", str(self.chunk_seconds), "-ar", "16000", "-ac", "1", chunk_file],
                capture_output=True
            )
            if result.returncode == 0 and os.path.exists(chunk_file):
                try:
                    out = self.model.transcribe(chunk_file, fp16=False)
                    text = out.get("text", "").strip()
                    if text:
                        self._queue.put(f"[audio] {text}")
                except Exception as e:
                    pass
                finally:
                    try: os.remove(chunk_file)
                    except: pass
            chunk_num += 1

    def get_lines(self):
        lines = []
        while not self._queue.empty():
            try: lines.append(self._queue.get_nowait())
            except queue.Empty: break
        return lines

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)


# ─── Twitch Chat Reader ───────────────────────────────────────────────────────

class TwitchChatReader:
    """
    Connects to Twitch IRC anonymously and reads chat messages.
    No OAuth needed for read-only access.
    """

    def __init__(self, channel):
        self.channel = channel.lstrip("#").lower()
        self.running = False
        self._thread = None
        self._queue = queue.Queue()

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        import socket
        HOST = "irc.chat.twitch.tv"
        PORT = 6667
        try:
            sock = socket.socket()
            sock.connect((HOST, PORT))
            sock.settimeout(5)
            # Anonymous login
            sock.send(b"NICK justinfan12345\r\n")
            sock.send(b"USER justinfan12345 0 * :justinfan12345\r\n")
            sock.send(f"JOIN #{self.channel}\r\n".encode())
            buf = ""
            while self.running:
                try:
                    data = sock.recv(2048).decode("utf-8", errors="ignore")
                    buf += data
                    while "\r\n" in buf:
                        line, buf = buf.split("\r\n", 1)
                        if "PRIVMSG" in line:
                            # Extract the message text
                            parts = line.split("PRIVMSG", 1)
                            if len(parts) == 2:
                                msg = parts[1].split(":", 1)[-1].strip()
                                self._queue.put(f"[chat] {msg}")
                        elif line.startswith("PING"):
                            sock.send(b"PONG :tmi.twitch.tv\r\n")
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception as e:
            print(f"  [!] Twitch chat error: {e}")

    def get_lines(self):
        lines = []
        while not self._queue.empty():
            try: lines.append(self._queue.get_nowait())
            except queue.Empty: break
        return lines

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)


# ─── Combined Feed ────────────────────────────────────────────────────────────

class CombinedFeed:
    """
    Merges Whisper transcription + Twitch chat into a single iterable feed
    that the AIClipper.watch_live() method can consume.
    """

    def __init__(self, whisper=None, chat=None):
        self.whisper = whisper
        self.chat = chat
        self.running = False
        self._queue = queue.Queue()
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._merge_loop, daemon=True)
        self._thread.start()

    def _merge_loop(self):
        while self.running:
            if self.whisper:
                for line in self.whisper.get_lines():
                    self._queue.put(line)
            if self.chat:
                for line in self.chat.get_lines():
                    self._queue.put(line)
            time.sleep(0.5)

    def get_feed(self):
        """Generator that yields lines as they arrive."""
        while self.running:
            try:
                yield self._queue.get(timeout=1)
            except queue.Empty:
                continue

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)
