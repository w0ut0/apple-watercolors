"""Build data/slideshow.html from data/paintings.jsonl for quick browsing."""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
KEYS = ["pom_id", "cultivar", "scientific_name", "origin", "description", "date",
        "artist", "license", "categories", "commons_url", "usda_url",
        "original_url", "original_size", "thumb_url", "image_file"]

records = []
with open(DATA / "paintings.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        d = {k: r.get(k) for k in KEYS}
        d["local"] = bool(r.get("image_file")) and (DATA / r["image_file"]).exists()
        records.append(d)
records.sort(key=lambda r: r.get("pom_id") or "")

payload = json.dumps(records, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>USDA Pomological Watercolors – Apple Slideshow</title>
<meta name="description" content="Browse USDA pomological apple watercolors with descriptions and metadata.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#120d0c;--panel:rgba(32,22,20,.72);--line:rgba(255,220,200,.12);--text:#f4ebe4;--muted:#b9a79c;--accent:#e2574c;--accent2:#f2b84b}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:Inter,system-ui,sans-serif;color:var(--text);background:var(--bg);overflow:hidden}
#bg{position:fixed;inset:-40px;background-size:cover;background-position:center;filter:blur(40px) saturate(1.3) brightness(.35);transition:background-image .6s;z-index:0}
.app{position:relative;z-index:1;display:grid;grid-template-rows:auto 1fr auto;height:100vh}
header{display:flex;align-items:center;gap:16px;padding:14px 24px;border-bottom:1px solid var(--line);background:rgba(18,13,12,.55);backdrop-filter:blur(12px)}
h1{font-family:Fraunces,serif;font-size:1.25rem;font-weight:700;white-space:nowrap}
h1 span{color:var(--accent)}
.search{flex:1;max-width:420px;margin-left:auto;position:relative}
.search input{width:100%;padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--text);font:inherit;outline:none;transition:border-color .2s,background .2s}
.search input:focus{border-color:var(--accent);background:rgba(255,255,255,.1)}
.count{color:var(--muted);font-size:.85rem;white-space:nowrap}
main{display:grid;grid-template-columns:1fr 400px;min-height:0}
.stage{position:relative;display:flex;align-items:center;justify-content:center;padding:24px;min-height:0}
.stage img{max-width:100%;max-height:100%;object-fit:contain;border-radius:6px;box-shadow:0 30px 80px rgba(0,0,0,.6);opacity:0;transform:scale(.98);transition:opacity .35s,transform .35s;cursor:zoom-in}
.stage img.show{opacity:1;transform:none}
.nav{position:absolute;top:50%;transform:translateY(-50%);width:52px;height:52px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:1.4rem;cursor:pointer;backdrop-filter:blur(8px);transition:background .2s,transform .2s}
.nav:hover{background:var(--accent);transform:translateY(-50%) scale(1.08)}
#prev{left:20px}#next{right:20px}
aside{border-left:1px solid var(--line);background:var(--panel);backdrop-filter:blur(16px);padding:28px;overflow-y:auto}
.id{font-size:.75rem;letter-spacing:.12em;color:var(--accent2);font-weight:600}
h2{font-family:Fraunces,serif;font-size:2rem;line-height:1.1;margin:6px 0 4px}
.sci{font-style:italic;color:var(--muted);margin-bottom:18px}
.desc{line-height:1.6;margin-bottom:22px;color:#e8dcd3}
dl{display:grid;grid-template-columns:100px 1fr;gap:10px 12px;font-size:.9rem;margin-bottom:22px}
dt{color:var(--muted)}dd{word-break:break-word}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:22px}
.tag{font-size:.75rem;padding:4px 10px;border-radius:999px;background:rgba(226,87,76,.14);border:1px solid rgba(226,87,76,.3);cursor:pointer;transition:background .2s}
.tag:hover{background:rgba(226,87,76,.35)}
.links{display:flex;flex-wrap:wrap;gap:8px}
.links a{font-size:.8rem;color:var(--text);text-decoration:none;padding:7px 12px;border-radius:8px;border:1px solid var(--line);transition:border-color .2s,color .2s}
.links a:hover{border-color:var(--accent2);color:var(--accent2)}
footer{display:flex;align-items:center;gap:16px;padding:12px 24px;border-top:1px solid var(--line);background:rgba(18,13,12,.6);backdrop-filter:blur(12px)}
footer button{padding:8px 16px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--text);font:inherit;font-size:.85rem;cursor:pointer;transition:background .2s}
footer button:hover,footer button.on{background:var(--accent);border-color:var(--accent)}
input[type=range]{flex:1;accent-color:var(--accent)}
.pos{font-variant-numeric:tabular-nums;color:var(--muted);font-size:.85rem;min-width:110px;text-align:right}
.hint{color:var(--muted);font-size:.75rem}
#lightbox{position:fixed;inset:0;z-index:10;background:rgba(0,0,0,.92);display:none;align-items:center;justify-content:center;cursor:zoom-out}
#lightbox.open{display:flex}#lightbox img{max-width:96vw;max-height:96vh}
.empty{color:var(--muted)}
@media(max-width:900px){main{grid-template-columns:1fr;grid-template-rows:55vh 1fr}aside{border-left:0;border-top:1px solid var(--line)}body{overflow:auto}.hint{display:none}}
</style>
</head>
<body>
<div id="bg"></div>
<div class="app">
<header>
  <h1>🍎 Pomological <span>Watercolors</span></h1>
  <div class="search"><input id="q" type="search" placeholder="Search cultivar, artist, origin, year…  ( / )"></div>
  <div class="count" id="count"></div>
