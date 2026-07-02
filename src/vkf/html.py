"""Self-contained HTML visualizer for a VKF bundle.

OKF ships a static HTML graph viewer; VKF's adds the trust layer — nodes are
coloured by freshness/lifecycle, ringed by visibility, and carry a type glyph;
edges are curved, directed (per-relation arrowheads), and styled by typed
relation (including claim-evidence edges). The viewer runs a live cooling
force-directed layout with zoom/pan, hover-to-focus (dim everything except a
node and its neighbours), full-text search, and type filters, so even bundles
with long identifiers stay legible. The output is a single dependency-free HTML
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
  :root {
    --bg:#0b0e14; --bg2:#0f131c; --panel:#0d111a; --line:#1e2530; --line2:#2a3342;
    --ink:#e7ecf3; --muted:#8b95a7; --faint:#5b6577; --accent:#7dd3fc;
  }
  * { box-sizing: border-box; }
  html,body { height:100%; }
  body { margin:0; font:13.5px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
    background:var(--bg); color:var(--ink); overflow:hidden; }
  header { height:52px; padding:0 16px; border-bottom:1px solid var(--line);
    display:flex; gap:14px; align-items:center; background:linear-gradient(180deg,#10151f,#0b0e14); }
  header h1 { font-size:14px; margin:0; font-weight:600; letter-spacing:.2px; white-space:nowrap; }
  header h1 .sub { color:var(--muted); font-weight:500; }
  .pill { border:1px solid var(--line2); border-radius:999px; padding:3px 10px; font-size:12px;
    color:var(--muted); background:#121826; white-space:nowrap; }
  .pill.err { color:#fecaca; border-color:#7f1d1d; background:#2a1416; }
  .pill.err.zero { color:#a7f3d0; border-color:#14532d; background:#0e2019; }
  .pill.warn { color:#fde68a; border-color:#78511b; background:#241d0f; }
  .grow { flex:1; }
  .search { position:relative; }
  .search input { width:230px; background:#0c1119; border:1px solid var(--line2); color:var(--ink);
    border-radius:8px; padding:7px 10px 7px 30px; font-size:13px; outline:none; }
  .search input:focus { border-color:var(--accent); box-shadow:0 0 0 3px rgba(125,211,252,.12); }
  .search svg { position:absolute; left:9px; top:8px; width:14px; height:14px; stroke:var(--faint); fill:none; }
  .btn { background:#121826; border:1px solid var(--line2); color:var(--ink); border-radius:8px;
    padding:7px 11px; font-size:12.5px; cursor:pointer; white-space:nowrap; }
  .btn:hover { border-color:#3a4658; background:#161d2b; }
  .btn.on { border-color:var(--accent); color:var(--accent); }
  #wrap { display:flex; height:calc(100vh - 52px); }
  #stage { flex:1; position:relative; overflow:hidden;
    background:radial-gradient(1200px 800px at 30% 0%, #121a28 0%, var(--bg) 60%); }
  svg#graph { width:100%; height:100%; display:block; cursor:grab; }
  svg#graph.panning { cursor:grabbing; }
  .zoombar { position:absolute; left:12px; bottom:12px; display:flex; flex-direction:column;
    border:1px solid var(--line2); border-radius:10px; overflow:hidden; background:#0d121c; }
  .zoombar button { width:34px; height:32px; background:transparent; color:var(--ink); border:0;
    border-bottom:1px solid var(--line); font-size:16px; cursor:pointer; }
  .zoombar button:last-child { border-bottom:0; font-size:12px; }
  .zoombar button:hover { background:#161d2b; }
  aside { width:344px; border-left:1px solid var(--line); background:var(--panel);
    display:flex; flex-direction:column; }
  .apad { padding:16px; overflow:auto; }
  #detail { flex:1; }
  .empty { color:var(--muted); }
  .empty .hint { margin-top:10px; font-size:12px; color:var(--faint); }
  .dtitle { font-size:15px; margin:0 0 2px; font-weight:600; word-break:break-word; }
  .did { font-size:12px; color:var(--muted); word-break:break-all; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  .badges { display:flex; flex-wrap:wrap; gap:6px; margin:12px 0 2px; }
  .badge { font-size:11px; padding:2px 8px; border-radius:999px; border:1px solid var(--line2); color:var(--ink);
    display:inline-flex; align-items:center; gap:6px; }
  .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
  .kv { display:grid; grid-template-columns:78px 1fr; gap:6px 10px; margin:14px 0 4px; font-size:13px; }
  .kv dt { color:var(--muted); } .kv dd { margin:0; word-break:break-word; }
  .kv dd.mono { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; color:var(--muted); }
  .rel-h { font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:var(--faint); margin:14px 0 6px; }
  .chip { display:inline-flex; align-items:center; gap:6px; background:#121826; border:1px solid var(--line2);
    border-radius:7px; padding:4px 8px; margin:0 6px 6px 0; font-size:12px; cursor:pointer; max-width:100%; }
  .chip:hover { border-color:var(--accent); }
  .chip .rl { width:16px; height:0; border-top:2px solid; flex:none; }
  .chip .nm { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .legend { border-top:1px solid var(--line); padding:14px 16px 20px; font-size:12px; color:var(--muted); }
  .legend b { color:var(--ink); font-weight:600; display:block; margin:12px 0 6px; font-size:11px;
    text-transform:uppercase; letter-spacing:.5px; }
  .legend b:first-child { margin-top:0; }
  .lrow { display:flex; align-items:center; gap:8px; margin:4px 0; cursor:default; }
  .lrow.click { cursor:pointer; user-select:none; }
  .lrow.click:hover { color:var(--ink); }
  .lrow.off { opacity:.4; }
  .lrow.off .cnt { text-decoration:line-through; }
  .swatch { width:12px; height:12px; border-radius:3px; flex:none; }
  .sline { width:16px; height:0; border-top:2px solid; flex:none; }
  .cnt { margin-left:auto; color:var(--faint); font-variant-numeric:tabular-nums; }
  /* SVG graph */
  .edge { fill:none; stroke-linecap:round; opacity:.52; transition:opacity .12s; }
  .edge.active { opacity:1; }
  .edge.dim { opacity:.05; }
  .node { cursor:pointer; }
  .node .ring { fill:#0b0e14; stroke-width:2.5; }
  .node .core { stroke:#0b0e14; stroke-width:1.5; }
  .node .glyph { fill:#08101a; font-weight:700; text-anchor:middle; font-size:10px; pointer-events:none;
    font-family:system-ui,sans-serif; }
  .node .lbl { pointer-events:none; }
  .node .lbl rect { fill:rgba(9,12,18,.86); stroke:rgba(255,255,255,.07); }
  .node .lbl text { fill:#dbe2ec; font-size:11px; }
  .node.dim { opacity:.14; }
  .node.sel .core { stroke:#ffffff; stroke-width:2.5; }
  .node.sel .lbl rect { stroke:rgba(255,255,255,.5); }
  .node.hit .core { stroke:#fde047; stroke-width:2.5; }
  .node.hidden, .edge.hidden { display:none; }
</style>
</head>
<body>
<header>
  <h1><span class="sub">VKF ·</span> <span id="title"></span></h1>
  <span class="pill" id="profile"></span>
  <span class="pill" id="counts"></span>
  <span class="pill" id="errs"></span>
  <span class="pill warn" id="warns"></span>
  <span class="grow"></span>
  <div class="search">
    <svg viewBox="0 0 24 24" stroke-width="2.4"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
    <input id="q" type="search" placeholder="Search concepts…" autocomplete="off" spellcheck="false">
  </div>
  <button class="btn" id="fit" title="Fit the whole graph in view">Fit view</button>
  <button class="btn" id="relayout" title="Reset node positions and re-run the layout">Re-layout</button>
  <button class="btn" id="freeze" title="Pause / resume the physics simulation">Freeze</button>
</header>
<div id="wrap">
  <div id="stage">
    <svg id="graph"></svg>
    <div class="zoombar">
      <button id="zin" title="Zoom in">+</button>
      <button id="zout" title="Zoom out">−</button>
      <button id="zrst" title="Reset view">⤢</button>
    </div>
  </div>
  <aside>
    <div class="apad" id="detail">
      <div class="empty">Nothing selected.
        <div class="hint">Click a node to inspect it. Hover to focus on its neighbours.
        Scroll to zoom, drag the background to pan, drag a node to reposition it.</div>
      </div>
    </div>
    <div class="legend" id="legend"></div>
  </aside>
</div>
<script>
const DATA = __DATA__;
const NS = "http://www.w3.org/2000/svg";

const FRESH = {
  fresh:        {c:"#34d399", t:"fresh"},
  stale:        {c:"#fb7185", t:"stale / past valid_until"},
  unknown:      {c:"#fbbf24", t:"no valid_until set"},
  deprecated:   {c:"#a78bfa", t:"deprecated"},
  superseded:   {c:"#a78bfa", t:"superseded"},
  retracted:    {c:"#64748b", t:"retracted"},
  archived:     {c:"#64748b", t:"archived"},
  "null":       {c:"#60a5fa", t:"undated"},
};
const freshColor = f => (FRESH[f] || FRESH["null"]).c;

const VIS = {
  public:       {c:"#22c55e", t:"public"},
  internal:     {c:"#3b82f6", t:"internal"},
  confidential: {c:"#f59e0b", t:"confidential"},
  restricted:   {c:"#ef4444", t:"restricted"},
  private:      {c:"#ec4899", t:"private"},
  "null":       {c:"#334155", t:"unspecified"},
};
const visColor = v => (VIS[v] || VIS["null"]).c;

const REL = {
  depends_on:    {c:"#60a5fa", dash:"",     t:"depends on"},
  supersedes:    {c:"#f59e0b", dash:"",     t:"supersedes"},
  superseded_by: {c:"#f59e0b", dash:"5 4",  t:"superseded by"},
  conflicts_with:{c:"#fb7185", dash:"7 5",  t:"conflicts with"},
  derived_from:  {c:"#34d399", dash:"2 4",  t:"derived from"},
  evidenced_by:  {c:"#22d3ee", dash:"1 5",  t:"evidenced by"},
  links_to:      {c:"#475569", dash:"",     t:"links to"},
};
const rel = r => REL[r] || REL.links_to;

// --- header ---------------------------------------------------------------
const $ = id => document.getElementById(id);
$("title").textContent = DATA.title;
$("profile").textContent = "profile " + DATA.profile;
$("counts").textContent = DATA.graph.nodes.length + " nodes · " + DATA.graph.edges.length + " edges";
const S = DATA.summary || {};
const ep = $("errs"); ep.textContent = (S.ERROR||0) + (S.ERROR===1?" error":" errors");
ep.classList.add("err"); if (!S.ERROR) ep.classList.add("zero");
if (S.WARNING) $("warns").textContent = S.WARNING + (S.WARNING===1?" warning":" warnings"); else $("warns").remove();

// --- model ----------------------------------------------------------------
const idx = {}; DATA.graph.nodes.forEach((n,i)=> idx[n.id]=i);
const N = DATA.graph.nodes.length;
const nodes = DATA.graph.nodes.map((n,i)=>{
  const a = (i/Math.max(1,N))*Math.PI*2, R = 60 + N*7;
  return Object.assign({}, n, { x:Math.cos(a)*R, y:Math.sin(a)*R, vx:0, vy:0, deg:0, fixed:false });
});
const edges = DATA.graph.edges
  .filter(e => idx[e.source]!==undefined && idx[e.target]!==undefined)
  .map(e => ({ s:idx[e.source], t:idx[e.target], relation:e.relation }));
const nbr = nodes.map(()=> new Set());
edges.forEach(e => { nodes[e.s].deg++; nodes[e.t].deg++; nbr[e.s].add(e.t); nbr[e.t].add(e.s); });
const radius = n => 11 + Math.min(8, n.deg*1.4);
const glyph = n => (n.type ? String(n.type)[0].toUpperCase() : "·");

// --- svg scaffold ---------------------------------------------------------
const svg = $("graph");
const defs = document.createElementNS(NS,"defs");
Object.entries(REL).forEach(([k,v])=>{
  const m = document.createElementNS(NS,"marker");
  m.setAttribute("id","ar-"+k); m.setAttribute("viewBox","0 0 8 8");
  m.setAttribute("markerWidth","7"); m.setAttribute("markerHeight","7");
  m.setAttribute("refX","6.5"); m.setAttribute("refY","4");
  m.setAttribute("orient","auto"); m.setAttribute("markerUnits","userSpaceOnUse");
  const p = document.createElementNS(NS,"path");
  p.setAttribute("d","M0,1 L7,4 L0,7 Z"); p.setAttribute("fill",v.c);
  m.appendChild(p); defs.appendChild(m);
});
svg.appendChild(defs);
const viewport = document.createElementNS(NS,"g");
const eLayer = document.createElementNS(NS,"g");
const nLayer = document.createElementNS(NS,"g");
viewport.appendChild(eLayer); viewport.appendChild(nLayer); svg.appendChild(viewport);

function esc(x){ return (x==null?"":String(x)).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function trunc(s,n){ s=String(s==null?"":s); return s.length>n ? s.slice(0,n-1)+"…" : s; }

// build persistent DOM (updated in place, never rebuilt)
const eEls = edges.map(e=>{
  const st = rel(e.relation);
  const p = document.createElementNS(NS,"path");
  p.setAttribute("class","edge"); p.setAttribute("stroke",st.c);
  if (st.dash) p.setAttribute("stroke-dasharray",st.dash);
  p.setAttribute("stroke-width","1.6");
  p.setAttribute("marker-end","url(#ar-"+(REL[e.relation]?e.relation:"links_to")+")");
  eLayer.appendChild(p); return p;
});
const nEls = nodes.map((n,i)=>{
  const g = document.createElementNS(NS,"g"); g.setAttribute("class","node");
  const r = radius(n);
  const ring = document.createElementNS(NS,"circle");
  ring.setAttribute("class","ring"); ring.setAttribute("r",r+2.5); ring.setAttribute("stroke",visColor(n.visibility));
  const core = document.createElementNS(NS,"circle");
  core.setAttribute("class","core"); core.setAttribute("r",r); core.setAttribute("fill",freshColor(n.freshness));
  const gl = document.createElementNS(NS,"text");
  gl.setAttribute("class","glyph"); gl.setAttribute("dy","3.4"); gl.textContent = glyph(n);
  const lbl = document.createElementNS(NS,"g");
  lbl.setAttribute("class","lbl"); lbl.setAttribute("transform","translate("+(r+7)+",0)");
  const rect = document.createElementNS(NS,"rect");
  const txt = document.createElementNS(NS,"text");
  const label = trunc(n.title || n.id, 26);
  txt.setAttribute("x","6"); txt.setAttribute("y","3.5"); txt.textContent = label;
  const w = label.length*6.05 + 12;
  rect.setAttribute("x","0"); rect.setAttribute("y","-9"); rect.setAttribute("rx","5");
  rect.setAttribute("height","18"); rect.setAttribute("width",w);
  lbl.appendChild(rect); lbl.appendChild(txt);
  const tip = document.createElementNS(NS,"title"); tip.textContent = (n.title? n.title+"  ":"")+"("+n.id+")";
  g.appendChild(ring); g.appendChild(core); g.appendChild(gl); g.appendChild(lbl); g.appendChild(tip);
  g.addEventListener("pointerenter", ()=>{ hovered=i; applyVisual(); });
  g.addEventListener("pointerleave", ()=>{ if(hovered===i){ hovered=-1; applyVisual(); } });
  g.addEventListener("pointerdown", ev=> startNodeDrag(ev,i));
  g.addEventListener("click", ev=>{ ev.stopPropagation(); select(i); });
  g.addEventListener("dblclick", ev=>{ ev.stopPropagation(); nodes[i].fixed=false; reheat(0.4); });
  nLayer.appendChild(g); return {g, r, lbl};
});

// --- layout (live cooling simulation) ------------------------------------
let alpha = 1;
function physics(){
  const cx=0, cy=0;
  for (let i=0;i<N;i++){
    let fx=0, fy=0; const a=nodes[i];
    for (let j=0;j<N;j++) if(i!==j){
      const b=nodes[j]; let dx=a.x-b.x, dy=a.y-b.y; let d2=dx*dx+dy*dy+0.01, d=Math.sqrt(d2);
      let f=6500/d2; fx+=f*dx/d; fy+=f*dy/d;
      const min=nEls[i].r+nEls[j].r+18;               // soft collision keeps labels apart
      if(d<min){ const push=(min-d)/d*0.5; fx+=dx*push; fy+=dy*push; }
    }
    fx += (cx-a.x)*0.018; fy += (cy-a.y)*0.018;        // gentle centering
    a.vx=(a.vx+fx*alpha)*0.82; a.vy=(a.vy+fy*alpha)*0.82;
  }
  const k=130;
  edges.forEach(e=>{ const a=nodes[e.s], b=nodes[e.t];
    let dx=b.x-a.x, dy=b.y-a.y, d=Math.sqrt(dx*dx+dy*dy)+0.01, f=(d-k)*0.04*alpha;
    a.vx+=f*dx/d; a.vy+=f*dy/d; b.vx-=f*dx/d; b.vy-=f*dy/d; });
  for (let i=0;i<N;i++){ const n=nodes[i]; if(n.fixed) continue; n.x+=n.vx; n.y+=n.vy; }
}
function edgeD(e){
  const a=nodes[e.s], b=nodes[e.t]; let dx=b.x-a.x, dy=b.y-a.y, d=Math.hypot(dx,dy)||1;
  const ux=dx/d, uy=dy/d, ra=nEls[e.s].r, rb=nEls[e.t].r+7;
  const sx=a.x+ux*ra, sy=a.y+uy*ra, tx=b.x-ux*rb, ty=b.y-uy*rb;
  const mx=(sx+tx)/2, my=(sy+ty)/2, c=d*0.11;          // slight curve to separate reciprocal edges
  return "M"+sx+","+sy+" Q"+(mx-uy*c)+","+(my+ux*c)+" "+tx+","+ty;
}
function render(){
  for (let i=0;i<N;i++){ const n=nodes[i]; nEls[i].g.setAttribute("transform","translate("+n.x.toFixed(1)+","+n.y.toFixed(1)+")"); }
  for (let i=0;i<edges.length;i++){ eEls[i].setAttribute("d", edgeD(edges[i])); }
}
// warm start so the ring layout settles before first paint
for (let i=0;i<220;i++){ physics(); alpha*=0.99; }
alpha=0;

let running=true, frame=null;
function loop(){
  if (running && (alpha>0.004 || dragNode>=0)){ physics(); render(); alpha*=0.985; }
  frame = requestAnimationFrame(loop);
}
function reheat(a){ if(running) alpha=Math.max(alpha,a); }
function relayout(){
  nodes.forEach((n,i)=>{ const a=(i/Math.max(1,N))*Math.PI*2, R=60+N*7;
    n.x=Math.cos(a)*R; n.y=Math.sin(a)*R; n.vx=0; n.vy=0; n.fixed=false; });
  running=true; setFreezeUI(); alpha=1;
  for (let i=0;i<220;i++){ physics(); alpha*=0.99; } alpha=0.3;
  render(); fit(); applyVisual();
}

// --- zoom / pan -----------------------------------------------------------
let scale=1, tx=0, ty=0;
function applyView(){ viewport.setAttribute("transform","translate("+tx+","+ty+") scale("+scale+")"); }
function zoomAt(cx,cy,factor){
  const before=labelsShown();
  const ns=Math.max(0.15,Math.min(4,scale*factor));
  tx = cx-(cx-tx)*(ns/scale); ty = cy-(cy-ty)*(ns/scale); scale=ns; applyView();
  if(labelsShown()!==before) applyVisual();       // only recompute labels when the LOD threshold flips
}
function fit(){
  if(!N){ return; }
  let minX=1e9,minY=1e9,maxX=-1e9,maxY=-1e9;
  nodes.forEach((n,i)=>{ const r=nEls[i].r+80; minX=Math.min(minX,n.x-r); minY=Math.min(minY,n.y-r);
    maxX=Math.max(maxX,n.x+r); maxY=Math.max(maxY,n.y+r); });
  const w=svg.clientWidth, h=svg.clientHeight, gw=maxX-minX, gh=maxY-minY;
  scale=Math.max(0.2,Math.min(2, Math.min(w/gw, h/gh)));
  tx = w/2 - (minX+gw/2)*scale; ty = h/2 - (minY+gh/2)*scale; applyView(); applyVisual();
}
svg.addEventListener("wheel", ev=>{ ev.preventDefault();
  const r=svg.getBoundingClientRect();
  zoomAt(ev.clientX-r.left, ev.clientY-r.top, ev.deltaY<0?1.12:1/1.12); }, {passive:false});
$("zin").onclick = ()=> zoomAt(svg.clientWidth/2, svg.clientHeight/2, 1.25);
$("zout").onclick = ()=> zoomAt(svg.clientWidth/2, svg.clientHeight/2, 1/1.25);
$("zrst").onclick = fit;
$("fit").onclick = fit;

// --- pointer drag (pan background or move a node) -------------------------
let dragNode=-1, panning=false, moved=false, last=null;
function toWorld(ev){ const r=svg.getBoundingClientRect();
  return { x:(ev.clientX-r.left-tx)/scale, y:(ev.clientY-r.top-ty)/scale }; }
function startNodeDrag(ev,i){ ev.stopPropagation(); dragNode=i; moved=false; nodes[i].fixed=true;
  reheat(0.35); svg.setPointerCapture(ev.pointerId); }
svg.addEventListener("pointerdown", ev=>{ if(dragNode>=0) return; panning=true; moved=false;
  last={x:ev.clientX,y:ev.clientY}; svg.classList.add("panning"); svg.setPointerCapture(ev.pointerId); });
svg.addEventListener("pointermove", ev=>{
  if(dragNode>=0){ moved=true; const w=toWorld(ev); const n=nodes[dragNode]; n.x=w.x; n.y=w.y; n.vx=0; n.vy=0; render(); }
  else if(panning){ moved=true; tx+=ev.clientX-last.x; ty+=ev.clientY-last.y; last={x:ev.clientX,y:ev.clientY}; applyView(); }
});
function endDrag(){
  // A dragged node stays pinned where you dropped it; double-click it to release.
  if(dragNode>=0){ dragNode=-1; reheat(0.15); }
  panning=false; svg.classList.remove("panning");
}
svg.addEventListener("pointerup", endDrag);
svg.addEventListener("pointercancel", endDrag);
svg.addEventListener("click", ()=>{ if(!moved){ select(-1); } });

// --- focus / search / filter ---------------------------------------------
let selected=-1, hovered=-1, query="", hidden=new Set();
const LABEL_ZOOM = 0.72;
function labelsShown(){ return scale>=LABEL_ZOOM || N<=22; }
function applyVisual(){
  const focus = hovered>=0 ? hovered : selected;
  const q = query.trim().toLowerCase();
  const showAll = labelsShown();
  for (let i=0;i<N;i++){
    const n=nodes[i], el=nEls[i], g=el.g;
    const isHidden = hidden.has(n.type||"null");
    g.classList.toggle("hidden", isHidden);
    if (isHidden) continue;
    let dim=false, hit=false;
    if (focus>=0) dim = !(i===focus || nbr[focus].has(i));
    if (q){ const m=((n.title||"")+" "+n.id).toLowerCase().includes(q); if(m) hit=true; else dim=true; }
    g.classList.toggle("dim", dim);
    g.classList.toggle("hit", hit);
    g.classList.toggle("sel", i===selected);
    const showLbl = hit || i===selected || i===focus || (focus>=0 && nbr[focus].has(i)) || (showAll && !dim);
    el.lbl.style.display = showLbl ? "" : "none";
  }
  for (let i=0;i<edges.length;i++){
    const e=edges[i], el=eEls[i];
    const hide = hidden.has(nodes[e.s].type||"null") || hidden.has(nodes[e.t].type||"null");
    el.classList.toggle("hidden", hide);
    let dim=false, active=false;
    if (focus>=0){ active = (e.s===focus || e.t===focus); dim=!active; }
    el.classList.toggle("active", active);
    el.classList.toggle("dim", dim);
  }
}
$("q").addEventListener("input", e=>{ query=e.target.value; applyVisual(); });
function setFreezeUI(){ const b=$("freeze"); b.classList.toggle("on",!running); b.textContent = running?"Freeze":"Frozen"; }
$("freeze").addEventListener("click", ()=>{ running=!running; setFreezeUI(); if(running) reheat(0.5); });
$("relayout").addEventListener("click", relayout);

// --- detail panel ---------------------------------------------------------
function badge(label,val,color){ if(val==null) return "";
  return "<span class='badge'>"+(color?"<span class='dot' style='background:"+color+"'></span>":"")+esc(val)+"</span>"; }
function chip(j,relation,dir){ const n=nodes[j], st=rel(relation);
  const arrow = dir==="out" ? "→" : "←";
  return "<span class='chip' data-i='"+j+"'><span class='rl' style='border-color:"+st.c+"'></span>"+
    "<span class='nm'>"+arrow+" "+esc(trunc(n.title||n.id,30))+"</span></span>"; }
function select(i){
  selected=i; const d=$("detail");
  if(i<0){ d.innerHTML="<div class='empty'>Nothing selected.<div class='hint'>Click a node to inspect it. "+
      "Hover to focus on its neighbours.</div></div>"; applyVisual(); return; }
  const n=nodes[i];
  const outs = edges.filter(e=>e.s===i), ins = edges.filter(e=>e.t===i);
  let rels="";
  if(outs.length){ rels+="<div class='rel-h'>outgoing</div>"+outs.map(e=>chip(e.t,e.relation,"out")).join(""); }
  if(ins.length){ rels+="<div class='rel-h'>incoming</div>"+ins.map(e=>chip(e.s,e.relation,"in")).join(""); }
  if(!rels) rels="<div class='rel-h'>relations</div><div style='color:var(--faint);font-size:12px'>none</div>";
  d.innerHTML =
    "<div class='dtitle'>"+esc(n.title||n.id)+"</div><div class='did'>"+esc(n.id)+"</div>"+
    "<div class='badges'>"+
      badge("type",n.type)+
      badge("status",n.status)+
      badge("visibility",n.visibility, visColor(n.visibility))+
      badge("freshness",n.freshness, freshColor(n.freshness))+
    "</div>"+
    "<dl class='kv'>"+
      (n.path?"<dt>path</dt><dd class='mono'>"+esc(n.path)+"</dd>":"")+
      (n.concept_id && n.concept_id!==n.id?"<dt>concept</dt><dd class='mono'>"+esc(n.concept_id)+"</dd>":"")+
    "</dl>"+ rels;
  d.querySelectorAll(".chip").forEach(c=> c.addEventListener("click", ()=> select(+c.dataset.i)));
  applyVisual();
}

// --- legend + type filter -------------------------------------------------
const typeCounts = {};
nodes.forEach(n=>{ const t=n.type||"untyped"; typeCounts[t]=(typeCounts[t]||0)+1; });
const usedFresh = new Set(nodes.map(n=> n.freshness==null?"null":n.freshness));
const usedVis   = new Set(nodes.map(n=> n.visibility==null?"null":n.visibility));
const usedRel   = new Set(edges.map(e=> REL[e.relation]?e.relation:"links_to"));
function legendRows(){
  const types = Object.keys(typeCounts).sort();
  const typeHtml = types.map(t=>{
    const off = hidden.has(t==="untyped"?"null":t);
    return "<div class='lrow click"+(off?" off":"")+"' data-t='"+esc(t)+"'>"+
      "<span class='swatch' style='background:#1b2432;border:1px solid var(--line2);"+
        "display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#cbd5e1'>"+
        esc(t[0].toUpperCase())+"</span>"+esc(t)+"<span class='cnt'>"+typeCounts[t]+"</span></div>"; });
  const freshHtml = [...usedFresh].map(f=> "<div class='lrow'><span class='swatch' style='background:"+freshColor(f)+"'></span>"+
      esc((FRESH[f]||FRESH["null"]).t)+"</div>");
  const visHtml = [...usedVis].map(v=> "<div class='lrow'><span class='swatch' style='border-radius:50%;background:#0b0e14;"+
      "border:2.5px solid "+visColor(v)+"'></span>"+esc((VIS[v]||VIS["null"]).t)+"</div>");
  const relHtml = [...usedRel].map(r=> "<div class='lrow'><span class='sline' style='border-color:"+rel(r).c+";"+
      (rel(r).dash?"border-top-style:dashed":"")+"'></span>"+esc(rel(r).t)+"</div>");
  return "<b>Type · click to filter · glyph = node</b>"+typeHtml.join("")+
    "<b>Freshness · node fill</b>"+freshHtml.join("")+
    "<b>Visibility · node ring</b>"+visHtml.join("")+
    "<b>Relations · edges</b>"+relHtml.join("");
}
function renderLegend(){
  const L=$("legend"); L.innerHTML=legendRows();
  L.querySelectorAll(".lrow.click").forEach(row=> row.addEventListener("click", ()=>{
    const t=row.dataset.t, key=t==="untyped"?"null":t;
    if(hidden.has(key)) hidden.delete(key); else hidden.add(key);
    renderLegend(); applyVisual(); }));
}
renderLegend();

// --- go -------------------------------------------------------------------
render(); applyView(); fit(); applyVisual(); loop();
window.addEventListener("resize", fit);
</script>
</body>
</html>
"""
