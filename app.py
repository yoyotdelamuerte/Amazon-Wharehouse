"""
Amazon Warehouse Simulation — Streamlit Dashboard
Run: streamlit run app.py
"""

import streamlit as st
import time
import json
import random
import config
from map_validator import MapValidator
from warehouse_map import WarehouseMap
from fleet_manager import FleetManager
from robot_agent import RobotState
from st_visualizer import generate_warehouse_svg

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Warehouse Control",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State Init ────────────────────────────────────────────────────────
DEFAULTS = {
    "sim_running": False,
    "sim_initialized": False,
    "wm": None, "fm": None,
    "tick": 0,
    "map_cells": {}, "map_categories": {},
    "editor_tool": "floor",
    "map_ready": False,
    "last_map_data": None,
    "error_msg": None,
    "dark_mode": True,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

dark = st.session_state.dark_mode

# ── Theme Colors ──────────────────────────────────────────────────────────────
if dark:
    BG          = "#0d1117"
    SURFACE     = "#161b22"
    SURFACE2    = "#1f2937"
    BORDER      = "#30363d"
    TEXT        = "#e6edf3"
    TEXT_MUTED  = "#8b949e"
    ACCENT      = "#f59e0b"
    ACCENT2     = "#fbbf24"
    MAP_BG      = "#010409"
    PILL_BG     = "#21262d"
else:
    BG          = "#f3f4f6"
    SURFACE     = "#ffffff"
    SURFACE2    = "#f9fafb"
    BORDER      = "#d1d5db"
    TEXT        = "#111827"
    TEXT_MUTED  = "#6b7280"
    ACCENT      = "#d97706"
    ACCENT2     = "#f59e0b"
    MAP_BG      = "#e5e7eb"
    PILL_BG     = "#e5e7eb"

# ── CSS Injection ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    font-size: 13px;
  }}

  /* ── Layout ── */
  .stApp {{
    background: {BG};
    height: 100vh;
    overflow: hidden;
  }}
  .block-container {{
    padding: 0.5rem 1rem 0 1rem !important;
    max-width: 100% !important;
  }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {{
    background: {SURFACE};
    border-right: 1px solid {BORDER};
  }}
  section[data-testid="stSidebar"] * {{
    color: {TEXT} !important;
  }}
  section[data-testid="stSidebar"] .stMarkdown small {{
    color: {TEXT_MUTED} !important;
  }}

  /* ── Top bar ── */
  .topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0 8px 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 8px;
  }}
  .topbar-title {{
    font-size: 15px;
    font-weight: 700;
    color: {ACCENT};
    letter-spacing: 0.3px;
  }}
  .topbar-sub {{
    font-size: 11px;
    color: {TEXT_MUTED};
  }}

  /* ── KPI strip ── */
  .kpi-strip {{
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }}
  .kpi {{
    flex: 1;
    min-width: 0;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 10px;
    text-align: center;
  }}
  .kpi-v {{
    font-size: 20px;
    font-weight: 700;
    color: {ACCENT};
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.1;
  }}
  .kpi-l {{
    font-size: 9px;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 2px;
  }}

  /* ── Section label ── */
  .sec {{
    font-size: 10px;
    font-weight: 600;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 5px;
    padding-bottom: 3px;
    border-bottom: 1px solid {BORDER};
  }}

  /* ── Map container ── */
  .map-wrap {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    overflow: hidden;
    background: {MAP_BG};
  }}

  /* ── Robot cards ── */
  .robot-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 7px 10px;
    margin-bottom: 5px;
  }}
  .robot-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }}
  .robot-id {{
    font-size: 12px;
    font-weight: 700;
    color: {TEXT};
    font-family: 'JetBrains Mono', monospace;
  }}
  .robot-state {{
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 9999px;
  }}
  .robot-meta {{
    font-size: 10px;
    color: {TEXT_MUTED};
    margin-bottom: 3px;
  }}
  .bar-wrap {{
    background: {BORDER};
    border-radius: 3px;
    height: 3px;
    margin-bottom: 2px;
  }}

  /* ── Orders table ── */
  .orders-wrap {{
    overflow-y: auto;
    max-height: 115px;
  }}
  .order-row {{
    display: grid;
    grid-template-columns: 52px 40px 50px 1fr 70px;
    gap: 6px;
    align-items: center;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 5px 10px;
    margin-bottom: 3px;
    border-left: 3px solid {BORDER};
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    color: {TEXT};
  }}
  .order-row.late {{ border-left-color: #ef4444 !important; }}
  .order-header {{
    display: grid;
    grid-template-columns: 52px 40px 50px 1fr 70px;
    gap: 6px;
    font-size: 9px;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 0 10px 3px 10px;
  }}

  /* ── Status badge ── */
  .badge-live {{
    display: inline-flex; align-items: center; gap: 5px;
    background: {("#052e16" if dark else "#dcfce7")};
    border: 1px solid {("#166534" if dark else "#86efac")};
    border-radius: 9999px; padding: 2px 10px;
    font-size: 10px; font-weight: 600; color: #4ade80;
  }}
  .badge-live .dot {{
    width: 6px; height: 6px; border-radius: 50%; background: #4ade80;
    animation: pulse 1.5s infinite;
  }}
  .badge-pause {{
    display: inline-flex; align-items: center; gap: 5px;
    background: {SURFACE2}; border: 1px solid {BORDER};
    border-radius: 9999px; padding: 2px 10px;
    font-size: 10px; font-weight: 600; color: {TEXT_MUTED};
  }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}

  /* ── Buttons ── */
  .stButton > button {{
    background: linear-gradient(135deg, {ACCENT}, {ACCENT2});
    color: #000;
    font-weight: 700;
    border: none;
    border-radius: 7px;
    padding: 6px 16px;
    font-size: 12px;
    width: 100%;
    transition: all 0.15s;
  }}
  .stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245,158,11,0.35);
  }}

  /* ── Sliders & checkboxes ── */
  .stSlider > div, .stCheckbox > div {{ color: {TEXT} !important; }}
  label {{ color: {TEXT} !important; }}

  /* ── Hide streamlit chrome ── */
  #MainMenu, footer, header {{ visibility: hidden; }}
  
  /* ── Responsive ── */
  @media (max-width: 900px) {{
    .kpi-v {{ font-size: 16px; }}
    .kpi {{ padding: 6px 8px; }}
    .block-container {{ padding: 0.3rem 0.5rem 0 !important; }}
    .orders-wrap {{ max-height: 90px; }}
  }}
  @media (max-width: 768px) {{
    .stApp {{ overflow: auto; height: auto; }}
    .kpi-strip {{ flex-wrap: wrap; }}
    .kpi {{ min-width: 80px; }}
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:

    # Theme toggle
    col_th1, col_th2 = st.columns([3, 1])
    with col_th1:
        st.markdown(f"<span style='font-size:13px;font-weight:700;color:{ACCENT};'>🏭 Warehouse</span>", unsafe_allow_html=True)
    with col_th2:
        theme_icon = "☀️" if dark else "🌙"
        if st.button(theme_icon, key="btn_theme", help="Basculer le thème"):
            st.session_state.dark_mode = not dark
            st.rerun()

    st.divider()

    # ── Simulation controls ──────────────────────────────
    st.markdown(f"<div class='sec'>⚙️ Simulation</div>", unsafe_allow_html=True)

    if not st.session_state.sim_initialized:
        if st.session_state.map_ready:
            if st.button("🚀 Lancer", key="btn_launch"):
                parsed = st.session_state.last_map_data
                config.MAP_SHELVES = parsed['shelves']
                config.MAP_DROPS   = parsed['drops']
                config.MAP_CHARGERS= parsed['chargers']
                config.NUM_ROBOTS  = len(config.MAP_CHARGERS)
                from order_manager import Order
                Order._id_counter  = 0
                wm = WarehouseMap()
                fm = FleetManager(wm)
                st.session_state.wm = wm
                st.session_state.fm = fm
                st.session_state.sim_initialized = True
                st.session_state.sim_running = True
                st.session_state.tick = 0
                st.rerun()
        else:
            st.caption("Configurez et validez la carte ci-dessous.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.session_state.sim_running:
                if st.button("⏸ Pause", key="btn_pause"): st.session_state.sim_running = False
            else:
                if st.button("▶️ Play",  key="btn_play"):  st.session_state.sim_running = True
        with c2:
            if st.button("🔄 Reset", key="btn_reset"):
                for k in ["sim_running","sim_initialized","wm","fm","map_ready","last_map_data","error_msg"]:
                    st.session_state[k] = False if isinstance(DEFAULTS[k], bool) else None
                st.session_state.tick = 0
                from order_manager import Order
                Order._id_counter = 0
                st.rerun()

    # ── Live controls ────────────────────────────────────
    if st.session_state.sim_initialized and st.session_state.fm:
        st.divider()
        st.markdown(f"<div class='sec'>🎛️ Contrôles</div>", unsafe_allow_html=True)
        fm = st.session_state.fm

        spawn_val = st.slider("Commandes / tick", 0, 100,
                              int(fm.order_manager.spawn_chance * 100),
                              format="%d%%", key="sl_spawn")
        fm.order_manager.spawn_chance = spawn_val / 100.0

        auto = st.checkbox("Flotte auto", value=fm.auto_mode, key="chk_auto")
        fm.auto_mode = auto
        if not auto:
            rv = st.slider("Robots actifs", 0, config.NUM_ROBOTS,
                           fm.active_limit, key="sl_robots")
            fm.active_limit = rv

    # ── Map editor ───────────────────────────────────────
    if not st.session_state.sim_initialized:
        st.divider()
        st.markdown(f"<div class='sec'>🗺️ Éditeur de Carte</div>", unsafe_allow_html=True)

        TOOLS = {
            "🧹 Sol":       "floor",
            "📦 Étagère L": "shelf_L",
            "📦 Étagère M": "shelf_M",
            "📦 Étagère H": "shelf_H",
            "⚡ Recharge":  "charger",
            "📥 Quai IN":   "drop_in",
            "📤 Quai OUT":  "drop_out",
        }
        sel = st.selectbox("Outil", list(TOOLS.keys()),
                           index=list(TOOLS.values()).index(st.session_state.editor_tool),
                           label_visibility="collapsed", key="tool_sel")
        st.session_state.editor_tool = TOOLS[sel]

        ca, cb = st.columns(2)
        with ca:
            if st.button("🎲 Aléatoire", key="btn_rnd"):
                _c, _k = {}, {}
                gw, gh = config.GRID_WIDTH, config.GRID_HEIGHT
                nc = random.randint(3, 7)
                sx = random.randint(1, gw - nc - 2)
                for i in range(nc): _c[(sx+i, 0)] = 'charger'
                nd = random.randint(1, 3)
                sy = random.randint(2, gh - nd*3 - 2)
                for i in range(nd):
                    yp = sy + i*3
                    _c[(gw-1, yp)] = 'drop_in'
                    _c[(gw-1, yp+1)] = 'drop_out'
                cats_avail = [config.CATEGORY_LIGHT, config.CATEGORY_MEDIUM, config.CATEGORY_HEAVY]
                for y in range(3, gh-2):
                    if y % 5 == 0: continue
                    for x in range(1, gw-3):
                        if x % 3 == 0 or (x,y) in _c: continue
                        if random.random() < 0.8:
                            cat = random.choice(cats_avail)
                            _c[(x,y)] = 'shelf'; _k[(x,y)] = cat
                st.session_state.map_cells = _c
                st.session_state.map_categories = _k
                st.session_state.map_ready = False
                st.rerun()
        with cb:
            if st.button("🔄 Effacer", key="btn_clr"):
                st.session_state.map_cells = {}
                st.session_state.map_categories = {}
                st.session_state.map_ready = False
                st.rerun()

        with st.expander("💾 JSON Import/Export"):
            up = st.file_uploader("Importer", type="json", key="up_json",
                                  label_visibility="collapsed")
            if up:
                try:
                    data = json.load(up)
                    _c, _k = {}, {}
                    for item in data:
                        pos = tuple(item['pos'])
                        _c[pos] = item['type']
                        if item.get('category'): _k[pos] = item['category']
                    st.session_state.map_cells = _c
                    st.session_state.map_categories = _k
                    st.session_state.map_ready = False
                    st.success("Importé !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {e}")
            if st.session_state.map_cells:
                exp = [{"pos":[x,y],"type":t,"category":st.session_state.map_categories.get((x,y))}
                       for (x,y),t in st.session_state.map_cells.items()]
                st.download_button("⬇️ Exporter", json.dumps(exp,indent=2),
                                   "warehouse_map.json", "application/json")

        if st.button("✅ Valider", key="btn_val"):
            raw = [{"pos":[x,y],"type":t,"category":st.session_state.map_categories.get((x,y))}
                   for (x,y),t in st.session_state.map_cells.items()]
            ok, err, parsed = MapValidator.validate(raw, config.GRID_WIDTH, config.GRID_HEIGHT)
            if ok:
                st.session_state.map_ready = True
                st.session_state.last_map_data = parsed
                st.success("Carte valide !")
            else:
                st.session_state.map_ready = False
                st.error(err)

# ─────────────────────────────────────────────────────────────────────────────
# Main — Map Editor view
# ─────────────────────────────────────────────────────────────────────────────
CAT_BG  = {config.CATEGORY_LIGHT:"#A5D6A7",config.CATEGORY_MEDIUM:"#FFCC80",config.CATEGORY_HEAVY:"#B0BEC5"}
CAT_LBL = {config.CATEGORY_LIGHT:"L",config.CATEGORY_MEDIUM:"M",config.CATEGORY_HEAVY:"H"}

if not st.session_state.sim_initialized:
    st.markdown(f"<div class='topbar'><div><div class='topbar-title'>🏭 Warehouse Control Center</div><div class='topbar-sub'>Éditeur de carte — cliquez Aléatoire + Valider + Lancer</div></div></div>", unsafe_allow_html=True)

    gw, gh = config.GRID_WIDTH, config.GRID_HEIGHT
    cells, cats = st.session_state.map_cells, st.session_state.map_categories
    cell_size = 26

    rows = []
    for gy in range(gh-1, -1, -1):
        row = []
        for gx in range(gw):
            ctype = cells.get((gx,gy),"floor")
            cat   = cats.get((gx,gy))
            if ctype == "floor":       bg,fg,lbl = ("#1f2937","#374151","") if dark else ("#e5e7eb","#9ca3af","")
            elif ctype == "shelf":     bg,fg,lbl = CAT_BG.get(cat,"#888"),"#111827",CAT_LBL.get(cat,"?")
            elif ctype == "charger":   bg,fg,lbl = "#4ADE80","#052E16","⚡"
            elif ctype == "drop_in":   bg,fg,lbl = "#EF4444","#fff","IN"
            elif ctype == "drop_out":  bg,fg,lbl = "#3B82F6","#fff","OUT"
            else:                      bg,fg,lbl = "#1f2937","#374151",""
            row.append(f'<td style="background:{bg};color:{fg};width:{cell_size}px;height:{cell_size}px;text-align:center;vertical-align:middle;font-size:8px;font-weight:700;border:1px solid {"#374151" if dark else "#d1d5db"};border-radius:2px;" title="{ctype}({gx},{gy})">{lbl}</td>')
        rows.append("<tr>"+"".join(row)+"</tr>")

    st.markdown(f'<div style="overflow:auto;max-height:calc(100vh - 140px);border:1px solid {BORDER};border-radius:10px;background:{MAP_BG};padding:4px;"><table style="border-collapse:collapse;table-layout:fixed;width:{gw*cell_size}px;">{"".join(rows)}</table></div>', unsafe_allow_html=True)

    st.markdown("---")
    with st.form("cell_edit"):
        c1,c2,c3 = st.columns([1,1,2])
        with c1: ex = st.number_input("X", 0, gw-1, 0, step=1, key="ex")
        with c2: ey = st.number_input("Y", 0, gh-1, 0, step=1, key="ey")
        with c3: sub = st.form_submit_button("🖊 Appliquer")
        if sub:
            tool = st.session_state.editor_tool
            pos = (int(ex),int(ey))
            if tool == "floor":
                cells.pop(pos,None); cats.pop(pos,None)
            elif tool.startswith("shelf_"):
                cm = {"shelf_L":config.CATEGORY_LIGHT,"shelf_M":config.CATEGORY_MEDIUM,"shelf_H":config.CATEGORY_HEAVY}
                cells[pos] = "shelf"; cats[pos] = cm[tool]
            else:
                cells[pos] = tool; cats.pop(pos,None)
            st.session_state.map_cells = cells
            st.session_state.map_categories = cats
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Main — Simulation Dashboard
# ─────────────────────────────────────────────────────────────────────────────
else:
    fm: FleetManager = st.session_state.fm
    wm: WarehouseMap = st.session_state.wm

    STATE_META = {
        RobotState.IDLE:     ("Repos",    "#9CA3AF"),
        RobotState.MOVING:   ("Mouvement","#F59E0B"),
        RobotState.LOADING:  ("Charge",   "#60A5FA"),
        RobotState.CHARGING: ("Recharge", "#4ADE80"),
        RobotState.RETURNING:("Retour",   "#EF4444"),
    }

    TICKS_PER_FRAME = max(1, config.TICK_RATE // 15)
    FRAME_DELAY = 1.0 / 15

    # ── Topbar: title + status + KPIs ────────────
    badge = ('<span class="badge-live"><span class="dot"></span>LIVE</span>' if st.session_state.sim_running else
             '<span class="badge-pause">⏸ PAUSE</span>')

    om = fm.order_manager
    kpis = [
        (om.completed_count, "Livrées"),
        (om.late_count,      "En retard"),
        (fm.conflicts_avoided,"Conflits"),
        (len(om.active_orders),"En cours"),
        (st.session_state.tick, "Ticks"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="kpi-v">{v}</div><div class="kpi-l">{l}</div></div>' for v,l in kpis)

    st.markdown(f"""
    <div class="topbar">
      <div style="display:flex;align-items:center;gap:10px;">
        <span class="topbar-title">🏭 Warehouse Control</span>
        {badge}
      </div>
    </div>
    <div class="kpi-strip">{kpi_html}</div>
    """, unsafe_allow_html=True)

    col_map, col_bots = st.columns([3, 2])

    with col_map:
        st.markdown(f'<div class="sec">🗺️ Carte Temps Réel</div>', unsafe_allow_html=True)
        map_ph = st.empty()

    with col_bots:
        st.markdown(f'<div class="sec">🤖 Flotte</div>', unsafe_allow_html=True)
        bots_ph = st.empty()
        st.markdown(f'<div class="sec" style="margin-top:6px;">📋 Commandes</div>', unsafe_allow_html=True)
        orders_ph = st.empty()

    # ── Main loop ────────────────────────────────
    while True:
        if st.session_state.sim_running:
            for _ in range(TICKS_PER_FRAME):
                fm.update()
                st.session_state.tick += 1

        # Map SVG
        svg = generate_warehouse_svg(wm, fm, width=520, height=400)
        map_ph.markdown(f'<div class="map-wrap">{svg}</div>', unsafe_allow_html=True)

        # Robot cards
        cards = []
        for r in fm.robots:
            lbl, col = STATE_META.get(r.state, ("?", "#6B7280"))
            batt  = int(r.battery_level)
            bcol  = "#4ADE80" if batt > 50 else ("#F59E0B" if batt > 25 else "#EF4444")
            lpct  = int(r.current_weight / config.ROBOT_MAX_CAPACITY * 100) if config.ROBOT_MAX_CAPACITY else 0
            inv_str = f"{r.current_weight}/{config.ROBOT_MAX_CAPACITY} kg"
            cards.append(f"""
<div class="robot-card">
  <div class="robot-top">
    <span class="robot-id">R{r.robot_id}</span>
    <span class="robot-state" style="background:{col}22;color:{col};">{lbl}</span>
  </div>
  <div class="robot-meta">🔋 {batt}% &nbsp;|&nbsp; 📦 {inv_str}</div>
  <div class="bar-wrap"><div style="background:{bcol};height:3px;border-radius:3px;width:{batt}%;"></div></div>
  <div class="bar-wrap"><div style="background:#60a5fa;height:3px;border-radius:3px;width:{lpct}%;"></div></div>
</div>""")
        bots_ph.markdown("".join(cards), unsafe_allow_html=True)

        # Orders table
        orders = om.active_orders
        if not orders:
            orders_ph.markdown(f'<div style="color:{TEXT_MUTED};font-size:11px;padding:8px 0;">Aucune commande active.</div>', unsafe_allow_html=True)
        else:
            hdr = f'<div class="order-header"><span>#ID</span><span>Prio</span><span>Poids</span><span>Avancement</span><span>Timer</span></div>'
            rows = []
            for o in orders[:15]:
                picked = sum(1 for i in o.items if i.picked_up)
                total  = len(o.items)
                pct    = int(picked/total*100) if total else 0
                t_str  = "RETARD ⚠" if o.is_late else str(o.deadline_timer)
                pcol   = "#EF4444" if o.priority >= 8 else ("#F59E0B" if o.priority >= 5 else TEXT_MUTED)
                rows.append(f"""
<div class="order-row {'late' if o.is_late else ''}">
  <span style="color:{TEXT};">#{o.order_id}</span>
  <span style="color:{pcol};font-weight:700;">P{o.priority}</span>
  <span style="color:{TEXT_MUTED};">{o.total_weight}kg</span>
  <div style="background:{BORDER};border-radius:3px;height:5px;"><div style="background:#4ADE80;height:5px;border-radius:3px;width:{pct}%;"></div></div>
  <span style="color:{'#EF4444' if o.is_late else TEXT_MUTED};text-align:right;">{t_str}</span>
</div>""")
            orders_ph.markdown(f'<div class="orders-wrap">{hdr}{"".join(rows)}</div>', unsafe_allow_html=True)

        time.sleep(FRAME_DELAY)
        st.rerun()