</header>
<main>
  <section class="stage">
    <button class="nav" id="prev" aria-label="Previous">‹</button>
    <img id="img" alt="">
    <button class="nav" id="next" aria-label="Next">›</button>
  </section>
  <aside id="info"></aside>
</main>
<footer>
  <button id="play">▶ Play</button>
  <button id="shuffle">⤮ Random</button>
  <input type="range" id="slider" min="0" value="0" aria-label="Position">
  <span class="pos" id="pos"></span>
  <span class="hint">← → navigate · Space play · R random · Enter zoom</span>
</footer>
</div>
<div id="lightbox"><img id="lbimg" alt=""></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const ALL = JSON.parse(document.getElementById('data').textContent);
let list = ALL, i = 0, timer = null;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const src = r => r.local ? r.image_file : (r.thumb_url || r.original_url);
const hay = r => [r.pom_id,r.cultivar,r.artist,r.origin,r.date,r.description,(r.categories||[]).join(' ')].join(' ').toLowerCase();
ALL.forEach(r => r._h = hay(r));

function render(){
  $('count').textContent = `${list.length.toLocaleString()} of ${ALL.length.toLocaleString()} paintings`;
  $('slider').max = Math.max(0, list.length - 1);
  if(!list.length){ $('img').classList.remove('show'); $('info').innerHTML='<p class="empty">No matches.</p>'; $('pos').textContent='0 / 0'; return; }
  i = (i + list.length) % list.length;
  const r = list[i], img = $('img');
  img.classList.remove('show');
  img.onload = () => img.classList.add('show');
  img.onerror = () => { if (img.src.indexOf(r.thumb_url) < 0 && r.thumb_url) img.src = r.thumb_url; };
  img.src = src(r); img.alt = `${r.cultivar} apple watercolor`;
  $('bg').style.backgroundImage = `url("${src(r)}")`;
  $('slider').value = i;
  $('pos').textContent = `${(i+1).toLocaleString()} / ${list.length.toLocaleString()}`;
  const row = (k,v) => v ? `<dt>${k}</dt><dd>${esc(v)}</dd>` : '';
  const sz = r.original_size ? `${r.original_size[0]} × ${r.original_size[1]} px` : '';
  const cats = (r.categories||[]).filter(c => !/^USDA Pomological Watercolors/.test(c));
  $('info').innerHTML = `
    <div class="id">${esc(r.pom_id)}</div>
    <h2>${esc(r.cultivar || 'Unknown cultivar')}</h2>
    <div class="sci">${esc(r.scientific_name)}</div>
    <p class="desc">${esc(r.description)}</p>
    <dl>${row('Artist', r.artist || 'Unknown')}${row('Date', r.date)}${row('Origin', r.origin)}${row('License', r.license)}${row('Original', sz)}</dl>
    ${cats.length ? `<div class="tags">${cats.map(c => `<span class="tag" data-q="${esc(c)}">${esc(c)}</span>`).join('')}</div>` : ''}
    <div class="links">
      ${r.commons_url ? `<a href="${esc(r.commons_url)}" target="_blank" rel="noopener">Wikimedia Commons ↗</a>` : ''}
      ${r.usda_url ? `<a href="${esc(r.usda_url)}" target="_blank" rel="noopener">USDA catalog ↗</a>` : ''}
      ${r.original_url ? `<a href="${esc(r.original_url)}" target="_blank" rel="noopener">Full resolution ↗</a>` : ''}
    </div>`;
  [1,-1].forEach(d => { const n = list[(i+d+list.length)%list.length]; if(n) new Image().src = src(n); });
  history.replaceState(null, '', '#' + r.pom_id);
}
const go = d => { i += d; render(); };
function filter(q){
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  const cur = list[i];
  list = terms.length ? ALL.filter(r => terms.every(t => r._h.includes(t))) : ALL;
  i = Math.max(0, list.indexOf(cur)); render();
}
function play(){
  if(timer){ clearInterval(timer); timer=null; $('play').textContent='▶ Play'; $('play').classList.remove('on'); }
  else { timer = setInterval(() => go(1), 3500); $('play').textContent='❚❚ Pause'; $('play').classList.add('on'); }
}
$('prev').onclick = () => go(-1); $('next').onclick = () => go(1);
$('play').onclick = play;
$('shuffle').onclick = () => { i = Math.floor(Math.random()*list.length); render(); };
$('slider').oninput = e => { i = +e.target.value; render(); };
let deb; $('q').oninput = e => { clearTimeout(deb); deb = setTimeout(() => filter(e.target.value), 150); };
$('info').onclick = e => { const t = e.target.closest('.tag'); if(t){ $('q').value = t.dataset.q; filter(t.dataset.q); } };
$('img').onclick = () => { const r = list[i]; $('lbimg').src = src(r); $('lightbox').classList.add('open'); };
$('lightbox').onclick = () => $('lightbox').classList.remove('open');
document.addEventListener('keydown', e => {
  if(e.target.tagName === 'INPUT'){ if(e.key==='Escape') e.target.blur(); return; }
  if(e.key==='ArrowRight') go(1);
  else if(e.key==='ArrowLeft') go(-1);
  else if(e.key===' '){ e.preventDefault(); play(); }
  else if(e.key==='r'||e.key==='R') $('shuffle').click();
  else if(e.key==='Enter') $('img').click();
  else if(e.key==='Escape') $('lightbox').classList.remove('open');
  else if(e.key==='/'){ e.preventDefault(); $('q').focus(); }
});
let tx=null; document.addEventListener('touchstart', e => tx = e.touches[0].clientX, {passive:true});
document.addEventListener('touchend', e => { if(tx===null) return; const dx = e.changedTouches[0].clientX - tx; if(Math.abs(dx)>50) go(dx<0?1:-1); tx=null; });
const h = location.hash.slice(1); if(h){ const k = ALL.findIndex(r => r.pom_id === h); if(k>=0) i = k; }
render();
</script>
</body>
</html>"""

out = DATA / "slideshow.html"
out.write_text(HTML.replace("__DATA__", payload), encoding="utf-8")
local = sum(r["local"] for r in records)
print(f"Wrote {out} with {len(records)} paintings ({local} local images)")
