"""
export.py — One-click social export for CLIP.AI
Supports: TikTok, YouTube Shorts, Twitter/X, Discord
"""
import os, json, subprocess, webbrowser
from pathlib import Path

C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","d":"\033[90m","x":"\033[0m"}
def c(k, t): return C.get(k,"") + t + C["x"]

class SocialExporter:
    def __init__(self, config_path=None):
        self.config_path = config_path or Path.home() / ".clipai" / "socials.json"
        self.config = self._load()

    def _load(self):
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {}

    def _save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.config, indent=2))

    def setup(self, platform, **kwargs):
        """Save credentials for a platform."""
        self.config[platform] = kwargs
        self._save()
        print(c("g", f"  [✓] {platform} configured"))

    def export(self, clip_path, platform, title=None, description=None, tags=None):
        """Export clip to a platform."""
        clip = Path(clip_path)
        if not clip.exists():
            print(c("y", f"  [!] File not found: {clip_path}"))
            return False

        title = title or clip.stem.replace("_", " ").title()
        description = description or f"Clipped with CLIP.AI"
        tags = tags or ["clip", "stream", "gaming", "clipai"]

        print(c("c", f"\n  [>] Exporting to {platform}: {clip.name}"))

        if platform == "youtube":
            return self._youtube(clip, title, description, tags)
        elif platform == "tiktok":
            return self._tiktok(clip, title, tags)
        elif platform == "twitter":
            return self._twitter(clip, title)
        elif platform == "discord":
            return self._discord(clip, title, description)
        else:
            print(c("y", f"  [!] Unknown platform: {platform}"))
            return False

    def _youtube(self, clip, title, description, tags):
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            import google.oauth2.credentials as credentials

            creds_data = self.config.get("youtube", {})
            if not creds_data:
                print(c("y", "  [!] YouTube not configured. Run: clipai config --youtube"))
                self._open_guide("youtube")
                return False

            print(c("c", "  [>] Uploading to YouTube..."))
            creds = credentials.Credentials(token=creds_data.get("token"))
            youtube = build("youtube", "v3", credentials=creds)
            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description,
                    "tags": tags,
                    "categoryId": "20"
                },
                "status": {"privacyStatus": "public"}
            }
            media = MediaFileUpload(str(clip), mimetype="video/mp4", resumable=True)
            req = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
            response = req.execute()
            url = f"https://youtube.com/watch?v={response['id']}"
            print(c("g", f"  [✓] Uploaded: {url}"))
            return url
        except ImportError:
            print(c("y", "  [!] Install: pip install google-api-python-client google-auth"))
            return False
        except Exception as e:
            print(c("y", f"  [!] YouTube upload failed: {e}"))
            return False

    def _tiktok(self, clip, title, tags):
        """TikTok requires their Creator API — guide user through setup."""
        creds = self.config.get("tiktok", {})
        if not creds:
            print(c("y", "  [!] TikTok not configured."))
            print(c("d", "  TikTok API requires approval from TikTok for Developers."))
            print(c("d", "  Visit: https://developers.tiktok.com"))
            print(c("d", "  Then run: clipai config --tiktok-token YOUR_TOKEN"))
            self._open_guide("tiktok")
            return False
        try:
            import urllib.request
            tag_str = " ".join(f"#{t}" for t in tags)
            payload = json.dumps({
                "post_info": {
                    "title": f"{title} {tag_str}"[:150],
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": clip.stat().st_size,
                    "chunk_size": clip.stat().st_size,
                    "total_chunk_count": 1,
                }
            }).encode()
            req = urllib.request.Request(
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                data=payload,
                headers={
                    "Authorization": f"Bearer {creds['token']}",
                    "Content-Type": "application/json"
                })
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                upload_url = data["data"]["upload_url"]
                with open(clip, "rb") as f:
                    video_data = f.read()
                upload_req = urllib.request.Request(
                    upload_url,
                    data=video_data,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Length": str(len(video_data)),
                        "Content-Range": f"bytes 0-{len(video_data)-1}/{len(video_data)}"
                    })
                urllib.request.urlopen(upload_req, timeout=60)
                print(c("g", "  [✓] Uploaded to TikTok"))
                return True
        except Exception as e:
            print(c("y", f"  [!] TikTok upload failed: {e}"))
            return False

    def _twitter(self, clip, title):
        """Upload clip to Twitter/X."""
        creds = self.config.get("twitter", {})
        if not creds:
            print(c("y", "  [!] Twitter not configured."))
            print(c("d", "  Get API keys at: https://developer.twitter.com"))
            print(c("d", "  Then run: clipai config --twitter-key KEY --twitter-secret SECRET"))
            return False
        try:
            import tweepy
            auth = tweepy.OAuthHandler(creds["api_key"], creds["api_secret"])
            auth.set_access_token(creds["access_token"], creds["access_secret"])
            api = tweepy.API(auth)
            print(c("c", "  [>] Uploading to Twitter/X..."))
            media = api.media_upload(str(clip), media_category="tweet_video")
            tweet = api.update_status(
                status=title[:280],
                media_ids=[media.media_id])
            url = f"https://twitter.com/i/web/status/{tweet.id}"
            print(c("g", f"  [✓] Tweeted: {url}"))
            return url
        except ImportError:
            print(c("y", "  [!] Install: pip install tweepy"))
            return False
        except Exception as e:
            print(c("y", f"  [!] Twitter upload failed: {e}"))
            return False

    def _discord(self, clip, title, description):
        """Send clip to a Discord webhook."""
        webhook = self.config.get("discord", {}).get("webhook")
        if not webhook:
            print(c("y", "  [!] Discord not configured."))
            print(c("d", "  Get a webhook URL from your Discord server settings."))
            print(c("d", "  Then run: clipai config --discord-webhook URL"))
            return False
        try:
            import urllib.request
            if clip.stat().st_size > 8 * 1024 * 1024:
                print(c("y", "  [!] Clip too large for Discord (8MB limit) — try compressing first"))
                return False
            import mimetypes
            boundary = "----ClipAIBoundary"
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="content"\r\n\r\n'
                f"{title}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{clip.name}"\r\n'
                f"Content-Type: video/mp4\r\n\r\n"
            ).encode() + clip.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
            req = urllib.request.Request(
                webhook, data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            urllib.request.urlopen(req, timeout=30)
            print(c("g", "  [✓] Sent to Discord"))
            return True
        except Exception as e:
            print(c("y", f"  [!] Discord upload failed: {e}"))
            return False

    def _open_guide(self, platform):
        guides = {
            "youtube": "https://developers.google.com/youtube/v3/guides/uploading_a_video",
            "tiktok":  "https://developers.tiktok.com/doc/login-kit-web",
        }
        url = guides.get(platform)
        if url:
            print(c("d", f"  Opening guide: {url}"))
            webbrowser.open(url)

    def list_platforms(self):
        platforms = ["youtube", "tiktok", "twitter", "discord"]
        print(c("c", "\n  Social Export Platforms:\n"))
        for p in platforms:
            configured = p in self.config
            status = c("g", "configured") if configured else c("d", "not configured")
            print(f"  · {p.ljust(12)} {status}")
        print()
