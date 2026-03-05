"""
╔══════════════════════════════════════════════════════════════╗
║       🔥  SMART EMAIL CLEANER — WEB INTERFACE  🔥            ║
║       Run: py -3.11 app.py                                 ║
║       Then open: http://localhost:5000             ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import io
import zipfile
from datetime import datetime
from flask import Flask, request, render_template_string, send_file, jsonify

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EMAIL DOMAINS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOTMAIL = ['@hotmail.com','@hotmail.co.uk','@hotmail.fr','@hotmail.de',
           '@hotmail.it','@hotmail.es','@hotmail.com.br','@hotmail.com.ar']
LIVE    = ['@live.com','@live.co.uk','@live.fr','@live.de','@live.com.ar']
OUTLOOK = ['@outlook.com','@outlook.fr','@outlook.de','@outlook.es',
           '@outlook.com.br','@outlook.com.ar','@outlook.in']
MSN     = ['@msn.com']
GMAIL   = ['@gmail.com']

def get_category(email):
    e = email.lower()
    if any(e.endswith(d) for d in GMAIL):   return 'gmail'
    if any(e.endswith(d) for d in HOTMAIL): return 'hotmail'
    if any(e.endswith(d) for d in LIVE):    return 'live'
    if any(e.endswith(d) for d in OUTLOOK): return 'outlook'
    if any(e.endswith(d) for d in MSN):     return 'msn'
    return 'other'

def parse_line(line):
    line = line.strip()
    if not line or line.startswith('#'): return None
    for sep in [':', '|', ' ']:
        parts = line.split(sep, 1)
        if len(parts) == 2:
            email, password = parts[0].strip(), parts[1].strip()
            if '@' in email and '.' in email and password:
                return email, password
    return None

def clean_accounts(text):
    lines = text.splitlines()
    seen  = set()
    cats  = {k: [] for k in ['gmail','hotmail','live','outlook','msn','other']}
    dups  = 0
    inv   = 0

    for line in lines:
        parsed = parse_line(line)
        if not parsed:
            inv += 1
            continue
        email, password = parsed
        key = email.lower()
        if key in seen:
            dups += 1
            continue
        seen.add(key)
        cats[get_category(email)].append(f"{email}:{password}")

    return cats, dups, inv

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HTML TEMPLATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HTML = '''<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🔥 Smart Email Cleaner</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:      #040810;
    --surface: #080f1a;
    --card:    #0b1623;
    --border:  #0f2a40;
    --cyan:    #00f5ff;
    --green:   #00ff88;
    --orange:  #ff6b00;
    --red:     #ff2d55;
    --yellow:  #ffd60a;
    --blue:    #2979ff;
    --purple:  #bf5af2;
    --text:    #c8e0f0;
    --dim:     #4a6a80;
  }
  * { margin:0; padding:0; box-sizing:border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Rajdhani', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Grid background */
  body::before {
    content:'';
    position:fixed; inset:0;
    background-image:
      linear-gradient(rgba(0,245,255,.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,245,255,.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events:none;
    z-index:0;
  }

  .wrap { position:relative; z-index:1; max-width:900px; margin:0 auto; padding:30px 20px; }

  /* HEADER */
  .header { text-align:center; margin-bottom:40px; }
  .header .logo {
    font-family:'Share Tech Mono', monospace;
    font-size:clamp(22px,5vw,42px);
    color: var(--cyan);
    text-shadow: 0 0 20px rgba(0,245,255,.6), 0 0 60px rgba(0,245,255,.3);
    letter-spacing:3px;
    animation: flicker 4s infinite;
  }
  @keyframes flicker {
    0%,95%,100%{opacity:1} 96%{opacity:.7} 97%{opacity:1} 98%{opacity:.8}
  }
  .header .sub {
    font-size:15px; color:var(--dim); margin-top:8px;
    letter-spacing:2px; text-transform:uppercase;
  }
  .header .url-badge {
    display:inline-block; margin-top:14px;
    background: rgba(0,245,255,.07);
    border:1px solid rgba(0,245,255,.25);
    border-radius:6px; padding:6px 18px;
    font-family:'Share Tech Mono',monospace;
    font-size:13px; color:var(--cyan);
  }

  /* CARDS */
  .card {
    background: var(--card);
    border:1px solid var(--border);
    border-radius:12px;
    padding:28px;
    margin-bottom:24px;
    position:relative;
    overflow:hidden;
  }
  .card::before {
    content:'';
    position:absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    opacity:.5;
  }
  .card-title {
    font-size:18px; font-weight:700;
    color:var(--cyan); letter-spacing:2px;
    text-transform:uppercase; margin-bottom:20px;
    display:flex; align-items:center; gap:10px;
  }

  /* DROP ZONE */
  .dropzone {
    border:2px dashed var(--border);
    border-radius:10px;
    padding:50px 20px;
    text-align:center;
    cursor:pointer;
    transition:all .3s;
    position:relative;
  }
  .dropzone:hover, .dropzone.drag {
    border-color:var(--cyan);
    background:rgba(0,245,255,.04);
    box-shadow: 0 0 30px rgba(0,245,255,.1);
  }
  .dropzone .icon { font-size:48px; margin-bottom:14px; display:block; }
  .dropzone .drop-title {
    font-size:20px; font-weight:700;
    color:var(--text); margin-bottom:8px;
  }
  .dropzone .drop-sub { font-size:14px; color:var(--dim); }
  .dropzone input[type=file] {
    position:absolute; inset:0; opacity:0; cursor:pointer; width:100%; height:100%;
  }
  .file-chosen {
    margin-top:14px; font-size:14px; color:var(--green);
    font-family:'Share Tech Mono',monospace;
    display:none;
  }

  /* BUTTON */
  .btn {
    width:100%; padding:16px;
    background: linear-gradient(135deg, #00b8cc, #00f5ff);
    color:#000; font-family:'Rajdhani',sans-serif;
    font-size:18px; font-weight:700;
    letter-spacing:3px; text-transform:uppercase;
    border:none; border-radius:8px;
    cursor:pointer; margin-top:18px;
    transition:all .3s;
    position:relative; overflow:hidden;
  }
  .btn:hover {
    box-shadow:0 0 30px rgba(0,245,255,.5);
    transform:translateY(-2px);
  }
  .btn:active { transform:translateY(0); }
  .btn:disabled { opacity:.4; cursor:not-allowed; transform:none; }
  .btn .btn-icon { margin-right:8px; }

  /* PROGRESS */
  #progress-wrap { display:none; margin-top:20px; }
  .progress-bar-bg {
    background:var(--border); border-radius:99px; height:8px; overflow:hidden;
  }
  .progress-bar-fill {
    height:100%; border-radius:99px;
    background:linear-gradient(90deg,var(--cyan),var(--green));
    width:0%; transition:width .4s ease;
    box-shadow:0 0 10px rgba(0,245,255,.5);
  }
  .progress-label {
    font-size:13px; color:var(--dim);
    font-family:'Share Tech Mono',monospace;
    margin-top:8px; text-align:center;
  }

  /* STATS */
  #stats-wrap { display:none; }
  .stats-grid {
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(130px,1fr));
    gap:14px; margin-bottom:20px;
  }
  .stat-item {
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:10px; padding:16px 12px;
    text-align:center;
    transition:transform .2s;
  }
  .stat-item:hover { transform:translateY(-3px); }
  .stat-num {
    font-family:'Share Tech Mono',monospace;
    font-size:28px; font-weight:700;
    display:block; margin-bottom:4px;
  }
  .stat-label { font-size:12px; color:var(--dim); text-transform:uppercase; letter-spacing:1px; }

  /* BAR CHART */
  .chart { margin-bottom:22px; }
  .chart-row { margin-bottom:12px; }
  .chart-label {
    display:flex; justify-content:space-between;
    font-size:13px; margin-bottom:5px;
  }
  .chart-name { color:var(--text); font-weight:600; }
  .chart-count { font-family:'Share Tech Mono',monospace; }
  .chart-bar-bg { background:var(--border); border-radius:99px; height:10px; overflow:hidden; }
  .chart-bar-fill { height:100%; border-radius:99px; transition:width 1s ease; width:0%; }

  /* DOWNLOAD BTNS */
  .dl-grid {
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(160px,1fr));
    gap:10px;
  }
  .dl-btn {
    display:flex; align-items:center; gap:8px;
    padding:12px 16px;
    border-radius:8px; border:1px solid;
    font-family:'Rajdhani',sans-serif;
    font-size:14px; font-weight:600;
    cursor:pointer; text-decoration:none;
    transition:all .25s; background:transparent;
    letter-spacing:1px;
  }
  .dl-btn:hover { transform:translateY(-2px); }
  .dl-all {
    width:100%; justify-content:center;
    padding:14px; font-size:16px;
    letter-spacing:2px; margin-bottom:12px;
    border-color:var(--yellow);
    color:var(--yellow);
  }
  .dl-all:hover { background:rgba(255,214,10,.08); box-shadow:0 0 20px rgba(255,214,10,.2); }

  /* COLORS */
  .c-cyan   { color:var(--cyan); }
  .c-green  { color:var(--green); }
  .c-red    { color:var(--red); }
  .c-orange { color:var(--orange); }
  .c-blue   { color:var(--blue); }
  .c-yellow { color:var(--yellow); }
  .c-purple { color:var(--purple); }
  .c-dim    { color:var(--dim); }

  .tag {
    display:inline-block; padding:2px 10px;
    border-radius:99px; font-size:11px;
    font-weight:700; letter-spacing:1px;
    text-transform:uppercase;
  }
  .tag-green { background:rgba(0,255,136,.1); color:var(--green); border:1px solid rgba(0,255,136,.3); }
  .tag-red   { background:rgba(255,45,85,.1); color:var(--red); border:1px solid rgba(255,45,85,.3); }

  /* SCAN LINES */
  .scanlines {
    position:fixed; inset:0; pointer-events:none; z-index:999;
    background:repeating-linear-gradient(
      0deg, transparent, transparent 2px,
      rgba(0,0,0,.08) 2px, rgba(0,0,0,.08) 4px
    );
  }

  /* FOOTER */
  .footer {
    text-align:center; margin-top:40px;
    font-size:12px; color:var(--dim);
    font-family:'Share Tech Mono',monospace;
    letter-spacing:2px;
  }

  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .pulse { animation:pulse 1.5s infinite; }
</style>
</head>
<body>
<div class="scanlines"></div>
<div class="wrap">

  <!-- HEADER -->
  <div class="header">
    <div class="logo">⚡ EMAIL ACCOUNT CLEANER</div>
    <div class="sub">Duplicate Remover · Auto Separator · Smart Filter</div>
    <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:14px;">
      <div class="url-badge">🌐 http://localhost:5000</div>
      <a href="https://t.me/ZeroShell_Store" target="_blank" style="display:inline-block;background:rgba(0,170,255,.1);border:1px solid rgba(0,170,255,.35);border-radius:6px;padding:6px 18px;font-family:Share Tech Mono,monospace;font-size:13px;color:#00aaff;text-decoration:none;">✈️ @ZeroShell_Store</a>
    </div>
  </div>

  <!-- UPLOAD CARD -->
  <div class="card">
    <div class="card-title">📤 Upload Your File</div>
    <form id="uploadForm">
      <div class="dropzone" id="dropzone">
        <input type="file" id="fileInput" name="file" accept=".txt">
        <span class="icon">📂</span>
        <div class="drop-title">Drop your .txt file here</div>
        <div class="drop-sub">Or click to browse files</div>
        <div class="file-chosen" id="fileChosen">✅ ✅ File selected: <span id="fileName"></span></div>
      </div>

      <div id="progress-wrap">
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" id="progressBar"></div>
        </div>
        <div class="progress-label" id="progressLabel">⏳ Processing...</div>
      </div>

      <button type="submit" class="btn" id="cleanBtn">
        <span class="btn-icon">🔥</span> CLEAN & SEPARATE
      </button>
    </form>
  </div>

  <!-- STATS CARD -->
  <div class="card" id="stats-wrap">
    <div class="card-title">📊 Result Statistics</div>

    <!-- Number cards -->
    <div class="stats-grid" id="statsGrid"></div>

    <!-- Bar chart -->
    <div class="chart" id="chartWrap"></div>

    <!-- Downloads -->
    <div class="card-title" style="margin-top:10px">💾 Download Files</div>
    <a class="dl-btn dl-all" id="dlAll" href="#" download>
      📦 Download All Together (ZIP)
    </a>
    <div class="dl-grid" id="dlGrid"></div>
  </div>

  <!-- TELEGRAM CARD -->
  <div class="card" style="text-align:center; border-color:rgba(0,136,204,.4);">
    <div style="font-size:36px; margin-bottom:10px;">✈️</div>
    <div style="font-family:'Share Tech Mono',monospace; font-size:22px; color:#00aaff;
                text-shadow:0 0 20px rgba(0,170,255,.6); margin-bottom:8px; letter-spacing:2px;">
      ZeroShell Store
    </div>
    <div style="color:#4a6a80; font-size:13px; letter-spacing:2px; margin-bottom:18px;">
      TOOLS · SERVICES · SUPPORT
    </div>
    <a href="https://t.me/ZeroShell_Store" target="_blank"
       style="display:inline-flex; align-items:center; gap:10px;
              background:linear-gradient(135deg,#0077b5,#00aaff);
              color:#fff; text-decoration:none; padding:14px 32px;
              border-radius:8px; font-family:'Rajdhani',sans-serif;
              font-size:17px; font-weight:700; letter-spacing:2px;
              transition:all .3s; box-shadow:0 0 20px rgba(0,170,255,.3);"
       onmouseover="this.style.boxShadow='0 0 40px rgba(0,170,255,.6)';this.style.transform='translateY(-2px)'"
       onmouseout="this.style.boxShadow='0 0 20px rgba(0,170,255,.3)';this.style.transform='translateY(0)'">
      ✈️ &nbsp;JOIN TELEGRAM
    </a>
    <div style="margin-top:14px; font-size:13px; color:#4a6a80;">
      💬 DM for support &nbsp;·&nbsp;
      <a href="https://t.me/ZeroShell_Store" target="_blank"
         style="color:#00aaff; text-decoration:none;">@ZeroShell_Store</a>
    </div>
  </div>

  <div class="footer">SMART EMAIL CLEANER v2.0 · PYTHON + FLASK · localhost:5000<br>
    <span style="color:#00aaff;">✈️ t.me/ZeroShell_Store</span>
  </div>
</div>

<script>
const COLORS = {
  gmail:   {color:'#00ff88', bg:'rgba(0,255,136,.12)', border:'rgba(0,255,136,.3)', icon:'📧'},
  hotmail: {color:'#ff2d55', bg:'rgba(255,45,85,.12)',  border:'rgba(255,45,85,.3)',  icon:'🔴'},
  outlook: {color:'#2979ff', bg:'rgba(41,121,255,.12)', border:'rgba(41,121,255,.3)', icon:'🔵'},
  live:    {color:'#ffd60a', bg:'rgba(255,214,10,.12)', border:'rgba(255,214,10,.3)', icon:'🟡'},
  msn:     {color:'#bf5af2', bg:'rgba(191,90,242,.12)', border:'rgba(191,90,242,.3)', icon:'🟣'},
  other:   {color:'#8899aa', bg:'rgba(136,153,170,.12)',border:'rgba(136,153,170,.3)',icon:'⚪'},
};

// Drag & drop
const dz = document.getElementById('dropzone');
dz.addEventListener('dragover', e=>{e.preventDefault();dz.classList.add('drag');});
dz.addEventListener('dragleave', ()=>dz.classList.remove('drag'));
dz.addEventListener('drop', e=>{
  e.preventDefault(); dz.classList.remove('drag');
  const f = e.dataTransfer.files[0];
  if(f){ document.getElementById('fileInput').files = e.dataTransfer.files; showFile(f.name); }
});
document.getElementById('fileInput').addEventListener('change', e=>{
  if(e.target.files[0]) showFile(e.target.files[0].name);
});
function showFile(name){
  document.getElementById('fileChosen').style.display='block';
  document.getElementById('fileName').textContent = name;
}

// FORM SUBMIT
document.getElementById('uploadForm').addEventListener('submit', async e=>{
  e.preventDefault();
  const fi = document.getElementById('fileInput');
  if(!fi.files.length){ alert('⚠️ Please select a .txt file first!'); return; }

  const btn = document.getElementById('cleanBtn');
  btn.disabled = true; btn.innerHTML = '<span class="pulse">⏳</span> Processing...';

  const pw = document.getElementById('progress-wrap');
  const pb = document.getElementById('progressBar');
  const pl = document.getElementById('progressLabel');
  pw.style.display='block'; pb.style.width='0%';

  // Fake progress animation
  let pct=0;
  const iv = setInterval(()=>{
    pct = Math.min(pct + Math.random()*8, 85);
    pb.style.width = pct+'%';
    pl.textContent = `⚙️ Analyzing... ${Math.round(pct)}%`;
  }, 120);

  const fd = new FormData();
  fd.append('file', fi.files[0]);

  try {
    const res  = await fetch('/clean', {method:'POST', body:fd});
    const data = await res.json();
    clearInterval(iv);

    if(data.error){ alert('❌ Error: '+data.error); btn.disabled=false; btn.innerHTML='<span>🔥</span> CLEAN & SEPARATE'; return; }

    pb.style.width='100%'; pl.textContent='✅ Done!';
    setTimeout(()=>{ pw.style.display='none'; showStats(data); }, 600);

  } catch(err){
    clearInterval(iv);
    alert('❌ Error: '+err.message);
  }
  btn.disabled=false; btn.innerHTML='<span class="btn-icon">🔥</span> CLEAN & SEPARATE';
});

function showStats(data){
  const sw = document.getElementById('stats-wrap');
  sw.style.display='block';
  sw.scrollIntoView({behavior:'smooth', block:'start'});

  const cats = data.categories;
  const total = Object.values(cats).reduce((a,b)=>a+b,0);

  // Number stat cards
  const sg = document.getElementById('statsGrid');
  sg.innerHTML = `
    <div class="stat-item">
      <span class="stat-num c-green">${total}</span>
      <span class="stat-label">✅ Total Unique</span>
    </div>
    <div class="stat-item">
      <span class="stat-num c-red">${data.duplicates}</span>
      <span class="stat-label">❌ Duplicates</span>
    </div>
    <div class="stat-item">
      <span class="stat-num c-cyan">${data.total_lines}</span>
      <span class="stat-label">📄 Total Lines</span>
    </div>
    <div class="stat-item">
      <span class="stat-num c-dim">${data.invalid}</span>
      <span class="stat-label">🗑️ Invalid</span>
    </div>
  `;

  // Bar chart
  const cw = document.getElementById('chartWrap');
  const maxVal = Math.max(...Object.values(cats), 1);
  const order = ['gmail','hotmail','outlook','live','msn','other'];
  cw.innerHTML = order.map(k => {
    const c = COLORS[k];
    const v = cats[k] || 0;
    const pct = (v/maxVal*100).toFixed(1);
    return `
      <div class="chart-row">
        <div class="chart-label">
          <span class="chart-name">${c.icon} ${k.toUpperCase()}</span>
          <span class="chart-count" style="color:${c.color}">${v} accounts</span>
        </div>
        <div class="chart-bar-bg">
          <div class="chart-bar-fill" style="background:${c.color};box-shadow:0 0 8px ${c.color}40"
               data-width="${pct}%"></div>
        </div>
      </div>`;
  }).join('');

  // Animate bars
  setTimeout(()=>{
    document.querySelectorAll('.chart-bar-fill').forEach(el=>{
      el.style.width = el.dataset.width;
    });
  }, 100);

  // Download buttons
  const dlg = document.getElementById('dlGrid');
  const dlAll = document.getElementById('dlAll');
  dlAll.href = '/download/all?session='+data.session;

  dlg.innerHTML = order.filter(k=>cats[k]>0).map(k=>{
    const c = COLORS[k];
    return `<a class="dl-btn" href="/download/${k}?session=${data.session}" download
              style="border-color:${c.border};color:${c.color};background:${c.bg}">
              ${c.icon} ${k.toUpperCase()} <span style="opacity:.6;font-size:12px">(${cats[k]})</span>
            </a>`;
  }).join('');
}
</script>
</body>
</html>'''

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  IN-MEMORY SESSION STORE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
sessions = {}

def make_file_content(accounts, title, domain_info):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        f"# ╔══════════════════════════════════════════════╗",
        f"# ║  🔥  {title:<40}║",
        f"# ║  📅  Date  : {ts:<32}║",
        f"# ║  📦  Domain: {domain_info:<32}║",
        f"# ║  ✅  Total : {str(len(accounts)):<32}║",
        f"# ╚══════════════════════════════════════════════╝",
        "",
    ]
    return "\n".join(lines + accounts)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/clean', methods=['POST'])
def clean():
    if 'file' not in request.files:
        return jsonify({'error': 'File not found'}), 400

    f = request.files['file']
    if not f.filename.endswith('.txt'):
        return jsonify({'error': 'Only .txt files allowed'}), 400

    text = f.read().decode('utf-8', errors='ignore')
    total_lines = len([l for l in text.splitlines() if l.strip()])
    cats, dups, inv = clean_accounts(text)

    sid = datetime.now().strftime('%Y%m%d%H%M%S%f')
    sessions[sid] = cats

    return jsonify({
        'session':     sid,
        'categories':  {k: len(v) for k, v in cats.items()},
        'duplicates':  dups,
        'invalid':     inv,
        'total_lines': total_lines + dups + inv,
    })

@app.route('/download/<cat>')
def download(cat):
    sid = request.args.get('session','')
    if sid not in sessions:
        return "Session expired", 404

    cats = sessions[sid]
    cfg = {
        'gmail':   ("GMAIL ACCOUNTS - UNIQUE",   "@gmail.com"),
        'hotmail': ("HOTMAIL ACCOUNTS - UNIQUE",  "@hotmail.com and variants"),
        'outlook': ("OUTLOOK ACCOUNTS - UNIQUE",  "@outlook.com and variants"),
        'live':    ("LIVE ACCOUNTS - UNIQUE",      "@live.com and variants"),
        'msn':     ("MSN ACCOUNTS - UNIQUE",       "@msn.com"),
        'other':   ("OTHER ACCOUNTS - UNIQUE",     "Mixed domains"),
    }

    if cat == 'all':
        # ZIP all files
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for k, (title, domain) in cfg.items():
                if cats.get(k):
                    content = make_file_content(cats[k], title, domain)
                    zf.writestr(f"{k}_unique.txt", content)
            # ALL combined
            all_accs = []
            for k in ['gmail','hotmail','outlook','live','msn','other']:
                all_accs.extend(cats.get(k,[]))
            content = make_file_content(all_accs, "ALL ACCOUNTS - UNIQUE", "All domains")
            zf.writestr("ALL_unique.txt", content)
        buf.seek(0)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(buf, as_attachment=True,
                         download_name=f"cleaned_accounts_{ts}.zip",
                         mimetype='application/zip')

    if cat not in cfg or not cats.get(cat):
        return "No data", 404

    title, domain = cfg[cat]
    content = make_file_content(cats[cat], title, domain)
    buf = io.BytesIO(content.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f"{cat}_unique.txt",
                     mimetype='text/plain')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == '__main__':
    print("\n" + "═"*55)
    print("  🔥  SMART EMAIL CLEANER — WEB SERVER")
    print("═"*55)
    print("  ✅  Server starting...")
    print("  🌐  Open browser: http://localhost:5000")
    print("  ⛔  Stop server: Ctrl+C")
    print("═"*55 + "\n")
    app.run(debug=False, host='0.0.0.0', port=5000)
