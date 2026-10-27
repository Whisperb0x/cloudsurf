"""Live dashboard for CloudPass: reads the newest logs/live_*.csv that
tools/live_monitor.py writes and serves a page with the current state and
small charts of the last few minutes.

  python tools/dashboard.py [port]     then open http://localhost:8765
"""
import csv, glob, json, os, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(HERE, "logs")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
WINDOW_S = 300  # seconds of history in the charts
FIELDS = ["gs_kt", "alt_ft", "in_cloud", "cloud_pct", "camera", "ACTIVE", "SPAWNS", "FAILS",
          "DENS", "EFFECT", "TEST", "HEARTBEAT", "strobe", "beacon", "landing"]


def newest_log():
    files = glob.glob(os.path.join(LOGS, "live_*.csv"))
    return max(files, key=os.path.getmtime) if files else None


def tail_rows(path, max_bytes=4_000_000):
    """Header + the last rows of a (growing) CSV without reading all of it."""
    with open(path, newline="") as f:
        header = next(csv.reader([f.readline()]))
        size = os.path.getsize(path)
        f.seek(max(0, size - max_bytes))
        if f.tell() > 0:
            f.readline()  # drop the partial line
        rows = list(csv.reader(f))
    return header, rows


def num(v):
    try:
        x = float(v)
        return x if x == x else None
    except ValueError:
        return None


