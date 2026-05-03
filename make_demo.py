# writes demo/index.html and updates clipai.py with real mint address
import pathlib

MINT = "AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump"
PUMP_URL = f"https://pump.fun/coin/{MINT}"

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>CLIP.AI — AI Stream Clipping · $CLIP</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
:root{--bg:#0a0c0f;--bg2:#0f1318;--bg3:#151a22;--border:#1e2733;--dim:#2a3444;--muted:#4a5a6e;--text:#c8d8e8;--bright:#e8f4ff;--cyan:#00d4ff;--green:#00ff88;--yellow:#ffcc00;--red:#ff4466;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;font-size:14px;line-height:1.6;min-height:100vh;}
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,212,255,.015) 2px,rgba(0,212,255,.015) 4px);pointer-events:none;z-index:9999;}
.wrap{max-width:860px;margin:0 auto;padding:0 24px;}
header{border-bottom:1px solid var(--border);padding:16px 0;}
.topbar{display:flex;align-items:center;justify-content:space-between;}
.logo{font-size:11px;color:var(--muted);letter-spacing:.15em;}
.logo span{color:var(--cyan);}
.badge{font-size:10px;padding:3px 10px;border:1px solid var(--yellow);color:var(--yellow);letter-spacing:.1em;}
.banner{padding:40px 0 28px;text-align:center;}
.ascii{font-size:clamp(7px,1.3vw,12px);line-height:1.2;color:var(--cyan);white-space:pre;text-shadow:0 0 20px rgba(0,212,255,.4);display:inline-block;}
.tagline{margin-top:16px;color:var(--muted);font-size:12px;letter-spacing:.08em;}
.tagline em{color:var(--green);font-style:normal;}
.terminal{background:var(--bg2);border:1px solid var(--border);margin:0 0 36px;overflow:hidden;}
.tbar{background:var(--bg3);border-bottom:1px solid var(--border);padding:9px 16px;display:flex;align-items:center;gap:7px;font-size:11px;color:var(--muted);}
.dot{width:10px;height:10px;border-radius:50%;}
.tbody{padding:18px 22px;min-height:260px;font-size:12px;}
.ln{display:flex;gap:8px;margin-bottom:2px;}
.cursor{display:inline-block;width:8px;height:13px;background:var(--cyan);vertical-align:middle;animation:blink 1s step-end infinite;}
@keyframes blink{50%{opacity:0;}}
.sec{font-size:10px;letter-spacing:.2em;color:var(--muted);text-transform:uppercase;margin-bottom:14px;}
.sec::before{content:'// ';color:var(--dim);}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:36px;}
.card{background:var(--bg2);padding:18px;transition:background .15s;}
.card:hover{background:var(--bg3);}
.ci{font-size:10px;color:var(--cyan);letter-spacing:.15em;margin-bottom:8px;}
.ct{color:var(--bright);font-size:13px;font-weight:700;margin-bottom:5px;}
.cd{color:var(--muted);font-size:12px;line-height:1.6;}
.coin{border:1px solid var(--yellow);padding:20px;margin-bottom:36px;display:grid;grid-template-columns:1fr 1fr;gap:20px;}
@media(max-width:560px){.coin{grid-template-columns:1fr;}}
.val{font-size:26px;font-weight:700;color:var(--yellow);font-family:monospace;}
.lbl{font-size:10px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-top:3px;}
.codeblock{background:var(--bg2);border:1px solid var(--border);padding:12px 18px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;gap:10px;}
.codeblock code{color:var(--green);font-family:inherit;font-size:12px;flex:1;}
.cpbtn{background:transparent;border:1px solid var(--dim);color:var(--muted);font-family:inherit;font-size:10px;padding:3px 9px;cursor:pointer;flex-shrink:0;transition:all .15s;}
.cpbtn:hover{border-color:var(--cyan);color:var(--cyan);}
.cpbtn.ok{border-color:var(--green);color:var(--green);}
.demo{border:1px solid var(--border);margin-bottom:36px;}
.dh{background:var(--bg3);border-bottom:1px solid var(--border);padding:10px 18px;font-size:11px;color:var(--muted);display:flex;justify-content:space-between;}
.db{padding:20px;}
.irow{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;}
.fl{font-size:10px;color:var(--muted);letter-spacing:.1em;margin-bottom:3px;}
.fld{flex:1;min-width:150px;}
input,select{width:100%;background:var(--bg);border:1px solid var(--dim);color:var(--bright);font-family:inherit;font-size:12px;padding:7px 10px;outline:none;transition:border-color .15s;}
input:focus,select:focus{border-color:var(--cyan);}
select option{background:var(--bg2);}
.btn{background:transparent;border:1px solid var(--cyan);color:var(--cyan);font-family:inherit;font-size:11px;padding:7px 18px;cursor:pointer;letter-spacing:.1em;text-transform:uppercase;transition:all .15s;align-self:flex-end;white-space:nowrap;}
.btn:hover{background:var(--cyan);color:var(--bg);}
.log{background:var(--bg);border:1px solid var(--border);padding:14px;min-height:140px;max-height:260px;overflow-y:auto;font-size:12px;line-height:1.9;}
.ll{opacity:0;animation:fi .2s forwards;}
@keyframes fi{to{opacity:1;}}
footer{border-top:1px solid var(--border);padding:20px 0;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--muted);flex-wrap:wrap;gap:10px;}
footer a{color:var(--cyan);text-decoration:none;}
</style>
</head>
<body>
<header><div class="wrap"><div class="topbar">
  <div class="logo">// <span>CLIP.AI</span> · ai stream clipping</div>
  <div class="badge">$CLIP · v1.0.0</div>
