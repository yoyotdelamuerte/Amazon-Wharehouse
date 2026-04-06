"""
Amazon Warehouse Simulation - Streamlit Dashboard
Run with: streamlit run app.py
"""

import streamlit as st
import time
import json
import random
import math
import config
from map_validator import MapValidator
from warehouse_map import WarehouseMap
from fleet_manager import FleetManager
from robot_agent import RobotState
from st_visualizer import generate_warehouse_svg

# ─────────────────────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Amazon Warehouse Control Center",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS – Dark Premium Dashboard
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Dark background */
  .stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    min-height: 100vh;
  }

  /* Header */
  .dashboard-header {
    background: linear-gradient(90deg, #1f2937 0%, #111827 100%);
    border: 1px solid #374151;
    border-radius: 12px;
    padding: 18px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  }

  .dashboard-title {
    font-size: 24px;
    font-weight: 700;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
  }

  /* KPI Cards */
  .kpi-card {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 4px 0;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    transition: border-color 0.2s;
  }
  .kpi-card:hover { border-color: #f59e0b; }
  .kpi-value {
    font-size: 32px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    background: linear-gradient(135deg, #f59e0b, #fbbf24);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .kpi-label {
    font-size: 12px;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500;
    margin-top: 4px;
  }

  /* Section titles */
  .section-title {
    font-size: 13px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #1f2937;
  }

  /* Robot status pills */
  .robot-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    margin: 2px;
    white-space: nowrap;
  }

  /* Map container */
  .map-container {
    border: 1px solid #374151;
    border-radius: 12px;
    overflow: hidden;
    background: #0d1117;
  }

  /* Data table */
  .order-table-row {
    background: #1f2937;
    border-radius: 6px;
    padding: 6px 10px;
    margin: 2px 0;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    border-left: 3px solid #374151;
  }
  .order-row-late { border-left-color: #ef4444 !important; }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #1f2937;
  }
  section[data-testid="stSidebar"] .stMarkdown { color: #d1d5db; }

  /* Buttons */
  .stButton > button {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #000;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s;
    width: 100%;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245,158,11,0.4);
  }

  /* Green launch button override */
  [data-testid="baseButton-secondary"] {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    color: white !important;
  }

  /* Slider */
  .stSlider > div { color: #d1d5db; }

  /* Status badge */
  .status-live {
    display: inline-flex; align-items: center; gap: 6px;
    background: #052e16; border: 1px solid #166534;
    border-radius: 9999px; padding: 4px 14px;
    font-size: 12px; font-weight: 600; color: #4ade80;
  }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #4ade80;
    animation: pulse-green 1.5s infinite;
  }
  @keyframes pulse-green {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  /* Hide Streamlit defaults */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "sim_running": False,
        "sim_initialized": False,
        "wm": None,
        "fm": None,
        "tick": 0,
        "map_cells": {},   # (x,y) -> type string (for editor)
        "map_categories": {},  # (x,y) -> category
        "editor_tool": "floor",
        "map_ready": False,
        "last_map_data": None,
        "error_msg": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar – Map Editor & Controls
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px 0;">
      <div style="font-size:28px;">🏭</div>
      <div style="font-size:16px; font-weight:700; color:#f59e0b;">Warehouse Control</div>
      <div style="font-size:11px; color:#6b7280;">Simulation Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Simulation Controls ──────────────────────────────
    st.markdown('<div class="section-title">⚙️ Simulation</div>', unsafe_allow_html=True)

    if not st.session_state.sim_initialized:
        if st.session_state.map_ready:
            if st.button("🚀 Lancer la Simulation", key="btn_launch"):
                # Initialize simulation objects
                parsed = st.session_state.last_map_data
                config.MAP_SHELVES = parsed['shelves']
                config.MAP_DROPS = parsed['drops']
                config.MAP_CHARGERS = parsed['chargers']
                config.NUM_ROBOTS = len(config.MAP_CHARGERS)
                wm = WarehouseMap()
                fm = FleetManager(wm)
                st.session_state.wm = wm
                st.session_state.fm = fm
                st.session_state.sim_initialized = True
                st.session_state.sim_running = True
                st.session_state.tick = 0
                st.rerun()
        else:
            st.info("⬇️ Configurez et validez la carte ci-dessous d'abord.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.session_state.sim_running:
                if st.button("⏸ Pause"):
                    st.session_state.sim_running = False
            else:
                if st.button("▶️ Reprendre"):
                    st.session_state.sim_running = True
        with col_b:
            if st.button("🔄 Reset"):
                for key in ["sim_running","sim_initialized","wm","fm","tick","map_ready","last_map_data","error_msg"]:
                    if key in ["sim_running","sim_initialized","map_ready"]:
                        st.session_state[key] = False
                    elif key in ["tick"]:
                        st.session_state[key] = 0
                    else:
                        st.session_state[key] = None
                # Reset Order counter
                from order_manager import Order
                Order._id_counter = 0
                st.rerun()

    st.divider()

    # ── Live Controls (when sim running) ────────────────
    if st.session_state.sim_initialized and st.session_state.fm:
        st.markdown('<div class="section-title">🎛️ Contrôles Temps Réel</div>', unsafe_allow_html=True)
        fm = st.session_state.fm

        spawn_val = st.slider(
            "📦 Taux de Génération des Commandes",
            min_value=0, max_value=100,
            value=int(fm.order_manager.spawn_chance * 100),
            format="%d%%",
            key="slider_spawn"
        )
        fm.order_manager.spawn_chance = spawn_val / 100.0

        auto_mode = st.checkbox("🤖 Gestion Automatique de la Flotte", value=fm.auto_mode, key="chk_auto")
        fm.auto_mode = auto_mode

        if not auto_mode:
            robots_val = st.slider(
                "🤖 Robots Actifs",
                min_value=0, max_value=config.NUM_ROBOTS,
                value=fm.active_limit,
                key="slider_robots"
            )
            fm.active_limit = robots_val

        st.divider()

    # ── Map Editor ──────────────────────────────────────
    if not st.session_state.sim_initialized:
        st.markdown('<div class="section-title">🗺️ Éditeur de Carte</div>', unsafe_allow_html=True)

        tool_options = {
            "🧹 Sol (Effacer)": "floor",
            "📦 Étagère Légère (L)": "shelf_L",
            "📦 Étagère Moyenne (M)": "shelf_M",
            "📦 Étagère Lourde (H)": "shelf_H",
            "⚡ Station de Recharge": "charger",
            "📥 Quai IN": "drop_in",
            "📤 Quai OUT": "drop_out",
        }
        selected_label = st.selectbox(
            "Outil actif",
            list(tool_options.keys()),
            index=list(tool_options.values()).index(st.session_state.editor_tool),
            key="tool_select"
        )
        st.session_state.editor_tool = tool_options[selected_label]

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 Carte Aléatoire", key="btn_random"):
                _cells, _cats = {}, {}
                gw, gh = config.GRID_WIDTH, config.GRID_HEIGHT
                num_chargers = random.randint(3, 7)
                start_x = random.randint(1, gw - num_chargers - 2)
                for i in range(num_chargers):
                    _cells[(start_x + i, 0)] = 'charger'
                num_drops = random.randint(1, 3)
                drop_x = gw - 1
                start_y = random.randint(2, gh - num_drops * 3 - 2)
                for i in range(num_drops):
                    y_pos = start_y + i * 3
                    _cells[(drop_x, y_pos)] = 'drop_in'
                    _cells[(drop_x, y_pos + 1)] = 'drop_out'
                shelf_categories = [config.CATEGORY_LIGHT, config.CATEGORY_MEDIUM, config.CATEGORY_HEAVY]
                for y in range(3, gh - 2):
                    if y % 5 == 0:
                        continue
                    for x in range(1, gw - 3):
                        if x % 3 == 0:
                            continue
                        if (x, y) not in _cells and random.random() < 0.8:
                            cat = random.choice(shelf_categories)
                            _cells[(x, y)] = 'shelf'
                            _cats[(x, y)] = cat
                st.session_state.map_cells = _cells
                st.session_state.map_categories = _cats
                st.session_state.map_ready = False
                st.session_state.error_msg = None
                st.rerun()

        with col2:
            if st.button("🔄 Effacer", key="btn_clear"):
                st.session_state.map_cells = {}
                st.session_state.map_categories = {}
                st.session_state.map_ready = False
                st.session_state.error_msg = None
                st.rerun()

        # JSON Import/Export
        with st.expander("💾 Importer / Exporter JSON"):
            uploaded = st.file_uploader("Charger un fichier JSON", type="json", key="map_upload")
            if uploaded:
                try:
                    data = json.load(uploaded)
                    _cells, _cats = {}, {}
                    for item in data:
                        pos = tuple(item['pos'])
                        _cells[pos] = item['type']
                        if item.get('category'):
                            _cats[pos] = item['category']
                    st.session_state.map_cells = _cells
                    st.session_state.map_categories = _cats
                    st.session_state.map_ready = False
                    st.success("Carte importée !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur d'import: {e}")

            # Export button
            if st.session_state.map_cells:
                export_data = []
                for (x, y), t in st.session_state.map_cells.items():
                    export_data.append({
                        "pos": [x, y],
                        "type": t,
                        "category": st.session_state.map_categories.get((x, y))
                    })
                st.download_button(
                    "⬇️ Exporter JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name="warehouse_map.json",
                    mime="application/json"
                )

        # Validate
        if st.button("✅ Valider & Préparer", key="btn_validate"):
            map_data_list = []
            for (x, y), t in st.session_state.map_cells.items():
                map_data_list.append({
                    "pos": [x, y],
                    "type": t,
                    "category": st.session_state.map_categories.get((x, y))
                })
            is_valid, err_msg, parsed = MapValidator.validate(
                map_data_list, config.GRID_WIDTH, config.GRID_HEIGHT
            )
            if is_valid:
                st.session_state.map_ready = True
                st.session_state.last_map_data = parsed
                st.session_state.error_msg = None
                st.success("✅ Carte valide ! Cliquez sur Lancer la Simulation.")
            else:
                st.session_state.map_ready = False
                st.session_state.error_msg = err_msg
                st.error(f"❌ {err_msg}")

# ─────────────────────────────────────────────────────────────────────────────
# Main Content Area
# ─────────────────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="dashboard-header">
  <span style="font-size:30px;">🏭</span>
  <div>
    <h1 class="dashboard-title">Amazon Warehouse Control Center</h1>
    <div style="font-size:12px; color:#6b7280; margin-top:2px;">Automated Robot Fleet Logistics Simulator</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── State: not initialized ─────────────────────────────────────────────────
if not st.session_state.sim_initialized:
    # Show the interactive map editor
    st.markdown('<div class="section-title">🗺️ Éditeur de Carte — Cliquez sur une cellule pour changer son type</div>', unsafe_allow_html=True)

    # Build the click-based grid editor using st.columns + st.button
    cells = st.session_state.map_cells
    cats = st.session_state.map_categories

    TOOL_COLORS = {
        "floor":   ("#E5E7EB", "#374151"),
        "shelf_L": ("#A5D6A7", "#1B5E20"),
        "shelf_M": ("#FFCC80", "#E65100"),
        "shelf_H": ("#B0BEC5", "#263238"),
        "charger": ("#4ADE80", "#052E16"),
        "drop_in": ("#F87171", "#7F1D1D"),
        "drop_out":("#60A5FA", "#1E3A5F"),
    }

    TYPE_TO_TOOL_KEY = {
        "floor": "floor", "shelf": None,
        "charger": "charger", "drop_in": "drop_in", "drop_out": "drop_out"
    }

    CELL_EMOJI = {
        "floor": "", "charger": "⚡", "drop_in": "IN", "drop_out": "OUT"
    }
    CAT_LABEL = {
        config.CATEGORY_LIGHT: "L", config.CATEGORY_MEDIUM: "M", config.CATEGORY_HEAVY: "H"
    }
    CAT_BG = {
        config.CATEGORY_LIGHT: "#A5D6A7", config.CATEGORY_MEDIUM: "#FFCC80", config.CATEGORY_HEAVY: "#B0BEC5"
    }

    gw = config.GRID_WIDTH
    gh = config.GRID_HEIGHT

    # Render the grid
    # We use a compact HTML grid table to avoid st.columns overhead and be faster
    tool = st.session_state.editor_tool
    cell_size = 30

    # Build HTML table
    html_rows = []
    clicked_pos = None  # Will be captured via form

    # Use a form so each click triggers a full rerun
    with st.form("map_editor_form", clear_on_submit=False):
        # We render an HTML preview + a text input trick for click detection
        # Better approach: use a selectbox of cells
        
        # Build the SVG preview of the current map state
        gw_px = gw * cell_size
        gh_px = gh * cell_size

        table_rows = []
        for gy in range(gh - 1, -1, -1):
            row_cells = []
            for gx in range(gw):
                ctype = cells.get((gx, gy), "floor")
                cat = cats.get((gx, gy))

                if ctype == "floor":
                    bg, fg = "#1f2937", "#374151"
                    label = ""
                elif ctype == "shelf":
                    bg = CAT_BG.get(cat, "#505050")
                    fg = "#111827"
                    label = CAT_LABEL.get(cat, "?")
                elif ctype == "charger":
                    bg, fg = "#4ADE80", "#052E16"
                    label = "⚡"
                elif ctype == "drop_in":
                    bg, fg = "#EF4444", "#fff"
                    label = "IN"
                elif ctype == "drop_out":
                    bg, fg = "#3B82F6", "#fff"
                    label = "OUT"
                else:
                    bg, fg = "#1f2937", "#374151"
                    label = ""

                cell_id = f"cell_{gx}_{gy}"
                border = "1px solid #374151"
                row_cells.append(
                    f'<td style="background:{bg};color:{fg};width:{cell_size}px;height:{cell_size}px;'
                    f'text-align:center;vertical-align:middle;font-size:9px;font-weight:700;'
                    f'border:{border};cursor:pointer;border-radius:2px;" '
                    f'title="{ctype} ({gx},{gy})">{label}</td>'
                )
            table_rows.append("<tr>" + "".join(row_cells) + "</tr>")

        table_html = (
            '<div style="overflow:auto; max-height:520px;">'
            f'<table style="border-collapse:collapse; table-layout:fixed; width:{gw_px}px;">'
            + "".join(table_rows) +
            "</table></div>"
        )
        st.markdown(table_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Modifier une cellule** (coordonnées X, Y — 0,0 = bas gauche) :")
        cols_edit = st.columns([1, 1, 1])
        with cols_edit[0]:
            edit_x = st.number_input("X", min_value=0, max_value=gw-1, value=0, step=1, key="edit_x")
        with cols_edit[1]:
            edit_y = st.number_input("Y", min_value=0, max_value=gh-1, value=0, step=1, key="edit_y")
        with cols_edit[2]:
            apply_btn = st.form_submit_button("🖊️ Appliquer l'outil")

        if apply_btn:
            ex, ey = int(edit_x), int(edit_y)
            current_tool = st.session_state.editor_tool
            if current_tool == 'floor':
                cells.pop((ex, ey), None)
                cats.pop((ex, ey), None)
            elif current_tool.startswith("shelf_"):
                cat_map = {"shelf_L": config.CATEGORY_LIGHT, "shelf_M": config.CATEGORY_MEDIUM, "shelf_H": config.CATEGORY_HEAVY}
                cells[(ex, ey)] = "shelf"
                cats[(ex, ey)] = cat_map[current_tool]
            else:
                cells[(ex, ey)] = current_tool
                cats.pop((ex, ey), None)
            st.session_state.map_cells = cells
            st.session_state.map_categories = cats
            st.rerun()

    st.caption("💡 Astuce: Utilisez **🎲 Carte Aléatoire** depuis la sidebar pour générer une carte instantanément, puis **✅ Valider & Préparer**.")

# ─── State: simulation running ───────────────────────────────────────────────
else:
    fm: FleetManager = st.session_state.fm
    wm: WarehouseMap = st.session_state.wm

    # ── KPI Row ─────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)

    def kpi(col, value, label):
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    kpi(k1, fm.order_manager.completed_count, "✅ Commandes livrées")
    kpi(k2, fm.order_manager.late_count, "⚠️ Commandes en retard")
    kpi(k3, fm.conflicts_avoided, "🛡️ Conflits évités")
    kpi(k4, len(fm.order_manager.active_orders), "📋 Commandes actives")
    kpi(k5, st.session_state.tick, "⏱ Ticks simulés")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Main Row: Visualisation + Robot Status ────────────────
    col_map, col_status = st.columns([2, 1])

    with col_map:
        status_badge = (
            '<span class="status-live"><span class="status-dot"></span>LIVE</span>'
            if st.session_state.sim_running else
            '<span style="background:#1f2937;border:1px solid #374151;border-radius:9999px;padding:4px 14px;font-size:12px;font-weight:600;color:#9ca3af;">⏸ PAUSE</span>'
        )
        st.markdown(f'<div class="section-title">🗺️ Carte en Temps Réel &nbsp;&nbsp;{status_badge}</div>', unsafe_allow_html=True)

        map_placeholder = st.empty()

    with col_status:
        st.markdown('<div class="section-title">🤖 Flotte de Robots</div>', unsafe_allow_html=True)
        robot_placeholder = st.empty()

    # ── Orders table ────────────────────────────────────
    st.markdown('<div class="section-title">📋 File des Commandes Active</div>', unsafe_allow_html=True)
    orders_placeholder = st.empty()

    # ─────────────────────────────────────────────────────────────────────────
    # Simulation Loop
    # ─────────────────────────────────────────────────────────────────────────
    FRAME_DELAY = 1.0 / 15  # Target ~15 FPS for web fluidity

    STATE_LABELS = {
        RobotState.IDLE: ("Repos", "#9CA3AF"),
        RobotState.MOVING: ("En Mouvement", "#F59E0B"),
        RobotState.LOADING: ("Chargement", "#60A5FA"),
        RobotState.CHARGING: ("Recharge", "#4ADE80"),
        RobotState.RETURNING: ("Retour Base", "#EF4444"),
    }

    # We run ticks per frame to speed up virtual time at lower visual FPS
    TICKS_PER_FRAME = max(1, config.TICK_RATE // 15)

    while True:
        if st.session_state.sim_running:
            for _ in range(TICKS_PER_FRAME):
                fm.update()
                st.session_state.tick += 1

        # ── Render Map ──
        svg = generate_warehouse_svg(wm, fm, width=580, height=520)
        map_placeholder.markdown(
            f'<div class="map-container">{svg}</div>',
            unsafe_allow_html=True
        )

        # ── Render Robot Status ──
        robot_html_parts = []
        for r in fm.robots:
            label, color = STATE_LABELS.get(r.state, ("Inconnu", "#6B7280"))
            batt_pct = int(r.battery_level)
            batt_bar_color = "#4ADE80" if batt_pct > 50 else ("#F59E0B" if batt_pct > 25 else "#EF4444")
            load_pct = int((r.current_weight / config.ROBOT_MAX_CAPACITY) * 100) if config.ROBOT_MAX_CAPACITY > 0 else 0
            robot_html_parts.append(f"""
<div style="background:#1f2937;border:1px solid #374151;border-radius:8px;padding:10px 14px;margin-bottom:6px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span style="font-size:13px;font-weight:700;color:#f3f4f6;font-family:'JetBrains Mono',monospace;">
      🤖 Robot #{r.robot_id}
    </span>
    <span style="background:{color}22;color:{color};padding:2px 10px;border-radius:9999px;font-size:11px;font-weight:600;">
      {label}
    </span>
  </div>
  <div style="font-size:11px;color:#9ca3af;margin-bottom:4px;">
    Batterie: <span style="color:{batt_bar_color};font-weight:600;">{batt_pct}%</span>
    &nbsp;|&nbsp; Charge: <span style="color:#60a5fa;font-weight:600;">{r.current_weight}/{config.ROBOT_MAX_CAPACITY}</span>
  </div>
  <div style="background:#374151;border-radius:4px;height:4px;margin-bottom:3px;">
    <div style="background:{batt_bar_color};height:4px;border-radius:4px;width:{batt_pct}%;transition:width 0.3s;"></div>
  </div>
  <div style="background:#374151;border-radius:4px;height:4px;">
    <div style="background:#60a5fa;height:4px;border-radius:4px;width:{load_pct}%;transition:width 0.3s;"></div>
  </div>
</div>
""")
        robot_placeholder.markdown("".join(robot_html_parts), unsafe_allow_html=True)

        # ── Render Orders ──
        orders = fm.order_manager.active_orders
        if not orders:
            orders_placeholder.markdown(
                '<div style="color:#6b7280;font-size:13px;text-align:center;padding:20px;">Aucune commande active en ce moment.</div>',
                unsafe_allow_html=True
            )
        else:
            order_rows = []
            for o in orders[:20]:  # Show max 20
                picked = sum(1 for item in o.items if item.picked_up)
                total = len(o.items)
                timer_str = f"{o.deadline_timer}" if not o.is_late else "⚠️ EN RETARD"
                late_cls = " order-row-late" if o.is_late else ""
                prio_color = "#EF4444" if o.priority >= 8 else ("#F59E0B" if o.priority >= 5 else "#9CA3AF")
                progress_pct = int((picked / total) * 100) if total > 0 else 0
                order_rows.append(f"""
<div style="display:grid;grid-template-columns:70px 60px 80px 1fr 100px;gap:8px;align-items:center;
            background:#1f2937;border:1px solid #374151;border-radius:6px;padding:8px 14px;margin-bottom:4px;
            border-left:3px solid {'#EF4444' if o.is_late else '#374151'};">
  <span style="font-size:12px;font-weight:700;color:#f3f4f6;font-family:'JetBrains Mono',monospace;">#{o.order_id}</span>
  <span style="color:{prio_color};font-size:12px;font-weight:700;">P{o.priority}</span>
  <span style="color:#9ca3af;font-size:11px;">{o.total_weight} kg</span>
  <div style="background:#374151;border-radius:4px;height:6px;">
    <div style="background:#4ADE80;height:6px;border-radius:4px;width:{progress_pct}%;"></div>
  </div>
  <span style="color:{'#EF4444' if o.is_late else '#9ca3af'};font-size:11px;font-family:'JetBrains Mono',monospace;text-align:right;">{timer_str}</span>
</div>
""")
            orders_placeholder.markdown("".join(order_rows), unsafe_allow_html=True)

        time.sleep(FRAME_DELAY)
        st.rerun()
