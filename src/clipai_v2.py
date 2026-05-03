"""
clipai_v2.py — CLIP.AI v2 full featured runner
Ties together: multi-LLM, post-processing, social export,
dashboard, community, OBS plugin
"""
import os, sys, json, time, argparse, threading
from pathlib import Path
from datetime import datetime

from llm import LLMClient
from postprocess import process_clip, has_ffmpeg
from export import SocialExporter
from dashboard import Dashboard, SessionLogger
from community import show_community_menu, get_prompt, show_prompts, add_to_gallery
from obs_plugin import OBSPlugin, OBSClipper

try:
    from whisper_module import WhisperTranscriber, TwitchChatReader, CombinedFeed
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

VERSION = "2.0.0"
CLIP_TOKEN_MINT = "AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump"
CONFIG_PATH = Path.home() / ".clipai" / "config.json"

C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","d":"\033[90m","b":"\033[1m","x":"\033[0m"}
def c(k, t): return C.get(k,"") + t + C["x"]

PLATFORMS = {
    "twitch":  "https://twitch.tv/",
    "youtube": "https://youtube.com/",
    "kick":    "https://kick.com/",
    "rumble":  "https://rumble.com/",
    "tiktok":  "https://tiktok.com/",
}

def banner():
    print(c("c", """
 ██████╗██╗     ██╗██████╗      █████╗ ██╗
██╔════╝██║     ██║██╔══██╗    ██╔══██╗██║
██║     ██║     ██║██████╔╝    ███████║██║
██║     ██║     ██║██╔═══╝     ██╔══██║██║
╚██████╗███████╗██║██║         ██║  ██║██║
 ╚═════╝╚══════╝╚═╝╚═╝         ╚═╝  ╚═╝╚═╝"""))
    print(c("d", f"  v{VERSION} · multi-LLM · post-processing · social export · OBS\n"))


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def save_config(data):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def build_llm(args, config):
    """Build LLM client from args or config."""
    provider = getattr(args, "llm", None) or config.get("llm_provider", "claude")
    model    = getattr(args, "model", None) or config.get("llm_model", None)
    api_key  = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
    base_url = config.get("ollama_url", "http://localhost:11434")

    llm = LLMClient(provider=provider, model=model, api_key=api_key, base_url=base_url)
    status = c("g", llm.describe()) if llm.available() else c("y", f"{llm.describe()} (unavailable)")
    print(f"  {'LLM'.ljust(20)}{status}")
    return llm


def analyze_moment(llm, recent_lines, prompt=None, keywords=None):
    """Ask LLM to score and label a moment."""
    sys_p = ("You are a stream clip analyzer. Given recent chat or audio transcript, "
             "identify if this is worth clipping. Return ONLY valid JSON:\n"
             '{"label":"<slug>","reason":"<why>","score":<1-10>}')
    context = []
    if prompt:   context.append(f"Goal: {prompt}")
    if keywords: context.append(f"Keywords: {', '.join(keywords)}")
    user_p = f"Recent stream:\n{chr(10).join(recent_lines[-20:])}\n\n{chr(10).join(context)}"
    try:
        text = llm.chat(sys_p, user_p)
        if text:
            text = text.replace("```json","").replace("```","").strip()
            return json.loads(text)
    except:
        pass
    return {"label":"highlight","reason":"Hype moment","score":8}


def post_process_clip(clip_path, args, config):
    """Run post processing pipeline on a clip."""
    if not has_ffmpeg():
        print(c("y", "  [!] ffmpeg not found — skipping post-processing"))
        return clip_path
    vertical  = getattr(args, "vertical", False)
    subtitles = getattr(args, "subtitles", False)
    effects   = getattr(args, "effects", False)
    if not any([vertical, subtitles, effects]):
        return clip_path
    return process_clip(
        clip_path,
        vertical=vertical,
        subtitles=subtitles,
        effects=effects,
        subtitle_style=getattr(args, "subtitle_style", "tiktok"),
        whisper_model=config.get("whisper_model", "base")
    )


def export_clip(clip_path, args, config, label):
    """Export clip to social platforms."""
    platforms = getattr(args, "export", None)
    if not platforms:
        return
    exporter = SocialExporter()
    tags = ["clipai", "stream", "gaming"] + [label.replace("_", "")]
    for platform in platforms.split(","):
        platform = platform.strip()
        exporter.export(clip_path, platform, title=label.replace("_"," ").title(), tags=tags)


def run_watch(args, config):
    """Main watch mode — autopilot or manual."""
    # resolve prompt from library if number given
    prompt = getattr(args, "prompt", "") or ""
    if prompt.isdigit():
        library_prompt = get_prompt(int(prompt))
        if library_prompt:
            prompt = library_prompt
            print(c("g", f"  [✓] Using library prompt: {prompt[:50]}"))

    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []

    # detect platform
    plat = "unknown"
    for pl in PLATFORMS:
        if pl in args.url.lower():
            plat = pl; break

    print(f"  {'Platform'.ljust(20)}{c('c', plat.upper())}")
    print(f"  {'Mode'.ljust(20)}{c('y', 'AUTOPILOT' if args.autopilot else 'MANUAL')}")
    if prompt:   print(f"  {'Prompt'.ljust(20)}{c('g', prompt[:50])}")
    if keywords: print(f"  {'Keywords'.ljust(20)}{c('g', ', '.join(keywords))}")
    print()

    llm     = build_llm(args, config)
    dash    = Dashboard(args.url.split("/")[-1], "autopilot" if args.autopilot else "manual")
    logger  = SessionLogger(args.url.split("/")[-1], args.output)

    # OBS mode
    obs_clipper = None
    if getattr(args, "obs", False):
        obs = OBSPlugin(password=config.get("obs_password",""))
        obs_clipper = OBSClipper(obs, args.output)
        if not obs_clipper.setup():
            print(c("y", "  [!] OBS not available — falling back to streamlink"))
            obs_clipper = None

    # streamlink capture
    capture = None
    if not obs_clipper:
        try:
            import subprocess
            from clipai import StreamCapture
            capture = StreamCapture(args.url, plat, args.output)
            capture.start_buffer(args.quality)
        except Exception as e:
            print(c("y", f"  [!] Capture error: {e}"))

    def do_clip(label="highlight", score=8, reason="", start=0, duration=60):
        """Clip, post-process, log, gallery, export."""
        clip_path = None
        if obs_clipper:
            obs_clipper.clip(label=label)
        elif capture:
            elapsed = capture.elapsed()
            clip_path = capture.clip(max(0, elapsed - duration), duration, label)

        if clip_path:
            clip_path = post_process_clip(clip_path, args, config)
            add_to_gallery(clip_path, label, score, reason, args.url.split("/")[-1], prompt)
            export_clip(clip_path, args, config, label)

        dash.add_clip(label, score, reason)
        logger.log_clip(label, score, reason, clip_path)

    # start dashboard
    dash.start()

    try:
        if args.autopilot:
            _run_autopilot(args, config, llm, dash, keywords, prompt, do_clip, capture)
        else:
            _run_manual(args, capture, do_clip, dash)
    except KeyboardInterrupt:
        pass
    finally:
        dash.stop()
        if capture: capture.stop()
        if obs_clipper: obs_clipper.stop()
        summary = logger.summary()
        print(c("c", f"\n  [✓] Session saved: {len(summary['clips'])} clips"))
        print(c("d", f"  Thanks for using CLIP.AI v{VERSION}\n"))


def _run_autopilot(args, config, llm, dash, keywords, prompt, do_clip, capture):
    """Autopilot loop — real chat + AI analysis."""
    channel = args.url.split("/")[-1]
    buf = []

    if WHISPER_AVAILABLE and not getattr(args, "demo", False) and capture:
        transcriber = WhisperTranscriber(model_size=config.get("whisper_model","base"))
        chat = None
        if "twitch" in args.url.lower():
            from whisper_module import TwitchChatReader
            chat = TwitchChatReader(channel)
            chat.start()
        transcriber.start(str(capture.buffer_file))
        feed_obj = CombinedFeed(whisper=transcriber, chat=chat)
        feed_obj.start()
        feed = feed_obj.get_feed()
    else:
        # demo feed
        feed = iter([
            "chat is going crazy","OH MY GOD","bro did NOT just do that",
            "lets gooo","clip that clip that","no way","chat WTF",
            "he actually did it","world record","highlight incoming",
            "I cannot believe it","absolute madness","POGGERS",
            "clip that","insane","NO WAY","stream highlight",
            "going viral","legend","clip that NOW","unreal","world class",
        ] * 4)

    last_clip = 0
    cooldown  = 45
    for line in feed:
        dash.add_message("chat", line)
        buf.append(line)

        # keyword trigger
        for kw in keywords:
            if kw.lower() in line.lower():
                result = analyze_moment(llm, buf, prompt, keywords)
                dash.set_hype(result["score"])
                do_clip(result["label"], result["score"], result["reason"])
                last_clip = time.time()
                buf = []
                break

        # AI auto trigger every 30 lines
        if len(buf) >= 30 and time.time() - last_clip > cooldown:
            result = analyze_moment(llm, buf, prompt, keywords)
            dash.set_hype(result["score"])
            if result["score"] >= 7:
                do_clip(result["label"], result["score"], result["reason"])
                last_clip = time.time()
            buf = []


def _run_manual(args, capture, do_clip, dash):
    """Manual clip mode."""
    print(c("c", "\n  -- MANUAL MODE --"))
    print(c("d", "  c = clip 60s | c <sec> | c <start> <end> | l <label> | q = quit\n"))
    label = None
    while True:
        try:
            raw = input(c("c", "  clip.ai> ")).strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not raw: continue
        parts = raw.split(); cmd = parts[0].lower()
        if cmd == "q": break
        elif cmd == "l" and len(parts) > 1:
            label = " ".join(parts[1:])
            print(c("g", f"  [✓] Label: {label}"))
        elif cmd == "c":
            elapsed = capture.elapsed() if capture else 0
            dur = 60; start = max(0, elapsed - dur)
            if len(parts) == 2: dur = int(parts[1]); start = max(0, elapsed - dur)
            elif len(parts) == 3: start = int(parts[1]); dur = int(parts[2]) - start
            do_clip(label or "manual_clip", 8, "Manual clip", start, dur)
            label = None
        else:
            print(c("d", "  [?] Unknown — type c to clip or q to quit"))


def main():
    p = argparse.ArgumentParser(description=f"CLIP.AI v{VERSION}")
    sub = p.add_subparsers(dest="command")

    # watch command
    w = sub.add_parser("watch", help="Watch and clip a stream")
    w.add_argument("url")
    w.add_argument("--autopilot",  action="store_true")
    w.add_argument("--manual",     action="store_true")
    w.add_argument("--prompt",     default="", help="AI prompt or library number e.g. 1")
    w.add_argument("--keywords",   default="")
    w.add_argument("--output",     default="./clips")
    w.add_argument("--quality",    default="best")
    w.add_argument("--demo",       action="store_true")
    w.add_argument("--llm",        default="claude", help="claude|openai|ollama|hermes3|gemini")
    w.add_argument("--model",      default=None,     help="Override model name")
    w.add_argument("--obs",        action="store_true", help="Use OBS replay buffer")
    w.add_argument("--vertical",   action="store_true", help="Auto crop to 9:16")
    w.add_argument("--subtitles",  action="store_true", help="Burn in Whisper subtitles")
    w.add_argument("--effects",    action="store_true", help="Add fade and effects")
    w.add_argument("--subtitle-style", default="tiktok", help="tiktok|minimal|bold")
    w.add_argument("--export",     default=None, help="Export to: youtube,tiktok,twitter,discord")

    # config command
    cfg = sub.add_parser("config", help="Configure keys and settings")
    cfg.add_argument("--wallet")
    cfg.add_argument("--api-key",           dest="api_key")
    cfg.add_argument("--openai-key",        dest="openai_key")
    cfg.add_argument("--gemini-key",        dest="gemini_key")
    cfg.add_argument("--ollama-url",        dest="ollama_url")
    cfg.add_argument("--obs-password",      dest="obs_password")
    cfg.add_argument("--llm",              default=None)
    cfg.add_argument("--whisper-model",    dest="whisper_model", default=None)
    cfg.add_argument("--discord-webhook",  dest="discord_webhook")
    cfg.add_argument("--show",             action="store_true")

    # other commands
    sub.add_parser("platforms",  help="List supported platforms")
    sub.add_parser("community",  help="Browse prompt library and clip gallery")
    sub.add_parser("obs-setup",  help="OBS setup guide")
    sub.add_parser("prompts",    help="Browse prompt library")

    args = p.parse_args()
    banner()

    if args.command == "platforms":
        print(c("c", "  Supported Platforms:\n"))
        for pl, url in PLATFORMS.items():
            print(f"  · {pl.ljust(12)}{c('d', url)}")
        print(); return

    if args.command == "obs-setup":
        OBSPlugin().setup_guide(); return

    if args.command == "community":
        show_community_menu(); return

    if args.command == "prompts":
        show_prompts(); return

    if args.command == "config":
        config = load_config()
        if args.wallet:         config["wallet"]             = args.wallet;         print(c("g","  [✓] Wallet saved"))
        if args.api_key:        config["anthropic_api_key"]  = args.api_key;        print(c("g","  [✓] Anthropic key saved"))
        if args.openai_key:     config["openai_api_key"]     = args.openai_key;     print(c("g","  [✓] OpenAI key saved"))
        if args.gemini_key:     config["gemini_api_key"]     = args.gemini_key;     print(c("g","  [✓] Gemini key saved"))
        if args.ollama_url:     config["ollama_url"]         = args.ollama_url;     print(c("g","  [✓] Ollama URL saved"))
        if args.obs_password:   config["obs_password"]       = args.obs_password;   print(c("g","  [✓] OBS password saved"))
        if args.llm:            config["llm_provider"]       = args.llm;            print(c("g",f"  [✓] LLM set to {args.llm}"))
        if args.whisper_model:  config["whisper_model"]      = args.whisper_model;  print(c("g","  [✓] Whisper model saved"))
        if args.discord_webhook:
            socials = json.loads((Path.home()/".clipai"/"socials.json").read_text()) if (Path.home()/".clipai"/"socials.json").exists() else {}
            socials["discord"] = {"webhook": args.discord_webhook}
            (Path.home()/".clipai"/"socials.json").write_text(json.dumps(socials, indent=2))
            print(c("g","  [✓] Discord webhook saved"))
        if args.show:
            for k, v in config.items():
                val = v[:8]+"..." if isinstance(v,str) and len(v)>8 else v
                print(f"  {k.ljust(24)}{val}")
        save_config(config)
        return

    if args.command == "watch":
        config = load_config()
        run_watch(args, config)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
