"""
postprocess.py — Post processing for CLIP.AI
Auto vertical crop 9:16, Whisper subtitles, basic effects
"""
import subprocess, os, json, time
from pathlib import Path

C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","d":"\033[90m","x":"\033[0m"}
def c(k, t): return C.get(k,"") + t + C["x"]

def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg","-version"], capture_output=True, check=True)
        return True
    except: return False

def has_whisper():
    try:
        import whisper
        return True
    except: return False

def vertical_crop(input_path, output_path=None, resolution="1080x1920"):
    """Crop 16:9 stream clip to 9:16 vertical for TikTok/Reels/Shorts."""
    inp = Path(input_path)
    out = Path(output_path) if output_path else inp.parent / f"{inp.stem}_vertical.mp4"
    w, h = resolution.split("x")
    print(c("c", f"  [>] Cropping to vertical {resolution}..."))
    result = subprocess.run([
        "ffmpeg", "-y", "-i", str(inp),
        "-vf", f"crop=ih*9/16:ih,scale={w}:{h}",
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast", str(out)
    ], capture_output=True)
    if result.returncode == 0:
        print(c("g", f"  [✓] Vertical clip: {out.name}"))
        return str(out)
    else:
        print(c("y", f"  [!] Crop failed: {result.stderr.decode()[:200]}"))
        return None

def add_subtitles(input_path, output_path=None, model_size="base", style="tiktok"):
    """Transcribe with Whisper and burn subtitles into the clip."""
    if not has_whisper():
        print(c("y", "  [!] Install whisper: pip install openai-whisper"))
        return None
    import whisper
    inp = Path(input_path)
    out = Path(output_path) if output_path else inp.parent / f"{inp.stem}_subtitled.mp4"
    srt = inp.parent / f"{inp.stem}.srt"
    print(c("c", f"  [>] Transcribing with Whisper {model_size}..."))
    model = whisper.load_model(model_size)
    result = model.transcribe(str(inp), word_timestamps=True)

    # write SRT file
    with open(srt, "w") as f:
        idx = 1
        for seg in result["segments"]:
            start = _fmt_time(seg["start"])
            end   = _fmt_time(seg["end"])
            text  = seg["text"].strip()
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")
            idx += 1
    print(c("g", f"  [✓] Subtitles written: {srt.name}"))

    # subtitle style
    styles = {
        "tiktok":  "FontName=Arial,FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Bold=1,Alignment=2",
        "minimal": "FontName=Arial,FontSize=14,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=1,Alignment=2",
        "bold":    "FontName=Arial,FontSize=22,PrimaryColour=&H00ffff,OutlineColour=&H000000,Outline=3,Bold=1,Alignment=2",
    }
    style_str = styles.get(style, styles["tiktok"])

    print(c("c", f"  [>] Burning subtitles ({style} style)..."))
    result2 = subprocess.run([
        "ffmpeg", "-y", "-i", str(inp),
        "-vf", f"subtitles={str(srt)}:force_style='{style_str}'",
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast", str(out)
    ], capture_output=True)
    if result2.returncode == 0:
        print(c("g", f"  [✓] Subtitled clip: {out.name}"))
        return str(out)
    else:
        print(c("y", f"  [!] Subtitle burn failed: {result2.stderr.decode()[:200]}"))
        return None

def add_effects(input_path, output_path=None, fade=True, intro_text=None):
    """Add fade in/out and optional intro card to clip."""
    inp = Path(input_path)
    out = Path(output_path) if output_path else inp.parent / f"{inp.stem}_fx.mp4"

    # get duration
    probe = subprocess.run([
        "ffprobe","-v","quiet","-print_format","json",
        "-show_format", str(inp)
    ], capture_output=True)
    try:
        duration = float(json.loads(probe.stdout)["format"]["duration"])
    except:
        duration = 60.0

    filters = []
    if fade:
        filters.append(f"fade=in:0:15,fade=out:st={max(0,duration-1)}:d=1")
    if intro_text:
        safe = intro_text.replace("'", "")
        filters.append(f"drawtext=text='{safe}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=h/4:enable='lt(t,2)'")

    vf = ",".join(filters) if filters else "null"
    print(c("c", f"  [>] Applying effects..."))
    result = subprocess.run([
        "ffmpeg", "-y", "-i", str(inp),
        "-vf", vf,
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast", str(out)
    ], capture_output=True)
    if result.returncode == 0:
        print(c("g", f"  [✓] Effects applied: {out.name}"))
        return str(out)
    else:
        print(c("y", f"  [!] Effects failed"))
        return None

def process_clip(input_path, vertical=True, subtitles=True, effects=True,
                 subtitle_style="tiktok", intro_text=None, whisper_model="base"):
    """Full post-processing pipeline — vertical crop → subtitles → effects."""
    current = input_path
    print(c("c", f"\n  [POST] Processing: {Path(input_path).name}"))

    if vertical:
        result = vertical_crop(current)
        if result: current = result

    if subtitles:
        result = add_subtitles(current, style=subtitle_style, model_size=whisper_model)
        if result: current = result

    if effects:
        result = add_effects(current, fade=True, intro_text=intro_text)
        if result: current = result

    print(c("g", f"  [✓] Final clip: {Path(current).name}\n"))
    return current

def _fmt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
