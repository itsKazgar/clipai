"""
community.py — Community features for CLIP.AI
Shared prompt library, clip gallery, upvoting
Stores data locally + optionally syncs to a public GitHub Gist
"""
import os, json, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

C = {"g":"\033[92m","c":"\033[96m","y":"\033[93m","r":"\033[91m","d":"\033[90m","b":"\033[1m","x":"\033[0m"}
def c(k, t): return C.get(k,"") + t + C["x"]

COMMUNITY_DIR = Path.home() / ".clipai" / "community"
PROMPTS_FILE  = COMMUNITY_DIR / "prompts.json"
GALLERY_FILE  = COMMUNITY_DIR / "gallery.json"

# Public gist IDs — update these once you create them on GitHub
PROMPTS_GIST = "https://gist.githubusercontent.com/itsKazgar/clipai-prompts/raw/prompts.json"
GALLERY_GIST = "https://gist.githubusercontent.com/itsKazgar/clipai-gallery/raw/gallery.json"

DEFAULT_PROMPTS = [
    {"id":"p001","title":"Clutch Plays","prompt":"insane clutch moments, impossible saves, last second wins","tags":["gaming","clutch"],"votes":42,"author":"itsKazgar"},
    {"id":"p002","title":"Funny Fails","prompt":"funny fails, rage moments, unexpected deaths, cursed plays","tags":["funny","fails"],"votes":38,"author":"itsKazgar"},
    {"id":"p003","title":"Hype Chat","prompt":"moments when chat goes absolutely crazy, mass spam, everyone reacting","tags":["hype","chat"],"votes":31,"author":"itsKazgar"},
    {"id":"p004","title":"World Records","prompt":"world record attempts, personal bests, speedrun moments","tags":["records","speedrun"],"votes":27,"author":"itsKazgar"},
    {"id":"p005","title":"Wholesome","prompt":"wholesome moments, heartwarming interactions, streamer being nice","tags":["wholesome"],"votes":19,"author":"itsKazgar"},
    {"id":"p006","title":"PVP Highlights","prompt":"player vs player highlights, kills, outplays, 1v1 wins","tags":["pvp","gaming"],"votes":24,"author":"itsKazgar"},
    {"id":"p007","title":"First Attempts","prompt":"first try success, never done before, impossible on first try","tags":["firsttry"],"votes":15,"author":"itsKazgar"},
    {"id":"p008","title":"Reaction Moments","prompt":"streamer genuine reaction, surprised, shocked, emotional","tags":["reaction"],"votes":22,"author":"itsKazgar"},
]

DEFAULT_GALLERY = []


def _ensure_dir():
    COMMUNITY_DIR.mkdir(parents=True, exist_ok=True)


