"""
whisper_module.py — drop into ~/clipai/src/
Real-time stream transcription using OpenAI Whisper
"""

import os
import time
import queue
import threading
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","d":"\033[90m","x":"\033[0m"}
def c(k,t): return C.get(k,"")+t+C["x"]

class WhisperTranscriber:
    """
    Pulls audio from a live stream buffer and transcribes in chunks.
    Feeds transcript lines into a queue for AIClipper to consume.
    """

    def __init__(self, model_size="base", chunk_seconds=15):
        self.model_size = model_size
        self.chunk_seconds = chunk_seconds
        self.model = None
        self.transcript_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.buffer_file = None
        self.full_transcript = []

    def load_model(self):
        if not WHISPER_AVAILABLE:
            print(c("y", "  [!] Whisper not installed. Run: pip install openai-whisper"))
            return False
        print(c("c", f"  [W] Loading Whisper model: {self.model_size}..."))
        print(c("d",  "      (first run downloads the model, ~150MB for base)"))
        try:
            self.model = whisper.load_model(self.model_size)
            print(c("g", f"  [✓] Whisper {self.model_size} model ready"))
            return True
        except Exception as e:
            print(c("y", f"  [!] Whisper load failed: {e}"))
            return False

    def _extract_audio_chunk(self, buffer_file, start_sec, duration_sec):
        """Extract a chunk of audio from the stream buffer as WAV"""
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", str(buffer_file),
            "-t", str(duration_sec),
            "-ar", "16000",   # Whisper wants 16kHz
            "-ac", "1",       # mono
            "-f", "wav",
            tmp.name
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            return tmp.name
        return None

    def _transcribe_chunk(self, audio_file):
        """Run Whisper on an audio chunk, return text"""
        if not self.model:
            return None
        try:
            result = self.model.transcribe(
                audio_file,
                language="en",
                fp16=False,
                verbose=False
            )
            text = result.get("text", "").strip()
            os.unlink(audio_file)  # cleanup
            return text if text else None
        except Exception as e:
            print(c("y", f"  [W] Transcription error: {e}"))
            return None

    def start(self, buffer_file):
        """Start transcribing from a stream buffer file in background"""
        self.buffer_file = buffer_file
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(c("g", "  [W] Whisper transcriber started"))

    def _run(self):
        """Background loop: extract audio chunks and transcribe"""
        chunk = 0
        while self.running:
            start = chunk * self.chunk_seconds
            # wait for buffer to have enough data
            time.sleep(self.chunk_seconds)

            if not self.buffer_file or not Path(self.buffer_file).exists():
                continue

            audio = self._extract_audio_chunk(
                self.buffer_file, start, self.chunk_seconds
            )
            if audio:
                text = self._transcribe_chunk(audio)
                if text:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(c("d", f"  [W] [{timestamp}] {text}"))
                    self.transcript_queue.put(text)
                    self.full_transcript.append(text)
            chunk += 1

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)
        print(c("d", "  [W] Transcriber stopped"))

    def get_transcript_feed(self):
        """Generator that yields transcript lines as they come in"""
        while self.running or not self.transcript_queue.empty():
            try:
                line = self.transcript_queue.get(timeout=1)
                yield line
            except queue.Empty:
                continue

    def get_full_transcript(self):
        return " ".join(self.full_transcript)


class TwitchChatReader:
    """
    Reads Twitch IRC chat and feeds messages into transcript queue.
    Works alongside Whisper for combined audio+chat analysis.
    """

    def __init__(self, channel, oauth_token=None):
        self.channel = channel.lstrip("/").split("/")[-1].lower()
        self.oauth = oauth_token or os.environ.get("TWITCH_OAUTH")
        self.running = False
        self.message_queue = queue.Queue()
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._connect, daemon=True)
        self.thread.start()

    def _connect(self):
        import socket
        try:
            sock = socket.socket()
            sock.connect(("irc.chat.twitch.tv", 6667))
            nick = "justinfan12345"  # anonymous read-only
            sock.send(f"NICK {nick}\r\n".encode())
            sock.send(f"JOIN #{self.channel}\r\n".encode())
            sock.settimeout(1)
            print(c("g", f"  [IRC] Connected to #{self.channel} chat"))

            buf = ""
            while self.running:
                try:
                    data = sock.recv(2048).decode("utf-8", errors="ignore")
                    buf += data
                    while "\r\n" in buf:
                        line, buf = buf.split("\r\n", 1)
                        if "PING" in line:
                            sock.send("PONG :tmi.twitch.tv\r\n".encode())
                        elif "PRIVMSG" in line:
                            msg = line.split("PRIVMSG")[1].split(":", 1)[-1].strip()
                            user = line.split("!")[0].lstrip(":")
                            print(c("d", f"  [IRC] {user}: {msg}"))
                            self.message_queue.put(msg)
                except socket.timeout:
                    continue
        except Exception as e:
            print(c("y", f"  [IRC] Chat connection failed: {e}"))

    def stop(self):
        self.running = False

    def get_feed(self):
        while self.running or not self.message_queue.empty():
            try:
                yield self.message_queue.get(timeout=1)
            except queue.Empty:
                continue


class CombinedFeed:
    """
    Merges Whisper audio transcript + Twitch chat into one feed
    for AIClipper to consume.
    """

    def __init__(self, whisper=None, chat=None):
        self.whisper = whisper
        self.chat = chat
        self.combined = queue.Queue()
        self.running = False

    def start(self):
        self.running = True
        if self.whisper:
            threading.Thread(target=self._drain, args=(self.whisper.transcript_queue,), daemon=True).start()
        if self.chat:
            threading.Thread(target=self._drain, args=(self.chat.message_queue,), daemon=True).start()

    def _drain(self, q):
        while self.running:
            try:
                item = q.get(timeout=1)
                self.combined.put(item)
            except queue.Empty:
                continue

    def get_feed(self):
        while self.running:
            try:
                yield self.combined.get(timeout=1)
            except queue.Empty:
                continue

    def stop(self):
        self.running = False


def install_whisper():
    """Helper to install whisper + deps"""
    print(c("c", "\n  [W] Installing Whisper..."))
    cmds = [
        ["pip", "install", "openai-whisper"],
        ["pip", "install", "numpy"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True)
        name = cmd[-1]
        if result.returncode == 0:
            print(c("g", f"  [✓] {name} installed"))
        else:
            print(c("y", f"  [!] {name} failed — try manually: {' '.join(cmd)}"))


if __name__ == "__main__":
    # Quick test
    print(c("c", "\n  Testing Whisper setup...\n"))
    if not WHISPER_AVAILABLE:
        print(c("y", "  Whisper not installed. Run:"))
        print(c("g", "  pip install openai-whisper\n"))
    else:
        t = WhisperTranscriber(model_size="base")
        if t.load_model():
            print(c("g", "\n  [✓] Whisper is ready to transcribe streams!"))
            print(c("d",  "  Usage: from whisper_module import WhisperTranscriber"))
