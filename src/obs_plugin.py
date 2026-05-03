"""
obs_plugin.py — OBS Studio integration for CLIP.AI
Connects to OBS via obs-websocket, triggers clips from OBS events
Install: pip install obsws-python
OBS: install obs-websocket plugin from https://obsproject.com/forum/resources/obs-websocket-5-0-0.1711/
"""
import json, time, threading, os
from pathlib import Path

C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","d":"\033[90m","b":"\033[1m","x":"\033[0m"}
def c(k, t): return C.get(k,"") + t + C["x"]

class OBSPlugin:
    def __init__(self, host="localhost", port=4455, password=None):
        self.host     = host
        self.port     = port
        self.password = password or os.environ.get("OBS_WEBSOCKET_PASSWORD","")
        self.client   = None
        self.connected = False
        self.clip_callback = None
        self.recording = False

    def connect(self):
        try:
            import obsws_python as obs
            self.client = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
                timeout=5
            )
            self.connected = True
            version = self.client.get_version()
            print(c("g", f"  [✓] OBS connected — v{version.obs_version}"))
            return True
        except ImportError:
            print(c("y", "  [!] Install: pip install obsws-python"))
            return False
        except Exception as e:
            print(c("y", f"  [!] OBS connection failed: {e}"))
            print(c("d", "  Make sure OBS is running with obs-websocket enabled"))
            print(c("d", "  OBS → Tools → WebSocket Server Settings → Enable"))
            return False

    def get_scenes(self):
        if not self.connected: return []
        try:
            resp = self.client.get_scene_list()
            return [s["sceneName"] for s in resp.scenes]
        except Exception as e:
            print(c("y", f"  [!] Could not get scenes: {e}"))
            return []

    def switch_scene(self, scene_name):
        if not self.connected: return False
        try:
            self.client.set_current_program_scene(scene_name)
            print(c("g", f"  [✓] Switched to scene: {scene_name}"))
            return True
        except Exception as e:
            print(c("y", f"  [!] Scene switch failed: {e}"))
            return False

    def start_recording(self):
        if not self.connected: return False
        try:
            self.client.start_record()
            self.recording = True
            print(c("g", "  [✓] OBS recording started"))
            return True
        except Exception as e:
            print(c("y", f"  [!] Could not start recording: {e}"))
            return False

    def stop_recording(self):
        if not self.connected: return None
        try:
            resp = self.client.stop_record()
            self.recording = False
            output = getattr(resp, "output_path", None)
            print(c("g", f"  [✓] OBS recording stopped: {output}"))
            return output
        except Exception as e:
            print(c("y", f"  [!] Could not stop recording: {e}"))
            return None

    def save_replay(self):
        """Save OBS replay buffer — best for clipping last 30-60 seconds."""
        if not self.connected: return False
        try:
            self.client.save_replay_buffer()
            print(c("g", "  [✓] OBS replay buffer saved"))
            return True
        except Exception as e:
            print(c("y", f"  [!] Replay buffer failed: {e}"))
            print(c("d", "  Make sure replay buffer is enabled in OBS output settings"))
            return False

    def start_replay_buffer(self):
        if not self.connected: return False
        try:
            self.client.start_replay_buffer()
            print(c("g", "  [✓] OBS replay buffer started"))
            return True
        except Exception as e:
            print(c("y", f"  [!] Could not start replay buffer: {e}"))
            return False

    def get_stream_status(self):
        if not self.connected: return None
        try:
            resp = self.client.get_stream_status()
            return {
                "streaming": resp.output_active,
                "duration":  getattr(resp, "output_duration", 0),
            }
        except:
            return None

    def set_clip_callback(self, callback):
        """Set a function to call when OBS triggers a clip event."""
        self.clip_callback = callback

    def watch_hotkey(self, hotkey="clip", interval=0.5):
        """
        Poll OBS for a custom hotkey press to trigger clipping.
        In OBS: Tools → Hotkeys → add a custom hotkey named 'clip'
        """
        print(c("c", f"  [OBS] Watching for hotkey: {hotkey}"))
        print(c("d", "  Press your OBS clip hotkey to trigger a clip"))

        def _watch():
            last = None
            while self.connected:
                try:
                    resp = self.client.trigger_hotkey_by_name(hotkey)
                    if resp and self.clip_callback:
                        self.clip_callback(label="obs_hotkey", source="obs")
                except:
                    pass
                time.sleep(interval)

        t = threading.Thread(target=_watch, daemon=True)
        t.start()

    def setup_guide(self):
        print(c("c", "\n  ── OBS SETUP GUIDE ──\n"))
        print(c("d", "  1. Install OBS Studio: https://obsproject.com"))
        print(c("d", "  2. Install obs-websocket plugin:"))
        print(c("d", "     https://obsproject.com/forum/resources/obs-websocket-5-0-0.1711/"))
        print(c("d", "  3. In OBS: Tools → WebSocket Server Settings"))
        print(c("d", "     → Enable WebSocket server"))
        print(c("d", "     → Set a password"))
        print(c("d", "  4. Save password:"))
        print(c("g", "     python3 src/clipai.py config --obs-password YOUR_PASSWORD"))
        print(c("d", "  5. Enable replay buffer:"))
        print(c("d", "     OBS → Settings → Output → Replay Buffer → Enable"))
        print(c("d", "     Set duration to 60 seconds"))
        print(c("d", "  6. Run CLIP.AI with OBS mode:"))
        print(c("g", "     python3 src/clipai.py watch twitch.tv/channel --obs"))
        print()

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        self.connected = False
        print(c("d", "  [OBS] Disconnected"))


class OBSClipper:
    """
    High level wrapper — uses OBS replay buffer for clipping
    instead of streamlink. Better quality, no separate capture needed.
    """
    def __init__(self, obs_plugin, output_dir="./clips"):
        self.obs = obs_plugin
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.clip_count = 0

    def setup(self):
        if not self.obs.connect():
            return False
        self.obs.start_replay_buffer()
        status = self.obs.get_stream_status()
        if status and status["streaming"]:
            print(c("g", "  [✓] OBS is streaming — ready to clip"))
        else:
            print(c("y", "  [!] OBS is not streaming — start your stream first"))
        return True

    def clip(self, label=None, source="ai"):
        """Save OBS replay buffer as a clip."""
        self.obs.save_replay()
        self.clip_count += 1
        label = label or f"clip_{self.clip_count}"
        print(c("g", f"  [✓] OBS clip saved: {label}"))
        return label

    def stop(self):
        self.obs.disconnect()