def _fetch_remote(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CLIP.AI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except:
        return None


def _load(path, default, remote_url=None):
    # try remote first
    if remote_url:
        remote = _fetch_remote(remote_url)
        if remote:
            _ensure_dir()
            path.write_text(json.dumps(remote, indent=2))
            return remote
    # fall back to local
    if path.exists():
        return json.loads(path.read_text())
    return default


def _save(path, data):
    _ensure_dir()
    path.write_text(json.dumps(data, indent=2))


# ── Prompt Library ────────────────────────────────────────────────────────────

def list_prompts(tag=None, sort="votes"):
    prompts = _load(PROMPTS_FILE, DEFAULT_PROMPTS, PROMPTS_GIST)
    if tag:
        prompts = [p for p in prompts if tag in p.get("tags", [])]
    if sort == "votes":
        prompts = sorted(prompts, key=lambda x: x["votes"], reverse=True)
    elif sort == "new":
        prompts = list(reversed(prompts))
    return prompts


def show_prompts(tag=None, sort="votes"):
    prompts = list_prompts(tag=tag, sort=sort)
    print(c("c", "\n  ── PROMPT LIBRARY ──\n"))
    for i, p in enumerate(prompts, 1):
        tags = " ".join(c("d", f"#{t}") for t in p.get("tags", []))
        print(f"  {c('d',str(i).rjust(2))}. {c('b',p['title'].ljust(20))} "
              f"{c('g', str(p['votes']).rjust(3))} votes  {tags}")
        print(f"      {c('d', p['prompt'][:65])}")
        print()
    return prompts


def get_prompt(index_or_id):
    prompts = _load(PROMPTS_FILE, DEFAULT_PROMPTS, PROMPTS_GIST)
    if isinstance(index_or_id, int):
        if 0 <= index_or_id - 1 < len(prompts):
            return prompts[index_or_id - 1]["prompt"]
    for p in prompts:
        if p["id"] == index_or_id:
            return p["prompt"]
    return None


def add_prompt(title, prompt, tags=None, author="anonymous"):
    prompts = _load(PROMPTS_FILE, DEFAULT_PROMPTS)
    new_id = f"p{len(prompts)+1:03}"
    entry = {
        "id":     new_id,
        "title":  title,
        "prompt": prompt,
        "tags":   tags or [],
        "votes":  0,
        "author": author,
        "added":  datetime.now().isoformat(),
    }
    prompts.append(entry)
    _save(PROMPTS_FILE, prompts)
    print(c("g", f"  [✓] Prompt saved: {title} ({new_id})"))
    return entry


def vote_prompt(index_or_id):
    prompts = _load(PROMPTS_FILE, DEFAULT_PROMPTS)
    voted = False
    for i, p in enumerate(prompts):
        match = (isinstance(index_or_id, int) and i == index_or_id - 1) or p["id"] == index_or_id
        if match:
            prompts[i]["votes"] = prompts[i].get("votes", 0) + 1
            voted = True
            print(c("g", f"  [✓] Voted for: {p['title']} ({prompts[i]['votes']} votes)"))
            break
    if voted:
        _save(PROMPTS_FILE, prompts)
    else:
        print(c("y", "  [!] Prompt not found"))


# ── Clip Gallery ──────────────────────────────────────────────────────────────

def add_to_gallery(clip_path, label, score, reason, channel, prompt=None):
    gallery = _load(GALLERY_FILE, DEFAULT_GALLERY)
    entry = {
        "id":      f"c{len(gallery)+1:04}",
        "file":    str(clip_path),
        "label":   label,
        "score":   score,
        "reason":  reason,
        "channel": channel,
        "prompt":  prompt,
        "added":   datetime.now().isoformat(),
        "votes":   0,
    }
    gallery.append(entry)
    _save(GALLERY_FILE, gallery)
    print(c("g", f"  [✓] Added to gallery: {label}"))
    return entry


def show_gallery(limit=10):
    gallery = _load(GALLERY_FILE, DEFAULT_GALLERY)
    gallery = sorted(gallery, key=lambda x: x["score"], reverse=True)
    print(c("c", "\n  ── CLIP GALLERY ──\n"))
    if not gallery:
        print(c("d", "  No clips in gallery yet. Start clipping!"))
        return
    for cl in gallery[:limit]:
        print(f"  {c('g', str(cl['score'])+'∕10')}  "
              f"{c('b', cl['label'].ljust(22))}  "
              f"{c('c', cl['channel'].ljust(16))}  "
              f"{c('d', cl['reason'][:30])}")
    print()


def show_community_menu():
    print(c("c", "\n  ── COMMUNITY ──\n"))
    print(f"  {c('c','1.')} Browse prompt library")
    print(f"  {c('c','2.')} Add a prompt")
    print(f"  {c('c','3.')} Vote on a prompt")
    print(f"  {c('c','4.')} View clip gallery")
    print(f"  {c('c','5.')} Use a prompt from library")
    print(f"  {c('c','q.')} Back\n")
    choice = input(c("c", "  > ")).strip().lower()

    if choice == "1":
        show_prompts()
    elif choice == "2":
        title  = input(c("d", "  Title: ")).strip()
        prompt = input(c("d", "  Prompt: ")).strip()
        tags   = input(c("d", "  Tags (comma separated): ")).strip().split(",")
        author = input(c("d", "  Your name (optional): ")).strip() or "anonymous"
        add_prompt(title, prompt, [t.strip() for t in tags], author)
    elif choice == "3":
        show_prompts()
        num = input(c("d", "  Vote for number: ")).strip()
        try: vote_prompt(int(num))
        except: print(c("y", "  [!] Invalid number"))
    elif choice == "4":
        show_gallery()
    elif choice == "5":
        prompts = show_prompts()
        num = input(c("d", "  Use prompt number: ")).strip()
        try:
            p = prompts[int(num)-1]
            print(c("g", f"\n  [✓] Using: {p['title']}"))
            print(c("d", f"  Prompt: {p['prompt']}"))
            return p["prompt"]
        except: print(c("y", "  [!] Invalid number"))
    return None