</div></div></header>

<div class="wrap">
<div class="banner">
<pre class="ascii"> ██████╗██╗     ██╗██████╗      █████╗ ██╗
██╔════╝██║     ██║██╔══██╗    ██╔══██╗██║
██║     ██║     ██║██████╔╝    ███████║██║
██║     ██║     ██║██╔═══╝     ██╔══██║██║
╚██████╗███████╗██║██║         ██║  ██║██║
 ╚═════╝╚══════╝╚═╝╚═╝         ╚═╝  ╚═╝╚═╝</pre>
<div class="tagline">ai-powered stream clipping · autopilot &amp; manual · token gated by <em>$CLIP</em></div>
</div>

<div class="terminal">
  <div class="tbar">
    <div class="dot" style="background:#ff5f57"></div>
    <div class="dot" style="background:#ffbd2e"></div>
    <div class="dot" style="background:#28ca41"></div>
    <span style="margin-left:6px;">bash — clipai</span>
  </div>
  <div class="tbody" id="term"></div>
</div>

<div class="sec">features</div>
<div class="grid">
  <div class="card"><div class="ci">[ AI ]</div><div class="ct">Autopilot</div><div class="cd">Claude AI watches the stream and clips viral moments automatically.</div></div>
  <div class="card"><div class="ci">[ ✦ ]</div><div class="ct">Prompt Clipping</div><div class="cd">Tell it what you want — "funny fails", "clutch plays". AI finds it.</div></div>
  <div class="card"><div class="ci">[ # ]</div><div class="ct">Keyword Triggers</div><div class="cd">Auto-clip when "clip that" or "insane" hits. You set the words.</div></div>
  <div class="card"><div class="ci">[ ▶ ]</div><div class="ct">Manual Mode</div><div class="cd">Full CLI control. Clip exact timestamps, label clips, export fast.</div></div>
  <div class="card"><div class="ci">[ $ ]</div><div class="ct">$CLIP Token Gate</div><div class="cd">Hold $CLIP on Solana to unlock. Verified via RPC every session.</div></div>
  <div class="card"><div class="ci">[ ⚡ ]</div><div class="ct">Multi-platform</div><div class="cd">Twitch · YouTube · Kick · PumpFun · Rumble · TikTok Live</div></div>
</div>

<div class="sec">try it · interactive demo</div>
<div class="demo">
  <div class="dh"><span>// CLIP.AI SIMULATOR</span><span style="color:var(--green);font-size:10px;">● LIVE</span></div>
  <div class="db">
    <div class="irow">
      <div class="fld"><div class="fl">// stream url</div><input id="url" value="twitch.tv/xqc"/></div>
      <div class="fld" style="max-width:130px;"><div class="fl">// mode</div><select id="mode"><option value="autopilot">autopilot</option><option value="manual">manual</option></select></div>
    </div>
    <div class="irow">
      <div class="fld"><div class="fl">// ai prompt</div><input id="prompt" placeholder="funny moments, clutch plays..."/></div>
      <div class="fld"><div class="fl">// keywords</div><input id="kw" placeholder="clip that, lets go, insane"/></div>
    </div>
    <div class="irow"><button class="btn" onclick="runDemo()">▶ RUN DEMO</button></div>
    <div class="log" id="log"><span style="color:var(--muted);">// click RUN DEMO to simulate</span></div>
  </div>
</div>

<div class="sec">$clip token · solana</div>
<div class="coin">
  <div>
    <div class="val">1,000</div><div class="lbl">min $CLIP to hold</div>
    <br/>
    <div class="val" style="color:var(--cyan);font-size:18px;">AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump</div>
    <div class="lbl">mint address</div>
  </div>
  <div style="font-size:12px;color:var(--muted);line-height:2.2;">
    <span style="color:var(--cyan);">01.</span> Buy $CLIP on <a href="''' + PUMP_URL + '''" style="color:var(--yellow);">pump.fun</a><br>
    <span style="color:var(--cyan);">02.</span> <code style="color:var(--green);">clipai config --wallet &lt;ADDR&gt;</code><br>
    <span style="color:var(--cyan);">03.</span> Balance verified via Solana RPC<br>
    <span style="color:var(--cyan);">04.</span> Clip everything
  </div>
</div>

<div class="sec">install</div>
<div class="codeblock"><code>git clone https://github.com/YOUR_GITHUB/clipai</code><button class="cpbtn" onclick="cp(this,'git clone https://github.com/YOUR_GITHUB/clipai')">copy</button></div>
<div class="codeblock"><code>pip install -r requirements.txt</code><button class="cpbtn" onclick="cp(this,'pip install -r requirements.txt')">copy</button></div>
<div class="codeblock"><code>python src/clipai.py watch twitch.tv/streamer --autopilot --demo</code><button class="cpbtn" onclick="cp(this,'python src/clipai.py watch twitch.tv/streamer --autopilot --demo')">copy</button></div>

</div>

<footer><div class="wrap" style="display:flex;justify-content:space-between;width:100%;flex-wrap:wrap;gap:10px;">
  <div>// CLIP.AI · MIT · <a href="https://github.com/YOUR_GITHUB/clipai">github</a></div>
  <div>powered by <span style="color:var(--yellow);">$CLIP</span> · no bs · ubuntu built</div>
</div></footer>

<script>
const SEQ=[
  {d:0,h:'<span style="color:#00d4ff;">$</span> <span style="color:#e8f4ff;">clipai watch twitch.tv/xqc --autopilot --keywords "clip that,lets go"</span>'},
  {d:600,h:'<span style="color:#c8d8e8;">  [$] Checking $CLIP balance...</span>'},
  {d:1100,h:'<span style="color:#00ff88;">  [✓] Verified: 5,000 $CLIP · mint: AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump</span>'},
  {d:1400,h:'<span style="color:#4a5a6e;">  Platform            </span><span style="color:#00d4ff;">TWITCH</span>'},
  {d:1500,h:'<span style="color:#4a5a6e;">  Mode                </span><span style="color:#ffcc00;">AUTOPILOT</span>'},
  {d:1600,h:'<span style="color:#4a5a6e;">  Keywords            </span><span style="color:#00ff88;">clip that, lets go</span>'},
  {d:1900,h:'<span style="color:#c8d8e8;">  [>] Connecting to twitch: twitch.tv/xqc</span>'},
  {d:2300,h:'<span style="color:#00ff88;">  [✓] Buffering stream → buffer_live.ts</span>'},
  {d:2600,h:'<span style="color:#00d4ff;">  [AI] Autopilot active — watching for moments...</span>'},
  {d:3500,h:'<span style="color:#ffcc00;">  [!] Keyword hit: \'clip that\'</span>'},
  {d:3800,h:'<span style="color:#ffcc00;">  [CLIP] Auto-clipping: clip_that</span>'},
  {d:4100,h:'<span style="color:#00ff88;">  [✓] Clip saved: clip_clip_that_live.mp4</span>'},
  {d:5500,h:'<span style="color:#00d4ff;">  [AI] Score 10/10 — clutch_play: Insane skill moment</span>'},
  {d:5800,h:'<span style="color:#ffcc00;">  [CLIP] Auto-clipping: clutch_play</span>'},
  {d:6100,h:'<span style="color:#00ff88;">  [✓] Clip saved: clip_clutch_play_live.mp4</span>'},
  {d:7500,h:'<span style="color:#00d4ff;">  [AI] Score 9/10 — hype_moment: Peak energy, chat went off</span>'},
  {d:7800,h:'<span style="color:#ffcc00;">  [CLIP] Auto-clipping: hype_moment</span>'},
  {d:8100,h:'<span style="color:#00ff88;">  [✓] Clip saved: clip_hype_moment_live.mp4</span>'},
  {d:8600,h:'<span style="color:#00d4ff;">  [✓] Done · 3 clips · ./clips · powered by $CLIP</span>'},
  {d:8900,h:'<span style="color:#00d4ff;">$</span> <span class="cursor"></span>'},
];
function runTerm(){
  const t=document.getElementById('term');
  t.innerHTML='';
  SEQ.forEach(s=>setTimeout(()=>{
    const d=document.createElement('div');
    d.className='ln';d.innerHTML=s.h;t.appendChild(d);t.scrollTop=t.scrollHeight;
  },s.d));
}
runTerm();setInterval(runTerm,11000);

let busy=false;
function runDemo(){
  if(busy)return;busy=true;
  const log=document.getElementById('log');log.innerHTML='';
  const url=document.getElementById('url').value||'twitch.tv/streamer';
  const mode=document.getElementById('mode').value;
  const prompt=document.getElementById('prompt').value;
  const kw=document.getElementById('kw').value;
  let plat='unknown';
  for(const p of ['twitch','youtube','kick','pumpfun','rumble','tiktok'])if(url.includes(p)){plat=p.toUpperCase();break;}
  const lines=[
    [`<span style="color:#00d4ff;">$</span> <span style="color:#e8f4ff;">clipai watch ${url} --${mode}${prompt?' --prompt "'+prompt+'"':''}${kw?' --keywords "'+kw+'"':''}</span>`,0],
    [`<span style="color:#c8d8e8;">  [$] Checking $CLIP balance...</span>`,400],
    [`<span style="color:#00ff88;">  [✓] Verified · AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump</span>`,900],
    [`<span style="color:#4a5a6e;">  Platform            </span><span style="color:#00d4ff;">${plat}</span>`,1100],
    [`<span style="color:#4a5a6e;">  Mode                </span><span style="color:#ffcc00;">${mode.toUpperCase()}</span>`,1200],
  ];
  if(prompt)lines.push([`<span style="color:#4a5a6e;">  Prompt              </span><span style="color:#00ff88;">${prompt}</span>`,1300]);
  if(kw)lines.push([`<span style="color:#4a5a6e;">  Keywords            </span><span style="color:#00ff88;">${kw}</span>`,1350]);
  lines.push(
    [`<span style="color:#c8d8e8;">  [>] Connecting: ${url}</span>`,1600],
    [`<span style="color:#00ff88;">  [✓] Buffering stream...</span>`,2000],
    [`<span style="color:#00d4ff;">  [AI] Autopilot active...</span>`,2300],
  );
  let t=2600;
  (kw?kw.split(','):[]).forEach((k,i)=>{
    t+=1000+i*500;
    lines.push([`<span style="color:#ffcc00;">  [!] Keyword: '${k.trim()}'</span>`,t]);
    t+=300;lines.push([`<span style="color:#00ff88;">  [✓] Clip saved: clip_${k.trim().replace(/ /g,'_')}.mp4</span>`,t]);
  });
  [['clutch_play','Unbelievable moment',10],['hype_moment','Peak energy',9],['funny_fail','Very shareable',8]].forEach(([l,r,s])=>{
    t+=1600;
    lines.push([`<span style="color:#00d4ff;">  [AI] Score ${s}/10 — ${l}: ${r}</span>`,t]);
    t+=300;lines.push([`<span style="color:#00ff88;">  [✓] Clip saved: clip_${l}.mp4</span>`,t]);
  });
  t+=500;lines.push([`<span style="color:#00d4ff;">  [✓] Done · powered by $CLIP</span>`,t]);
  lines.forEach(([h,d])=>setTimeout(()=>{
    const el=document.createElement('div');el.className='ll';el.innerHTML=h;log.appendChild(el);log.scrollTop=log.scrollHeight;
  },d));
  setTimeout(()=>{busy=false;},t+800);
}
function cp(btn,text){
  navigator.clipboard.writeText(text).then(()=>{
    btn.textContent='copied!';btn.classList.add('ok');
    setTimeout(()=>{btn.textContent='copy';btn.classList.remove('ok');},2000);
  });
}
</script>
</body>
</html>'''

pathlib.Path('demo').mkdir(exist_ok=True)
pathlib.Path('demo/index.html').write_text(html)
print('demo/index.html written!')
