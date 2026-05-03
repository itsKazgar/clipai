import pathlib

html = """<!DOCTYPE html>
<html lang=en>
<head>
<meta charset=UTF-8>
<meta name=viewport content="width=device-width,initial-scale=1,maximum-scale=1">
<title>CLIP.AI - AI Stream Clipping</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
:root{--bg:#0a0c0f;--bg2:#0f1318;--bg3:#151a22;--border:#1e2733;--dim:#2a3444;--muted:#4a5a6e;--text:#c8d8e8;--bright:#e8f4ff;--cyan:#00d4ff;--green:#00ff88;--yellow:#ffcc00;}
*{margin:0;padding:0;box-sizing:border-box}
html,body{max-width:100%;overflow-x:hidden}
body{background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;font-size:14px;line-height:1.6;min-height:100vh}
.w{max-width:820px;margin:0 auto;padding:0 16px}
header{border-bottom:1px solid var(--border);padding:14px 0}
.tb{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
.logo{font-size:11px;color:var(--muted);letter-spacing:.12em}
.logo span{color:var(--cyan)}
.badge{font-size:10px;padding:3px 10px;border:1px solid var(--yellow);color:var(--yellow);white-space:nowrap}
.banner{padding:36px 0 24px;text-align:center;overflow:hidden}
.ascii{font-size:clamp(6px,1.8vw,12px);line-height:1.2;color:var(--cyan);white-space:pre;text-shadow:0 0 20px rgba(0,212,255,.4);display:block;overflow:hidden}
.tag{margin-top:14px;color:var(--muted);font-size:11px;padding:0 8px}
.tag em{color:var(--green);font-style:normal}
.term{background:var(--bg2);border:1px solid var(--border);margin:0 0 32px;overflow:hidden}
.tbar{background:var(--bg3);border-bottom:1px solid var(--border);padding:8px 14px;display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted)}
.dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.tbody{padding:14px 16px;min-height:200px;font-size:11px;overflow:hidden}
.ln{margin-bottom:2px;word-break:break-word;overflow-wrap:anywhere}
.cur{display:inline-block;width:7px;height:12px;background:var(--cyan);vertical-align:middle;animation:bl 1s step-end infinite}
@keyframes bl{50%{opacity:0}}
.sec{font-size:10px;letter-spacing:.18em;color:var(--muted);text-transform:uppercase;margin-bottom:12px}
.sec::before{content:"// ";color:var(--dim)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:32px}
.card{background:var(--bg2);padding:16px;transition:background .15s}
.card:hover{background:var(--bg3)}
.ci{font-size:10px;color:var(--cyan);letter-spacing:.12em;margin-bottom:6px}
.ct{color:var(--bright);font-size:13px;font-weight:700;margin-bottom:4px}
.cd{color:var(--muted);font-size:12px;line-height:1.6}
.coin{border:1px solid var(--yellow);padding:18px;margin-bottom:32px}
.ca-label{font-size:10px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:6px}
.ca-addr{font-size:11px;font-weight:700;color:var(--yellow);word-break:break-all;overflow-wrap:anywhere;line-height:1.6;padding:10px;background:var(--bg3);border:1px solid var(--dim);margin-bottom:14px}
.coin-steps{font-size:12px;color:var(--muted);line-height:2.2}
.cb{background:var(--bg2);border:1px solid var(--border);padding:10px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;gap:10px;overflow:hidden}
.cb code{color:var(--green);font-family:inherit;font-size:11px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cpb{background:transparent;border:1px solid var(--dim);color:var(--muted);font-family:inherit;font-size:10px;padding:3px 9px;cursor:pointer;flex-shrink:0;transition:all .15s;white-space:nowrap}
.cpb:hover{border-color:var(--cyan);color:var(--cyan)}
.demo{border:1px solid var(--border);margin-bottom:32px}
.dh{background:var(--bg3);border-bottom:1px solid var(--border);padding:9px 16px;font-size:11px;color:var(--muted);display:flex;justify-content:space-between;align-items:center}
.db{padding:16px}
.ir{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.fl{font-size:10px;color:var(--muted);margin-bottom:3px}
.fld{flex:1;min-width:140px}
input,select{width:100%;background:var(--bg);border:1px solid var(--dim);color:var(--bright);font-family:inherit;font-size:12px;padding:7px 10px;outline:none;-webkit-appearance:none}
input:focus,select:focus{border-color:var(--cyan)}
select option{background:var(--bg2)}
.btn{background:transparent;border:1px solid var(--cyan);color:var(--cyan);font-family:inherit;font-size:11px;padding:7px 18px;cursor:pointer;text-transform:uppercase;transition:all .15s;white-space:nowrap}
.btn:hover{background:var(--cyan);color:var(--bg)}
.log{background:var(--bg);border:1px solid var(--border);padding:12px;min-height:130px;max-height:220px;overflow-y:auto;overflow-x:hidden;font-size:11px;line-height:1.9;word-break:break-word}
.ll{opacity:0;animation:fi .2s forwards}
@keyframes fi{to{opacity:1}}
footer{border-top:1px solid var(--border);padding:18px 0;font-size:11px;color:var(--muted);text-align:center}
footer a{color:var(--cyan);text-decoration:none}
@media(max-width:480px){
  .ascii{font-size:5.5px}
  .cb code{font-size:10px}
  .grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<header><div class=w><div class=tb>
  <div class=logo>// <span>CLIP.AI</span> &middot; ai stream clipping</div>
  <div class=badge>$CLIP &middot; v1.0.0</div>
</div></div></header>

<div class=w>
<div class=banner>
<pre class=ascii> ██████╗██╗     ██╗██████╗      █████╗ ██╗
██╔════╝██║     ██║██╔══██╗    ██╔══██╗██║
██║     ██║     ██║██████╔╝    ███████║██║
██║     ██║     ██║██╔═══╝     ██╔══██║██║
╚██████╗███████╗██║██║         ██║  ██║██║
 ╚═════╝╚══════╝╚═╝╚═╝         ╚═╝  ╚═╝╚═╝</pre>
<div class=tag>ai stream clipping &middot; autopilot &amp; manual &middot; token gated by <em>$CLIP</em></div>
</div>

<div class=term>
  <div class=tbar>
    <div class=dot style=background:#ff5f57></div>
    <div class=dot style=background:#ffbd2e></div>
    <div class=dot style=background:#28ca41></div>
    <span style=margin-left:6px>bash &mdash; clipai</span>
  </div>
  <div class=tbody id=term></div>
</div>

<div class=sec>features</div>
<div class=grid>
  <div class=card><div class=ci>[ AI ]</div><div class=ct>Autopilot</div><div class=cd>Claude AI + Whisper watch the stream and auto-clip viral moments.</div></div>
  <div class=card><div class=ci>[ # ]</div><div class=ct>Keyword Triggers</div><div class=cd>Set trigger words. Auto-clip when they hit chat or audio.</div></div>
  <div class=card><div class=ci>[ ✦ ]</div><div class=ct>Prompt Clipping</div><div class=cd>Tell it what you want. Funny fails, clutch plays, hype moments.</div></div>
  <div class=card><div class=ci>[ ▶ ]</div><div class=ct>Manual Mode</div><div class=cd>Full CLI control. Clip exact timestamps, label and export fast.</div></div>
  <div class=card><div class=ci>[ $ ]</div><div class=ct>$CLIP Token Gate</div><div class=cd>Hold $CLIP on Solana to unlock. Verified via RPC every session.</div></div>
  <div class=card><div class=ci>[ ⚡ ]</div><div class=ct>Multi-platform</div><div class=cd>Twitch &middot; YouTube &middot; Kick &middot; PumpFun &middot; Rumble &middot; TikTok Live</div></div>
</div>

<div class=sec>interactive demo</div>
<div class=demo>
  <div class=dh><span>// CLIP.AI SIMULATOR</span><span style=color:#00ff88;font-size:10px>&#9679; LIVE</span></div>
  <div class=db>
    <div class=ir>
      <div class=fld><div class=fl>// stream url</div><input id=url value=twitch.tv/xqc></div>
      <div class=fld style=max-width:120px><div class=fl>// mode</div>
        <select id=mode><option value=autopilot>autopilot</option><option value=manual>manual</option></select>
      </div>
    </div>
    <div class=ir>
      <div class=fld><div class=fl>// ai prompt</div><input id=prompt placeholder="funny moments, clutch plays..."></div>
      <div class=fld><div class=fl>// keywords</div><input id=kw placeholder="clip that, lets go"></div>
    </div>
    <div class=ir><button class=btn onclick=runDemo()>&#9654; RUN DEMO</button></div>
    <div class=log id=log><span style=color:var(--muted)>// click RUN DEMO to simulate</span></div>
  </div>
</div>

<div class=sec>$clip token &middot; solana</div>
<div class=coin>
  <div class=ca-label>contract address</div>
  <div class=ca-addr>AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump</div>
  <div class=coin-steps>
    <span style=color:var(--cyan)>01.</span> Buy $CLIP on <a href=https://pump.fun/coin/AgPcsPV2X1J4beYTGpc55WgibPuJcJwqWiXvHn5pump style=color:var(--yellow)>pump.fun</a><br>
    <span style=color:var(--cyan)>02.</span> <code style=color:var(--green)>clipai config --wallet YOUR_WALLET</code><br>
    <span style=color:var(--cyan)>03.</span> Balance verified via Solana RPC on every launch<br>
    <span style=color:var(--cyan)>04.</span> Clip everything
  </div>
</div>

<div class=sec>install</div>
<div class=cb><code>git clone https://github.com/itsKazgar/clipai</code><button class=cpb onclick="cpy(this,'git clone https://github.com/itsKazgar/clipai')">copy</button></div>
<div class=cb><code>pip install -r requirements.txt</code><button class=cpb onclick="cpy(this,'pip install -r requirements.txt')">copy</button></div>
<div class=cb><code>python src/clipai.py watch twitch.tv/streamer --autopilot --demo</code><button class=cpb onclick="cpy(this,'python src/clipai.py watch twitch.tv/streamer --autopilot --demo')">copy</button></div>

</div>

<footer>
  CLIP.AI &middot; MIT &middot; <a href=https://github.com/itsKazgar/clipai>github.com/itsKazgar/clipai</a>
  &middot; powered by <span style=color:var(--yellow)>$CLIP</span>
</footer>

<script>
const S=[
  {d:0,h:'<span style=color:#00d4ff>$</span> <span style=color:#e8f4ff>clipai watch twitch.tv/xqc --autopilot --keywords "clip that,lets go"</span>'},
  {d:600,h:'<span style=color:#c8d8e8>&nbsp;&nbsp;[$] Checking $CLIP balance...</span>'},
  {d:1100,h:'<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] Verified: 5,000 $CLIP</span>'},
  {d:1400,h:'<span style=color:#4a5a6e>&nbsp;&nbsp;Platform &nbsp;&nbsp;&nbsp;&nbsp;</span><span style=color:#00d4ff>TWITCH</span>'},
  {d:1500,h:'<span style=color:#4a5a6e>&nbsp;&nbsp;Mode &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span><span style=color:#ffcc00>AUTOPILOT</span>'},
  {d:1600,h:'<span style=color:#4a5a6e>&nbsp;&nbsp;Keywords &nbsp;&nbsp;&nbsp;</span><span style=color:#00ff88>clip that, lets go</span>'},
  {d:1900,h:'<span style=color:#c8d8e8>&nbsp;&nbsp;[>] Connecting: twitch.tv/xqc</span>'},
  {d:2300,h:'<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] Buffering stream...</span>'},
  {d:2600,h:'<span style=color:#00d4ff>&nbsp;&nbsp;[AI] Whisper + Autopilot active...</span>'},
  {d:3400,h:'<span style=color:#ffcc00>&nbsp;&nbsp;[!] Keyword: clip that</span>'},
  {d:3700,h:'<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] clip_clip_that.mp4 saved</span>'},
  {d:5000,h:'<span style=color:#00d4ff>&nbsp;&nbsp;[AI] Score 10/10 &mdash; clutch_play</span>'},
  {d:5300,h:'<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] clip_clutch_play.mp4 saved</span>'},
  {d:6800,h:'<span style=color:#00d4ff>&nbsp;&nbsp;[AI] Score 9/10 &mdash; hype_moment</span>'},
  {d:7100,h:'<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] clip_hype_moment.mp4 saved</span>'},
  {d:7600,h:'<span style=color:#00d4ff>&nbsp;&nbsp;[&#10003;] Done &middot; 3 clips &middot; $CLIP verified</span>'},
  {d:7900,h:'<span style=color:#00d4ff>$</span> <span class=cur></span>'},
];
function runTerm(){
  const t=document.getElementById('term');t.innerHTML='';
  S.forEach(s=>setTimeout(()=>{const d=document.createElement('div');d.className='ln';d.innerHTML=s.h;t.appendChild(d);t.scrollTop=t.scrollHeight;},s.d));
}
runTerm();setInterval(runTerm,10000);

let busy=false;
function runDemo(){
  if(busy)return;busy=true;
  const log=document.getElementById('log');log.innerHTML='';
  const url=document.getElementById('url').value||'twitch.tv/streamer';
  const mode=document.getElementById('mode').value;
  const prompt=document.getElementById('prompt').value;
  const kw=document.getElementById('kw').value;
  let plat='UNKNOWN';
  for(const p of['twitch','youtube','kick','pumpfun','rumble','tiktok'])if(url.includes(p)){plat=p.toUpperCase();break;}
  const lines=[
    [`<span style=color:#00d4ff>$</span> <span style=color:#e8f4ff>clipai watch ${url} --${mode}</span>`,0],
    [`<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] $CLIP verified</span>`,600],
    [`<span style=color:#4a5a6e>&nbsp;&nbsp;Platform &nbsp;&nbsp;&nbsp;&nbsp;</span><span style=color:#00d4ff>${plat}</span>`,900],
    [`<span style=color:#4a5a6e>&nbsp;&nbsp;Mode &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span><span style=color:#ffcc00>${mode.toUpperCase()}</span>`,1000],
  ];
  if(prompt)lines.push([`<span style=color:#4a5a6e>&nbsp;&nbsp;Prompt &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span><span style=color:#00ff88>${prompt}</span>`,1100]);
  if(kw)lines.push([`<span style=color:#4a5a6e>&nbsp;&nbsp;Keywords &nbsp;&nbsp;&nbsp;</span><span style=color:#00ff88>${kw}</span>`,1150]);
  lines.push(
    [`<span style=color:#c8d8e8>&nbsp;&nbsp;[>] Connecting: ${url}</span>`,1400],
    [`<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] Buffering...</span>`,1800],
    [`<span style=color:#00d4ff>&nbsp;&nbsp;[AI] Whisper + Autopilot active...</span>`,2100],
  );
  let t=2400;
  (kw?kw.split(','):[]).forEach((k,i)=>{
    t+=900+i*400;
    lines.push([`<span style=color:#ffcc00>&nbsp;&nbsp;[!] Keyword: ${k.trim()}</span>`,t]);
    t+=300;
    lines.push([`<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] clip_${k.trim().replace(/ /g,'_')}.mp4 saved</span>`,t]);
  });
  [['clutch_play',10],['hype_moment',9],['funny_fail',8]].forEach(([l,s])=>{
    t+=1400;
    lines.push([`<span style=color:#00d4ff>&nbsp;&nbsp;[AI] Score ${s}/10 &mdash; ${l}</span>`,t]);
    t+=300;
    lines.push([`<span style=color:#00ff88>&nbsp;&nbsp;[&#10003;] clip_${l}.mp4 saved</span>`,t]);
  });
  t+=400;
  lines.push([`<span style=color:#00d4ff>&nbsp;&nbsp;[&#10003;] Done &middot; $CLIP verified</span>`,t]);
  lines.forEach(([h,d])=>setTimeout(()=>{
    const el=document.createElement('div');el.className='ll';el.innerHTML=h;log.appendChild(el);log.scrollTop=log.scrollHeight;
  },d));
  setTimeout(()=>{busy=false;},t+600);
}
function cpy(btn,text){
  navigator.clipboard.writeText(text).then(()=>{
    btn.textContent='copied!';
    setTimeout(()=>{btn.textContent='copy';},2000);
  });
}
</script>
</body>
</html>"""

pathlib.Path('demo').mkdir(exist_ok=True)
pathlib.Path('demo/index.html').write_text(html)
pathlib.Path('index.html').write_text(html)
print('done! demo/index.html and index.html updated')