def snapshot():
    path = newest_log()
    if not path:
        return {"log": None}
    header, rows = tail_rows(path)
    idx = {h: i for i, h in enumerate(header)}
    if not rows:
        return {"log": os.path.basename(path)}
    t_end = num(rows[-1][idx["wall"]]) or 0.0
    # one point per second: frames in that second = fps, last values for the rest
    buckets = {}
    for r in rows:
        if len(r) != len(header):
            continue
        t = num(r[idx["wall"]])
        if t is None or t < t_end - WINDOW_S:
            continue
        b = buckets.setdefault(int(t), {"n": 0})
        b["n"] += 1
        for k in FIELDS:
            if k in idx:
                b[k] = num(r[idx[k]])
    secs = sorted(buckets)[:-1]  # the last second is still filling
    series = {"t": [s - int(t_end) for s in secs], "fps": [buckets[s]["n"] for s in secs]}
    for k in ("ACTIVE", "DENS", "cloud_pct", "in_cloud"):
        series[k] = [buckets[s].get(k) for s in secs]
    last = {k: num(rows[-1][idx[k]]) for k in FIELDS if k in idx}
    age = time.time() - os.path.getmtime(path)
    return {"log": os.path.basename(path), "stale_s": round(age, 1), "last": last, "series": series}


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>CloudPass live</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0f1419;--card:#172029;--fg:#e6edf3;--mut:#8b98a5;--ok:#5fd38d;--bad:#ff7b72;--a:#58a6ff;--b:#f0b35a;--c:#c39bff}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,Segoe UI,sans-serif;padding:16px}
h1{font-size:18px;margin:0 0 12px} .mut{color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:14px}
.card{background:var(--card);border-radius:10px;padding:10px 12px}
.card .k{color:var(--mut);font-size:12px}.card .v{font-size:22px;font-weight:600;margin-top:2px}
.ok{color:var(--ok)}.bad{color:var(--bad)}
canvas{width:100%;height:120px;background:var(--card);border-radius:10px;display:block;margin-bottom:10px}
.lab{font-size:12px;color:var(--mut);margin:6px 2px 4px}
</style></head><body>
<h1>CloudPass live <span id="log" class="mut"></span></h1>
<div class="grid" id="cards"></div>
<div class="lab">FPS (frames per second, last 5 min)</div><canvas id="c_fps"></canvas>
<div class="lab">Clouds alive <span style="color:var(--b)">&#9632;</span> &nbsp; in cloud <span style="color:var(--c)">&#9632;</span></div><canvas id="c_alive"></canvas>
<div class="lab">Cloud density % <span style="color:var(--a)">&#9632;</span> &nbsp; patch density x25 <span style="color:var(--b)">&#9632;</span></div><canvas id="c_dens"></canvas>
<script>
function card(k,v,cls){return `<div class="card"><div class="k">${k}</div><div class="v ${cls||''}">${v}</div></div>`}
function fmt(v,d){return v==null?'-':Number(v).toFixed(d||0)}
function chart(id,lines,ymax){
  const c=document.getElementById(id),dpr=window.devicePixelRatio||1,w=c.clientWidth,h=c.clientHeight;
  c.width=w*dpr;c.height=h*dpr;const g=c.getContext('2d');g.scale(dpr,dpr);g.clearRect(0,0,w,h);
  let max=ymax||1;lines.forEach(l=>l.v.forEach(x=>{if(x!=null&&x>max)max=x}));
  g.strokeStyle='#26323d';g.fillStyle='#8b98a5';g.font='11px system-ui';
  for(let i=0;i<=4;i++){const y=h-6-(h-16)*i/4;g.beginPath();g.moveTo(30,y);g.lineTo(w-4,y);g.stroke();g.fillText(Math.round(max*i/4),2,y+4)}
  lines.forEach(l=>{const n=l.v.length;if(n<2)return;g.strokeStyle=l.col;g.lineWidth=l.fill?0:1.6;g.beginPath();let on=false;
    l.v.forEach((x,i)=>{if(x==null){on=false;return}const px=30+(w-34)*i/(n-1),py=h-6-(h-16)*x/max;on?g.lineTo(px,py):g.moveTo(px,py);on=true});
    if(l.fill){g.lineTo(w-4,h-6);g.lineTo(30,h-6);g.closePath();g.fillStyle=l.col+'40';g.fill()}else g.stroke()})
}
async function tick(){
  try{
    const d=await (await fetch('data')).json();
    document.getElementById('log').textContent=d.log?('· '+d.log):'· no log yet';
    if(!d.last){return}
    const L=d.last,s=d.series,fps=s.fps.length?s.fps[s.fps.length-1]:null;
    const live=d.stale_s<3;
    document.getElementById('cards').innerHTML=
      card('Monitor',live?'live':'waiting',live?'ok':'bad')+card('FPS',fmt(fps))+
      card('Clouds alive',fmt(L.ACTIVE))+card('In cloud',L.in_cloud>0.5?'yes':'no',L.in_cloud>0.5?'ok':'')+
      card('Cloud density',fmt(L.cloud_pct,1)+' %')+card('Patch density',fmt(L.DENS,2))+
      card('Spawned',fmt(L.SPAWNS))+card('Failed',fmt(L.FAILS),L.FAILS>0?'bad':'')+
      card('Effect',fmt(L.EFFECT))+card('Test mode',L.TEST>0.5?'on':'off')+
      card('Ground speed',fmt(L.gs_kt)+' kt')+card('Altitude',fmt(L.alt_ft)+' ft')+
      card('Lights','S'+(L.strobe>0.5?'●':'○')+' B'+(L.beacon>0.5?'●':'○')+' L'+(L.landing>0.5?'●':'○'));
    chart('c_fps',[{v:s.fps,col:'#58a6ff'}],60);
    chart('c_alive',[{v:s.in_cloud.map(x=>x==null?null:x*Math.max(10,...s.ACTIVE.filter(v=>v!=null))),col:'#c39bff',fill:true},{v:s.ACTIVE,col:'#f0b35a'}],10);
    chart('c_dens',[{v:s.cloud_pct,col:'#58a6ff'},{v:s.DENS.map(x=>x==null?null:x*25),col:'#f0b35a'}],100);
  }catch(e){document.getElementById('log').textContent='· dashboard error: '+e}
}
tick();setInterval(tick,1000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/data"):
            body = json.dumps(snapshot()).encode()
            ctype = "application/json"
        else:
            body = PAGE.encode("utf-8")
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"CloudPass dashboard on http://localhost:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
