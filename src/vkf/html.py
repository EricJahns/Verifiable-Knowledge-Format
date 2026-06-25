"""Self-contained HTML visualizer for a VKF bundle.

OKF ships a static HTML graph viewer; VKF's adds the trust layer — nodes are
coloured by freshness/lifecycle and bordered by visibility, edges are styled by
typed relation (including claim-evidence edges), and a side panel surfaces
ownership, status, and freshness. The output is a single dependency-free HTML
file (no CDN, no build step) suitable for committing next to the bundle.
"""

from __future__ import annotations

import json
from pathlib import Path

from .service import KnowledgeService


def render_html(root: str | Path, title: str | None = None) -> str:
    service = KnowledgeService(root)
    graph = service.graph()
    fresh = {r["id"]: r["freshness"] for r in service.freshness()}
    for node in graph["nodes"]:
        node["freshness"] = fresh.get(node["id"])
    validation = service.validate()
    data = {
        "title": title or service.root.name,
        "profile": service.profile,
        "graph": graph,
        "summary": validation["summary"],
    }
    payload = json.dumps(data).replace("</", "<\\/")
    return _TEMPLATE.replace("__DATA__", payload)


def write_html(root: str | Path, out: str | Path, title: str | None = None) -> Path:
    out = Path(out)
    out.write_text(render_html(root, title=title))
    return out


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VKF Knowledge Graph</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.45 system-ui, sans-serif; background: #0f1115; color: #e6e8eb; }
  header { padding: 12px 18px; border-bottom: 1px solid #2a2e37; display: flex; gap: 18px; align-items: baseline; flex-wrap: wrap; }
  header h1 { font-size: 16px; margin: 0; font-weight: 600; }
  header .meta { color: #9aa3af; font-size: 12px; }
  header .pill { background:#1b212b; border:1px solid #2a2e37; border-radius: 999px; padding:2px 10px; font-size:12px; }
  #wrap { display: flex; height: calc(100vh - 50px); }
  #graph { flex: 1; }
  aside { width: 340px; border-left: 1px solid #2a2e37; padding: 16px; overflow:auto; }
  aside h2 { font-size: 14px; margin: 0 0 4px; }
  aside .kv { display:grid; grid-template-columns: 96px 1fr; gap:4px 10px; margin-top:10px; font-size:13px; }
  aside .kv dt { color:#9aa3af; } aside .kv dd { margin:0; word-break: break-word; }
  .legend { font-size:12px; color:#9aa3af; }
  .legend b { color:#e6e8eb; font-weight:600; display:block; margin:12px 0 4px; }
  .legend .row { display:flex; align-items:center; gap:8px; margin:3px 0; }
  .swatch { width:12px; height:12px; border-radius:3px; display:inline-block; }
  .empty { color:#9aa3af; }
  text { fill:#cfd4db; font: 11px system-ui, sans-serif; pointer-events:none; }
  line { stroke-opacity: .7; }
  circle.node { cursor:pointer; stroke:#0f1115; stroke-width:2px; }
  circle.node.sel { stroke:#e6e8eb; stroke-width:3px; }
</style>
</head>
<body>
<header>
  <h1>VKF · <span id="title"></span></h1>
  <span class="pill" id="profile"></span>
  <span class="meta" id="counts"></span>
  <span class="meta" id="errs"></span>
</header>
<div id="wrap">
  <svg id="graph"></svg>
  <aside>
    <div id="detail" class="empty">Click a node to inspect a concept.</div>
    <div class="legend" id="legend"></div>
  </aside>
</div>
<script>
const DATA = __DATA__;
const FRESH_COLOR = { fresh:"#34d399", stale:"#f87171", unknown:"#fbbf24",
  deprecated:"#a78bfa", superseded:"#a78bfa", retracted:"#6b7280", archived:"#6b7280", null:"#60a5fa" };
const REL_STYLE = {
  depends_on:   { stroke:"#60a5fa", dash:"" },
  supersedes:   { stroke:"#f59e0b", dash:"" },
  superseded_by:{ stroke:"#f59e0b", dash:"4 3" },
  conflicts_with:{ stroke:"#f87171", dash:"6 4" },
  derived_from: { stroke:"#34d399", dash:"2 3" },
  evidenced_by: { stroke:"#22d3ee", dash:"1 3" },
  links_to:     { stroke:"#3b4250", dash:"" },
};
document.getElementById("title").textContent = DATA.title;
document.getElementById("profile").textContent = "profile " + DATA.profile;
document.getElementById("counts").textContent =
  DATA.graph.nodes.length + " concepts · " + DATA.graph.edges.length + " edges";
const s = DATA.summary || {};
document.getElementById("errs").textContent =
  (s.ERROR||0) + " errors · " + (s.WARNING||0) + " warnings";

const svg = document.getElementById("graph");
const W = () => svg.clientWidth, H = () => svg.clientHeight;
const NS = "http://www.w3.org/2000/svg";

// Build node/edge model. Edges may reference ids not present as nodes.
const byId = {}; DATA.graph.nodes.forEach(n => byId[n.id] = n);
const nodes = DATA.graph.nodes.map(n => Object.assign({}, n,
  { x: Math.random()*800+100, y: Math.random()*600+50, vx:0, vy:0 }));
const idx = {}; nodes.forEach((n,i) => idx[n.id]=i);
const edges = DATA.graph.edges
  .filter(e => idx[e.source]!==undefined && idx[e.target]!==undefined)
  .map(e => ({ s: idx[e.source], t: idx[e.target], relation: e.relation }));

// Simple force-directed layout (good enough for bundle-sized graphs).
function simulate(iter) {
  const k = 90, rep = 9000, cx = W()/2, cy = H()/2;
  for (let it=0; it<iter; it++) {
    for (let i=0;i<nodes.length;i++) {
      let fx=0, fy=0;
      for (let j=0;j<nodes.length;j++) if (i!==j) {
        let dx=nodes[i].x-nodes[j].x, dy=nodes[i].y-nodes[j].y;
        let d2=dx*dx+dy*dy+0.01, d=Math.sqrt(d2);
        let f=rep/d2; fx+=f*dx/d; fy+=f*dy/d;
      }
      fx += (cx-nodes[i].x)*0.01; fy += (cy-nodes[i].y)*0.01;
      nodes[i].vx=(nodes[i].vx+fx)*0.85; nodes[i].vy=(nodes[i].vy+fy)*0.85;
    }
    edges.forEach(e => {
      let a=nodes[e.s], b=nodes[e.t];
      let dx=b.x-a.x, dy=b.y-a.y, d=Math.sqrt(dx*dx+dy*dy)+0.01;
      let f=(d-k)*0.05;
      a.vx+=f*dx/d; a.vy+=f*dy/d; b.vx-=f*dx/d; b.vy-=f*dy/d;
    });
    nodes.forEach(n => { if(!n.fixed){ n.x+=n.vx; n.y+=n.vy; } });
  }
}
simulate(300);

let sel = null;
function draw() {
  svg.innerHTML = "";
  edges.forEach(e => {
    const a=nodes[e.s], b=nodes[e.t], st=REL_STYLE[e.relation]||REL_STYLE.links_to;
    const l=document.createElementNS(NS,"line");
    l.setAttribute("x1",a.x); l.setAttribute("y1",a.y);
    l.setAttribute("x2",b.x); l.setAttribute("y2",b.y);
    l.setAttribute("stroke",st.stroke); l.setAttribute("stroke-dasharray",st.dash);
    svg.appendChild(l);
  });
  nodes.forEach((n,i) => {
    const c=document.createElementNS(NS,"circle");
    c.setAttribute("class","node"+(sel===i?" sel":""));
    c.setAttribute("cx",n.x); c.setAttribute("cy",n.y); c.setAttribute("r",10);
    c.setAttribute("fill", FRESH_COLOR[n.freshness] || FRESH_COLOR.null);
    c.addEventListener("mousedown", ev => startDrag(ev,i));
    c.addEventListener("click", () => select(i));
    svg.appendChild(c);
    const t=document.createElementNS(NS,"text");
    t.setAttribute("x",n.x+13); t.setAttribute("y",n.y+4);
    t.textContent = n.title || n.id;
    svg.appendChild(t);
  });
}
function esc(x){ return (x==null?"":String(x)).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function select(i) {
  sel=i; const n=nodes[i];
  document.getElementById("detail").className="";
  document.getElementById("detail").innerHTML =
    "<h2>"+esc(n.title||n.id)+"</h2><div class='legend'>"+esc(n.id)+"</div>"+
    "<dl class='kv'>"+
    row("type",n.type)+row("status",n.status)+row("visibility",n.visibility)+
    row("freshness",n.freshness)+row("path",n.path)+"</dl>";
  draw();
}
function row(k,v){ return v==null?"":"<dt>"+k+"</dt><dd>"+esc(v)+"</dd>"; }

let drag=null;
function startDrag(ev,i){ drag={i, }; nodes[i].fixed=true; ev.preventDefault(); }
window.addEventListener("mousemove", ev=>{
  if(drag===null) return;
  const r=svg.getBoundingClientRect();
  nodes[drag.i].x=ev.clientX-r.left; nodes[drag.i].y=ev.clientY-r.top;
  nodes[drag.i].vx=0; nodes[drag.i].vy=0; draw();
});
window.addEventListener("mouseup", ()=>{ if(drag){nodes[drag.i].fixed=false;drag=null;} });
window.addEventListener("resize", ()=>{ simulate(40); draw(); });

// Legend
const fl = Object.entries({fresh:"fresh",stale:"stale / past valid_until",unknown:"no valid_until",
  deprecated:"deprecated / superseded","null":"undated"});
const rl = Object.entries(REL_STYLE);
document.getElementById("legend").innerHTML =
  "<b>Freshness (node colour)</b>"+ fl.map(([k,t])=>
    "<div class='row'><span class='swatch' style='background:"+(FRESH_COLOR[k]||FRESH_COLOR.null)+"'></span>"+t+"</div>").join("")+
  "<b>Relations (edges)</b>"+ rl.map(([k,v])=>
    "<div class='row'><span class='swatch' style='background:"+v.stroke+"'></span>"+k+"</div>").join("");

draw();
</script>
</body>
</html>
"""
