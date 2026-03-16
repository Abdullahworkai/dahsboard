import streamlit as st
import json
import os
import io
import calendar
from datetime import datetime, date
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from supabase import create_client, Client

st.set_page_config(
    page_title="Abdullah's WorkOS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Supabase connection ───────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data(table: str, default: dict) -> dict:
    try:
        res = supabase.table(table).select("id, data").limit(1).execute()
        if res.data:
            return res.data[0]["data"]
    except Exception as e:
        st.warning(f"Could not load {table}: {e}")
    return default

def save_data(table: str, data: dict):
    try:
        res = supabase.table(table).select("id").limit(1).execute()
        if res.data:
            row_id = res.data[0]["id"]
            supabase.table(table).update({"data": data}).eq("id", row_id).execute()
        else:
            supabase.table(table).insert({"data": data}).execute()
    except Exception as e:
        st.error(f"Could not save to {table}: {e}")

def load_notes() -> list:
    try:
        res = supabase.table("notes").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.warning(f"Could not load notes: {e}")
        return []

def save_note(project: str, title: str, content: str, tags: list):
    try:
        supabase.table("notes").insert({
            "project": project,
            "title":   title,
            "content": content,
            "tags":    tags,
        }).execute()
    except Exception as e:
        st.error(f"Could not save note: {e}")

def delete_note(note_id: str):
    try:
        supabase.table("notes").delete().eq("id", note_id).execute()
    except Exception as e:
        st.error(f"Could not delete note: {e}")

# ── Load all data ─────────────────────────────────────────────────────────────
ogsm_data     = load_data("ogsm",     {"objectives": []})
tasks_data    = load_data("tasks",    {"tasks": []})
requests_data = load_data("requests", {"requests": []})


# ── LAVENDER THEME CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --bg:        #13111a;
    --bg2:       #1a1726;
    --bg3:       #221e32;
    --bg4:       #2a2540;
    --lav:       #b79eff;
    --lav2:      #9b7ff4;
    --lav3:      #7c5cbf;
    --lav-soft:  #e8deff;
    --lav-glow:  rgba(183,158,255,0.15);
    --rose:      #ff8fab;
    --mint:      #72efb0;
    --gold:      #ffd97d;
    --sky:       #89d4f5;
    --text:      #ede9ff;
    --muted:     #7b72a8;
    --border:    #2e2848;
    --shadow:    0 4px 28px rgba(0,0,0,0.5);
    --glow:      0 0 24px rgba(183,158,255,0.18);
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
h1,h2,h3,h4 {
    font-family: 'Playfair Display', serif !important;
    color: var(--lav-soft) !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1726 0%, #13111a 100%) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

.card {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
}
.card-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--lav-soft);
    margin-bottom: 6px;
}
.metric-card {
    background: linear-gradient(135deg, var(--bg3) 0%, var(--bg4) 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: var(--shadow), var(--glow);
}
.metric-num   { font-family: 'Playfair Display', serif; font-size: 2.6rem; font-weight: 700; line-height: 1; }
.metric-label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.12em; margin-top: 8px; }

.tag { display:inline-block; padding:3px 11px; border-radius:999px; font-size:0.7rem; font-weight:700; margin-right:5px; letter-spacing:0.04em; }
.tag-high   { background:rgba(255,143,171,0.18); color:#ff8fab; border:1px solid rgba(255,143,171,0.3); }
.tag-medium { background:rgba(255,217,125,0.18); color:#ffd97d; border:1px solid rgba(255,217,125,0.3); }
.tag-low    { background:rgba(114,239,176,0.18); color:#72efb0; border:1px solid rgba(114,239,176,0.3); }
.tag-todo   { background:rgba(183,158,255,0.18); color:#b79eff; border:1px solid rgba(183,158,255,0.3); }
.tag-inprog { background:rgba(137,212,245,0.18); color:#89d4f5; border:1px solid rgba(137,212,245,0.3); }
.tag-done   { background:rgba(114,239,176,0.18); color:#72efb0; border:1px solid rgba(114,239,176,0.3); }
.tag-scope  { background:rgba(255,143,171,0.12); color:#ff8fab; border:1px solid rgba(255,143,171,0.2); }

.stProgress > div > div { background: linear-gradient(90deg, var(--lav3), var(--lav)) !important; border-radius:999px !important; }
.stProgress > div { background: var(--bg4) !important; border-radius:999px !important; }

.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
}

.stButton>button {
    background: linear-gradient(135deg, var(--lav3), var(--lav2)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(124,92,191,0.4) !important;
}
.stButton>button:hover { opacity:0.88 !important; }

.stTabs [data-baseweb="tab"] { font-weight:600 !important; color:var(--muted) !important; }
.stTabs [aria-selected="true"] { color:var(--lav) !important; }
.stTabs [data-baseweb="tab-border"] { background:var(--lav) !important; }

.streamlit-expanderHeader {
    background: var(--bg3) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}

.stAlert { border-radius: 14px !important; }
hr { border-color: var(--border) !important; margin: 24px 0 !important; }

.kanban-col { background:var(--bg2); border:1px solid var(--border); border-radius:16px; padding:16px; min-height:220px; }
.kanban-header { font-size:0.8rem; font-weight:800; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid var(--border); }

.task-title { color: #e8deff !important; font-weight: 700; font-size: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── load data ─────────────────────────────────────────────────────────────────

pending_requests = [r for r in requests_data["requests"] if r.get("status") == "pending"]
badge_count = len(pending_requests)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:14px 0 28px 0;'>
        <div style='font-family:Playfair Display,serif;font-size:1.6rem;font-weight:700;
                    background:linear-gradient(135deg,#b79eff,#89d4f5);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>WorkOS</div>
        <div style='font-size:0.72rem;color:#7b72a8;margin-top:3px;letter-spacing:0.08em;'>ABDULLAH ALSUBAIE</div>
    </div>
    """, unsafe_allow_html=True)

    inbox_label = "📥 Inbox" + (f"  🔴 {badge_count}" if badge_count else "")
    page = st.radio("Navigate", [
        "🎯 Dashboard",
        "📋 My OGSM",
        "✅ My Tasks",
        "🗂️ Kanban Board",
        "📅 Gantt Chart",
        "📓 My Notes",
        "📊 Reports",
        "📆 Calendar",
        inbox_label,
        "🔗 Request a Task",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"<div style='font-size:0.72rem;color:#7b72a8;'>📅 {datetime.now().year} · Local JSON storage</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if page == "🎯 Dashboard":

    now  = datetime.now()
    hour = now.hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

    st.markdown(f"""
    <div style='margin-bottom:32px;'>
        <div style='font-family:Playfair Display,serif;font-size:2.2rem;font-weight:700;
                    background:linear-gradient(135deg,#e8deff,#b79eff,#89d4f5);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            {greeting}, Abdullah
        </div>
        <div style='color:#7b72a8;margin-top:4px;font-size:0.95rem;'>
            {now.strftime('%A, %d %B %Y')} &nbsp;·&nbsp; Here's your year at a glance
        </div>
    </div>
    """, unsafe_allow_html=True)

    tasks      = tasks_data["tasks"]
    objectives = ogsm_data.get("objectives", [])
    today      = now.date()

    total_tasks  = len(tasks)
    done_tasks   = len([t for t in tasks if t.get("status") == "Done"])
    inprog_tasks = len([t for t in tasks if t.get("status") == "In Progress"])
    todo_tasks   = len([t for t in tasks if t.get("status") == "To Do"])
    scope_tasks  = len([t for t in tasks if t.get("project") == "Out of Scope"])
    overdue_list = [t for t in tasks
                    if t.get("due_date") and t.get("status") != "Done"
                    and datetime.strptime(t["due_date"], "%Y-%m-%d").date() < today]

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for col, num, label, color in [
        (c1, total_tasks,        "Total Tasks",   "#b79eff"),
        (c2, done_tasks,         "Completed",     "#72efb0"),
        (c3, inprog_tasks,       "In Progress",   "#89d4f5"),
        (c4, todo_tasks,         "To Do",         "#ffd97d"),
        (c5, len(overdue_list),  "Overdue",       "#ff8fab"),
        (c6, scope_tasks,        "Out of Scope",  "#c084fc"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-num" style="color:{color};">{num}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── ROW 2: OGSM compact scroll (left) + bar chart (right) ──
    left, right = st.columns([1, 1])

    with left:
        st.markdown("<h3>My OGSM Progress</h3>", unsafe_allow_html=True)
        if not objectives:
            st.info("Add OGSM projects in **My OGSM** to see progress here.")
        else:
            # Show first 5, rest hidden in expander
            visible = objectives[:5]
            hidden  = objectives[5:]
            for obj in visible:
                obj_tasks = [t for t in tasks if t.get("project") == obj["name"]]
                done_n  = len([t for t in obj_tasks if t.get("status") == "Done"])
                total_n = len(obj_tasks)
                remain  = total_n - done_n
                pct     = int((done_n / total_n * 100) if total_n else 0)
                col_color = obj.get("color","#b79eff")
                na, nb = st.columns([3, 1])
                na.markdown(
                    f"<div style='border-left:3px solid {col_color};padding-left:10px;margin-bottom:2px;'>"
                    f"<span style='font-weight:700;color:#e8deff;font-size:0.88rem;'>{obj['name']}</span>"
                    f"<span style='font-size:0.72rem;color:#7b72a8;margin-left:8px;'>✅ {done_n} · 🔄 {remain} · {total_n} total</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                nb.markdown(f"<div style='text-align:right;color:{col_color};font-weight:700;font-size:0.88rem;padding-top:2px;'>{pct}%</div>", unsafe_allow_html=True)
                st.progress(pct / 100)
                st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

            if hidden:
                with st.expander(f"+ {len(hidden)} more projects"):
                    for obj in hidden:
                        obj_tasks = [t for t in tasks if t.get("project") == obj["name"]]
                        done_n  = len([t for t in obj_tasks if t.get("status") == "Done"])
                        total_n = len(obj_tasks)
                        remain  = total_n - done_n
                        pct     = int((done_n / total_n * 100) if total_n else 0)
                        col_color = obj.get("color","#b79eff")
                        na, nb = st.columns([3, 1])
                        na.markdown(
                            f"<div style='border-left:3px solid {col_color};padding-left:10px;margin-bottom:2px;'>"
                            f"<span style='font-weight:700;color:#e8deff;font-size:0.88rem;'>{obj['name']}</span>"
                            f"<span style='font-size:0.72rem;color:#7b72a8;margin-left:8px;'>✅ {done_n} · 🔄 {remain} · {total_n} total</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        nb.markdown(f"<div style='text-align:right;color:{col_color};font-weight:700;font-size:0.88rem;padding-top:2px;'>{pct}%</div>", unsafe_allow_html=True)
                        st.progress(pct / 100)
                        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

    with right:
        st.markdown("<h3>Tasks by Project</h3>", unsafe_allow_html=True)
        proj_labels, proj_done_vals, proj_remain_vals = [], [], []
        for obj in objectives:
            obj_tasks = [t for t in tasks if t.get("project") == obj["name"]]
            d = len([t for t in obj_tasks if t.get("status") == "Done"])
            r = len(obj_tasks) - d
            proj_labels.append(obj["name"][:14])
            proj_done_vals.append(d)
            proj_remain_vals.append(r)
        oos = [t for t in tasks if t.get("project") == "Out of Scope"]
        if oos:
            oos_d = len([t for t in oos if t.get("status") == "Done"])
            proj_labels.append("Out of Scope")
            proj_done_vals.append(oos_d)
            proj_remain_vals.append(len(oos) - oos_d)
        if proj_labels:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Done",      x=proj_labels, y=proj_done_vals,
                                 marker_color="#72efb0", marker_line_width=0))
            fig.add_trace(go.Bar(name="Remaining", x=proj_labels, y=proj_remain_vals,
                                 marker_color="#b79eff", marker_line_width=0))
            fig.update_layout(
                barmode="stack",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ede9ff", family="Plus Jakarta Sans"),
                margin=dict(t=10, b=60, l=10, r=10), height=340,
                legend=dict(orientation="h", y=1.06, font=dict(size=11)),
                xaxis=dict(color="#7b72a8", gridcolor="#2e2848", tickangle=-30),
                yaxis=dict(color="#7b72a8", gridcolor="#2e2848"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add tasks to projects to see this chart.")

    st.markdown("---")

    # ── ROW 3: Upcoming deadlines with action buttons ──
    st.markdown("<h3>⏰ Upcoming Deadlines</h3>", unsafe_allow_html=True)
    upcoming = sorted(
        [t for t in tasks if t.get("due_date") and t.get("status") != "Done"],
        key=lambda x: x["due_date"]
    )[:4]

    if not upcoming:
        st.success("No upcoming deadlines — all clear, Abdullah!")
    else:
        dcols = st.columns(len(upcoming))
        for i, t in enumerate(upcoming):
            due_d     = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
            days_left = (due_d - today).days
            color     = "#ff8fab" if days_left <= 3 else ("#ffd97d" if days_left <= 7 else "#b79eff")
            urgency   = "Overdue!" if days_left < 0 else ("Due today!" if days_left == 0 else f"{days_left}d left")
            task_id   = t.get("id")
            edit_key  = f"dash_edit_{task_id}"

            with dcols[i]:
                st.markdown(f"""
                <div style='background:#221e32;border:1px solid #2e2848;border-top:3px solid {color};
                            border-radius:14px;padding:14px;text-align:center;margin-bottom:8px;'>
                    <div style='font-size:0.7rem;color:#7b72a8;margin-bottom:4px;'>{t.get('project','')[:22]}</div>
                    <div style='font-weight:700;color:#e8deff;font-size:0.88rem;margin-bottom:6px;'>{t['title'][:26]}</div>
                    <div style='color:{color};font-weight:700;font-size:0.82rem;'>{urgency}</div>
                    <div style='font-size:0.7rem;color:#7b72a8;margin-top:3px;'>{t["due_date"]}</div>
                </div>""", unsafe_allow_html=True)

                # Action buttons
                btn1, btn2 = st.columns(2)
                if btn1.button("✅ Done", key=f"dash_done_{task_id}"):
                    idx = next((j for j,x in enumerate(tasks_data["tasks"]) if x.get("id")==task_id), None)
                    if idx is not None:
                        tasks_data["tasks"][idx]["status"] = "Done"
                        save_data("tasks", tasks_data)
                        st.rerun()
                if btn2.button("✏️ Edit", key=f"dash_editbtn_{task_id}"):
                    st.session_state[edit_key] = not st.session_state.get(edit_key, False)

                # Inline edit form
                if st.session_state.get(edit_key, False):
                    with st.form(key=f"dash_form_{task_id}"):
                        new_title = st.text_input("Title", value=t.get("title",""))
                        new_due   = st.date_input("New Due Date",
                                                  value=datetime.strptime(t["due_date"],"%Y-%m-%d").date()
                                                  if t.get("due_date") else None)
                        new_prio  = st.selectbox("Priority", ["High","Medium","Low"],
                                                 index=["High","Medium","Low"].index(t.get("priority","Medium")))
                        new_stat  = st.selectbox("Status", ["To Do","In Progress","Done"],
                                                 index=["To Do","In Progress","Done"].index(t.get("status","To Do")))
                        s1, s2 = st.columns(2)
                        if s1.form_submit_button("💾 Save"):
                            idx = next((j for j,x in enumerate(tasks_data["tasks"]) if x.get("id")==task_id), None)
                            if idx is not None:
                                tasks_data["tasks"][idx].update({
                                    "title":    new_title,
                                    "due_date": str(new_due) if new_due else "",
                                    "priority": new_prio,
                                    "status":   new_stat,
                                    "updated_at": str(datetime.now()),
                                })
                                save_data("tasks", tasks_data)
                                st.session_state[edit_key] = False
                                st.success("Updated!")
                                st.rerun()
                        if s2.form_submit_button("Cancel"):
                            st.session_state[edit_key] = False
                            st.rerun()

    st.markdown("---")

    # ── ROW 4: Compact recent tasks (5 max) + link to full list ──
    st.markdown("<h3>🕐 Active Tasks</h3>", unsafe_allow_html=True)

    active = [t for t in tasks if t.get("status") != "Done"]
    active_sorted = sorted(active, key=lambda x: (x.get("due_date","9999"), x.get("created_at","")))[:5]

    if not active_sorted:
        st.success("All tasks are done — great work, Abdullah! 🎉")
    else:
        # Header row
        st.markdown("""
        <div style='display:grid;grid-template-columns:3fr 1.5fr 1fr 1fr;gap:8px;
                    padding:6px 12px;font-size:0.7rem;color:#7b72a8;
                    text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #2e2848;margin-bottom:4px;'>
            <div>Task</div><div>Project</div><div>Priority</div><div>Due</div>
        </div>""", unsafe_allow_html=True)

        for t in active_sorted:
            priority  = t.get("priority","Medium")
            due       = t.get("due_date","")
            p_cls     = f"tag-{priority.lower()}"
            task_id   = t.get("id")
            is_over   = due and datetime.strptime(due,"%Y-%m-%d").date() < today
            due_color = "#ff8fab" if is_over else "#7b72a8"
            title_str = t["title"][:40]

            # Row with inline done checkbox
            rc = st.columns([0.2, 3, 1.5, 1, 1])
            is_done_chk = t.get("status") == "Done"
            checked = rc[0].checkbox("", value=is_done_chk, key=f"dash_chk_{task_id}")
            if checked != is_done_chk:
                idx = next((j for j,x in enumerate(tasks_data["tasks"]) if x.get("id")==task_id), None)
                if idx is not None:
                    tasks_data["tasks"][idx]["status"] = "Done" if checked else "To Do"
                    save_data("tasks", tasks_data)
                    st.rerun()
            rc[1].markdown(f"<span style='font-size:0.88rem;color:#e8deff;font-weight:600;'>{title_str}</span>", unsafe_allow_html=True)
            rc[2].markdown(f"<span style='font-size:0.78rem;color:#7b72a8;'>{t.get('project','')[:16]}</span>", unsafe_allow_html=True)
            rc[3].markdown(f"<span class='tag {p_cls}'>{priority}</span>", unsafe_allow_html=True)
            rc[4].markdown(f"<span style='font-size:0.78rem;color:{due_color};'>{due or '—'}</span>", unsafe_allow_html=True)

        remaining_count = len(active) - len(active_sorted)
        if remaining_count > 0:
            st.markdown(f"<div style='text-align:center;margin-top:12px;'><a href='#' style='color:#b79eff;font-size:0.85rem;'>+{remaining_count} more tasks → go to My Tasks</a></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:right;margin-top:8px;font-size:0.78rem;color:#7b72a8;'>Showing {len(active_sorted)} of {len(active)} active tasks</div>", unsafe_allow_html=True)

    if badge_count:
        st.warning(f"📥 You have **{badge_count}** pending task request(s) in your inbox.")

# ════════════════════════════════════════════════════════════════════════════
# MY OGSM
# ════════════════════════════════════════════════════════════════════════════
elif page == "📋 My OGSM":
    st.markdown("<h1>My OGSM</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#7b72a8;margin-bottom:24px;'>Abdullah's Objectives, Goals, Strategies and Measures for the year.</div>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])

    with st.expander("Add New Project / Objective", expanded=not objectives):
        with st.form("add_obj"):
            n1, n2 = st.columns(2)
            name      = n1.text_input("Project Name *", placeholder="e.g. Udemy Learning")
            objective = n2.text_input("Objective *", placeholder="What do you want to achieve?")
            goal      = st.text_input("Goal", placeholder="Measurable outcome")
            strategy  = st.text_area("Strategy", placeholder="How will you get there?", height=80)
            measure   = st.text_input("KPI / Measure", placeholder="e.g. Complete 3 courses by Q3")
            m1, m2 = st.columns(2)
            target = m1.number_input("KPI Target (%)", 0, 100, 100)
            color  = m2.color_picker("Project Colour", "#b79eff")
            if st.form_submit_button("Save Project"):
                if name and objective:
                    objectives.append({
                        "id": len(objectives)+1, "name": name, "objective": objective,
                        "goal": goal, "strategy": strategy, "measure": measure,
                        "target": target, "color": color,
                        "created_at": str(datetime.now().date())
                    })
                    ogsm_data["objectives"] = objectives
                    save_data("ogsm", ogsm_data)
                    st.success(f"Project '{name}' added to your OGSM!")
                    st.rerun()
                else:
                    st.error("Name and Objective are required.")

    if objectives:
        st.markdown("### Abdullah's Projects")
        for i, obj in enumerate(objectives):
            with st.expander(f"{obj['name']}", expanded=False):
                tasks = tasks_data["tasks"]
                obj_tasks = [t for t in tasks if t.get("project") == obj["name"]]
                done_n  = len([t for t in obj_tasks if t.get("status") == "Done"])
                total_n = len(obj_tasks)
                pct     = int((done_n / total_n * 100) if total_n else 0)
                e1, e2  = st.columns([3,1])
                with e1:
                    st.markdown(f"""
                    <div class='card'>
                        <div style='font-size:0.72rem;color:#7b72a8;text-transform:uppercase;'>Objective</div>
                        <div style='margin-bottom:12px;color:#ede9ff;'>{obj.get('objective','—')}</div>
                        <div style='font-size:0.72rem;color:#7b72a8;text-transform:uppercase;'>Goal</div>
                        <div style='margin-bottom:12px;color:#ede9ff;'>{obj.get('goal','—')}</div>
                        <div style='font-size:0.72rem;color:#7b72a8;text-transform:uppercase;'>Strategy</div>
                        <div style='margin-bottom:12px;color:#ede9ff;'>{obj.get('strategy','—')}</div>
                        <div style='font-size:0.72rem;color:#7b72a8;text-transform:uppercase;'>KPI / Measure</div>
                        <div style='color:#ede9ff;'>{obj.get('measure','—')}</div>
                    </div>""", unsafe_allow_html=True)
                with e2:
                    st.markdown(f"""
                    <div class='metric-card' style='text-align:center;'>
                        <div class='metric-num' style='color:{obj.get("color","#b79eff")};'>{pct}%</div>
                        <div class='metric-label'>Progress</div>
                        <div style='margin-top:10px;font-size:0.8rem;color:#7b72a8;'>{done_n}/{total_n} tasks</div>
                    </div>""", unsafe_allow_html=True)
                    st.progress(pct/100)
                if st.button(f"Delete '{obj['name']}'", key=f"del_{i}"):
                    objectives.pop(i)
                    ogsm_data["objectives"] = objectives
                    save_data("ogsm", ogsm_data)
                    st.rerun()
    else:
        st.info("No projects yet. Add your first OGSM project above!")

# ════════════════════════════════════════════════════════════════════════════
# MY TASKS
# ════════════════════════════════════════════════════════════════════════════
elif page == "✅ My Tasks":
    st.markdown("<h1>My Tasks</h1>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])
    proj_names = [o["name"] for o in objectives] + ["Out of Scope"]
    tasks = tasks_data["tasks"]

    done_count = len([t for t in tasks if t.get("status") == "Done"])
    tab1, tab2, tab3 = st.tabs(["Add Task", "All Tasks", f"Completed ({done_count})"])

    with tab1:
        with st.form("add_task"):
            t1, t2 = st.columns(2)
            title   = t1.text_input("Task Title *")
            project = t2.selectbox("Project", proj_names if proj_names else ["Out of Scope"])
            desc    = st.text_area("Description / Reflection", height=80)
            c1, c2, c3 = st.columns(3)
            priority = c1.selectbox("Priority", ["High","Medium","Low"])
            status   = c2.selectbox("Status", ["To Do","In Progress","Done"])
            due_date = c3.date_input("Due Date", value=None)
            if st.form_submit_button("Save Task"):
                if title:
                    tasks.append({
                        "id":          len(tasks)+1,
                        "title":       title,
                        "project":     project,
                        "description": desc,
                        "priority":    priority,
                        "status":      status,
                        "due_date":    str(due_date) if due_date else "",
                        "created_at":  str(datetime.now()),
                    })
                    tasks_data["tasks"] = tasks
                    save_data("tasks", tasks_data)
                    st.success(f"Task '{title}' added successfully!")
                    st.rerun()
                else:
                    st.error("Task title is required.")

    with tab2:
        f1,f2,f3,f4 = st.columns(4)
        f_proj   = f1.selectbox("Project",  ["All"] + proj_names, key="fp")
        f_status = f2.selectbox("Status",   ["All","To Do","In Progress","Done"], key="fs")
        f_prio   = f3.selectbox("Priority", ["All","High","Medium","Low"], key="fpr")
        f_search = f4.text_input("Search", placeholder="keyword...", key="fsrch")

        filtered = tasks
        if f_proj   != "All": filtered = [t for t in filtered if t.get("project")  == f_proj]
        if f_status != "All": filtered = [t for t in filtered if t.get("status")   == f_status]
        if f_prio   != "All": filtered = [t for t in filtered if t.get("priority") == f_prio]
        if f_search:          filtered = [t for t in filtered if f_search.lower()  in t.get("title","").lower()]

        st.markdown(f"<div style='color:#7b72a8;margin:10px 0;font-size:0.85rem;'>{len(filtered)} task(s)</div>", unsafe_allow_html=True)

        for i, t in enumerate(sorted(filtered, key=lambda x: x.get("created_at",""), reverse=True)):
            priority = t.get("priority","Medium")
            status   = t.get("status","To Do")
            due      = t.get("due_date","")
            p_cls    = f"tag-{priority.lower()}"
            s_cls    = "tag-done" if status=="Done" else ("tag-inprog" if status=="In Progress" else "tag-todo")
            is_over  = due and status != "Done" and datetime.strptime(due, "%Y-%m-%d").date() < datetime.now().date()
            is_done  = status == "Done"
            task_id  = t.get("id")
            edit_key = f"edit_mode_{task_id}"

            # ── Row: quick-done checkbox + title + tags ──
            row_cols = st.columns([0.3, 4, 2, 1, 1])

            # Checkbox to toggle Done instantly
            checked = row_cols[0].checkbox(
                "", value=is_done, key=f"chk_{task_id}",
                help="Mark as Done / Undo"
            )
            if checked != is_done:
                new_st = "Done" if checked else "To Do"
                idx = next((j for j,x in enumerate(tasks_data["tasks"]) if x.get("id")==task_id), None)
                if idx is not None:
                    tasks_data["tasks"][idx]["status"] = new_st
                    save_data("tasks", tasks_data)
                    st.rerun()

            # Title + tags
            title_style = "text-decoration:line-through;color:#7b72a8;" if is_done else "color:#e8deff;font-weight:700;"
            overdue_badge = " 🔴" if is_over else ""
            row_cols[1].markdown(
                f"<span style='{title_style}font-size:0.95rem;'>{t['title']}{overdue_badge}</span>"
                f"&nbsp;<span class='tag {p_cls}'>{priority}</span>"
                f"&nbsp;<span class='tag {s_cls}'>{status}</span>",
                unsafe_allow_html=True
            )

            # Project + due date
            due_display = f"📅 {due}" if due else ""
            row_cols[2].markdown(
                f"<div style='font-size:0.78rem;color:#7b72a8;margin-top:6px;'>📁 {t.get('project','')}</div>"
                f"<div style='font-size:0.78rem;color:{'#ff8fab' if is_over else '#7b72a8'};'>{due_display}</div>",
                unsafe_allow_html=True
            )

            # Edit button
            if row_cols[3].button("✏️ Edit", key=f"editbtn_{task_id}"):
                st.session_state[edit_key] = not st.session_state.get(edit_key, False)

            # Delete button
            if row_cols[4].button("🗑️", key=f"del_t_{task_id}"):
                tasks_data["tasks"] = [x for x in tasks_data["tasks"] if x.get("id") != task_id]
                save_data("tasks", tasks_data)
                st.rerun()

            # ── Inline edit form (shown when edit mode active) ──
            if st.session_state.get(edit_key, False):
                with st.form(key=f"edit_form_{task_id}"):
                    st.markdown(f"<div style='font-size:0.8rem;color:#b79eff;font-weight:700;margin-bottom:8px;'>Editing: {t['title']}</div>", unsafe_allow_html=True)
                    e1, e2 = st.columns(2)
                    new_title   = e1.text_input("Title",   value=t.get("title",""))
                    new_project = e2.selectbox("Project",  proj_names,
                                               index=proj_names.index(t.get("project","Out of Scope"))
                                               if t.get("project") in proj_names else 0)
                    new_desc    = st.text_area("Description / Reflection",
                                               value=t.get("description",""), height=80)
                    f1, f2, f3  = st.columns(3)
                    new_priority = f1.selectbox("Priority", ["High","Medium","Low"],
                                                index=["High","Medium","Low"].index(t.get("priority","Medium")))
                    new_status_e = f2.selectbox("Status", ["To Do","In Progress","Done"],
                                                index=["To Do","In Progress","Done"].index(t.get("status","To Do")))
                    current_due  = None
                    if t.get("due_date"):
                        try: current_due = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
                        except: pass
                    new_due = f3.date_input("Due Date", value=current_due)

                    sa, sb = st.columns(2)
                    if sa.form_submit_button("💾 Save Changes"):
                        idx = next((j for j,x in enumerate(tasks_data["tasks"]) if x.get("id")==task_id), None)
                        if idx is not None:
                            tasks_data["tasks"][idx].update({
                                "title":       new_title,
                                "project":     new_project,
                                "description": new_desc,
                                "priority":    new_priority,
                                "status":      new_status_e,
                                "due_date":    str(new_due) if new_due else "",
                                "updated_at":  str(datetime.now()),
                            })
                            save_data("tasks", tasks_data)
                            st.session_state[edit_key] = False
                            st.success("Task updated!")
                            st.rerun()
                    if sb.form_submit_button("Cancel"):
                        st.session_state[edit_key] = False
                        st.rerun()

            st.markdown("<hr style='margin:6px 0;border-color:#2e2848;'>", unsafe_allow_html=True)


    with tab3:
        st.markdown("<div style='color:#7b72a8;margin-bottom:16px;font-size:0.88rem;'>All tasks you have marked as Done — your work log for the year.</div>", unsafe_allow_html=True)

        completed = [t for t in tasks if t.get("status") == "Done"]

        # Filters
        cf1, cf2, cf3 = st.columns(3)
        c_proj   = cf1.selectbox("Filter by Project", ["All"] + proj_names, key="cp")
        c_prio   = cf2.selectbox("Filter by Priority", ["All","High","Medium","Low"], key="cpr")
        c_search = cf3.text_input("Search", placeholder="keyword...", key="csrch")

        if c_proj   != "All": completed = [t for t in completed if t.get("project") == c_proj]
        if c_prio   != "All": completed = [t for t in completed if t.get("priority") == c_prio]
        if c_search:          completed = [t for t in completed if c_search.lower() in t.get("title","").lower()]

        completed = sorted(completed, key=lambda x: x.get("updated_at") or x.get("created_at",""), reverse=True)

        st.markdown(f"<div style='color:#72efb0;font-size:0.85rem;margin-bottom:12px;'>🎉 {len(completed)} completed task(s)</div>", unsafe_allow_html=True)

        if not completed:
            st.info("No completed tasks yet. Keep going, Abdullah!")
        else:
            for t in completed:
                priority  = t.get("priority","Medium")
                p_cls     = f"tag-{priority.lower()}"
                proj      = t.get("project","—")
                due       = t.get("due_date","")
                done_date = (t.get("updated_at") or t.get("created_at",""))[:10]
                desc      = t.get("description","")
                task_id   = t.get("id")

                with st.expander(f"✅  {t['title']}  ·  {proj}"):
                    ca, cb = st.columns([3,1])
                    with ca:
                        st.markdown(
                            f"<span class='tag {p_cls}'>{priority}</span>"
                            f"<span class='tag tag-done' style='margin-left:4px;'>Done</span>",
                            unsafe_allow_html=True
                        )
                        if desc:
                            st.markdown(f"<div style='margin-top:10px;color:#c4bce8;'>{desc}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='margin-top:10px;color:#7b72a8;font-style:italic;font-size:0.85rem;'>No reflection added</div>", unsafe_allow_html=True)
                    with cb:
                        st.markdown(
                            f"<div style='background:#1a1726;border:1px solid #2e2848;border-radius:12px;padding:12px;text-align:center;'>"
                            f"<div style='font-size:0.7rem;color:#7b72a8;text-transform:uppercase;letter-spacing:0.08em;'>Completed</div>"
                            f"<div style='font-weight:700;color:#72efb0;font-size:0.95rem;margin-top:4px;'>{done_date}</div>"
                            f"{'<div style=\'font-size:0.72rem;color:#7b72a8;margin-top:4px;\'>Due was ' + due + '</div>' if due else ''}"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    # Allow undo + delete
                    bu1, bu2 = st.columns(2)
                    if bu1.button("↩️ Undo (back to To Do)", key=f"undo_{task_id}"):
                        idx = next((j for j,x in enumerate(tasks_data["tasks"]) if x.get("id")==task_id), None)
                        if idx is not None:
                            tasks_data["tasks"][idx]["status"] = "To Do"
                            save_data("tasks", tasks_data)
                            st.rerun()
                    if bu2.button("🗑️ Delete", key=f"del_done_{task_id}"):
                        tasks_data["tasks"] = [x for x in tasks_data["tasks"] if x.get("id") != task_id]
                        save_data("tasks", tasks_data)
                        st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# KANBAN
# ════════════════════════════════════════════════════════════════════════════
elif page == "🗂️ Kanban Board":
    st.markdown("<h1>Kanban Board</h1>", unsafe_allow_html=True)
    objectives = ogsm_data.get("objectives", [])
    proj_names = [o["name"] for o in objectives] + ["Out of Scope"]
    tasks = tasks_data["tasks"]
    sel_proj = st.selectbox("Filter by Project", ["All"] + proj_names)
    filtered = tasks if sel_proj == "All" else [t for t in tasks if t.get("project") == sel_proj]
    todo   = [t for t in filtered if t.get("status") == "To Do"]
    inprog = [t for t in filtered if t.get("status") == "In Progress"]
    done   = [t for t in filtered if t.get("status") == "Done"]
    col1, col2, col3 = st.columns(3)
    for container, title, task_list, color in [
        (col1, "To Do",       todo,   "#b79eff"),
        (col2, "In Progress", inprog, "#89d4f5"),
        (col3, "Done",        done,   "#72efb0"),
    ]:
        with container:
            st.markdown(f'<div class="kanban-col"><div class="kanban-header" style="color:{color};">{title} &nbsp; {len(task_list)}</div>', unsafe_allow_html=True)
            for t in task_list:
                p     = t.get("priority","Medium")
                p_cls = f"tag-{p.lower()}"
                due   = t.get("due_date","")
                oos   = '<span class="tag tag-scope" style="font-size:0.62rem;">OOS</span>' if t.get("project")=="Out of Scope" else ""
                st.markdown(f"""
                <div class="card" style="padding:12px 14px;margin-bottom:10px;">
                    <div style="font-weight:700;font-size:0.88rem;color:#e8deff;margin-bottom:6px;">{t['title']}</div>
                    <span class="tag {p_cls}">{p}</span>{oos}
                    <div style='font-size:0.73rem;color:#7b72a8;margin-top:6px;'>📁 {t.get('project','')}</div>
                    {f"<div style='font-size:0.73rem;color:#7b72a8;'>📅 {due}</div>" if due else ""}
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# GANTT — uses plotly.express timeline (no scipy / figure_factory needed)
# ════════════════════════════════════════════════════════════════════════════
elif page == "📅 Gantt Chart":

    st.markdown("<h1>Gantt Chart</h1>", unsafe_allow_html=True)
    tasks = tasks_data["tasks"]
    gantt_tasks = [t for t in tasks if t.get("due_date") and t.get("created_at")]

    if not gantt_tasks:
        st.info("Add tasks with due dates to see the Gantt chart.")
    else:
        rows = []
        for t in gantt_tasks:
            try:
                start = t["created_at"][:10]
                end   = t["due_date"]
                if start <= end:
                    rows.append(dict(
                        Task=t["title"][:40],
                        Start=start,
                        Finish=end,
                        Project=t.get("project","Unknown"),
                        Status=t.get("status","To Do"),
                        Priority=t.get("priority","Medium"),
                    ))
            except:
                pass

        if rows:
            df = pd.DataFrame(rows)
            palette  = ["#b79eff","#ff8fab","#72efb0","#ffd97d","#89d4f5","#c084fc","#fb923c"]
            projects = df["Project"].unique()
            cmap     = {p: palette[i % len(palette)] for i, p in enumerate(projects)}

            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task",
                              color="Project", color_discrete_map=cmap,
                              hover_data=["Status","Priority","Project"])
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ede9ff", family="Plus Jakarta Sans"),
                height=max(350, len(rows)*36 + 80),
                margin=dict(l=200, r=20, t=30, b=60),
                xaxis=dict(color="#7b72a8", gridcolor="#2e2848"),
                yaxis=dict(color="#ede9ff"),
                legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No tasks with valid start/end date pairs found.")

# ════════════════════════════════════════════════════════════════════════════
# MY NOTES
# ════════════════════════════════════════════════════════════════════════════
elif page == "📓 My Notes":
    st.markdown("<h1>My Notes</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#7b72a8;margin-bottom:20px;'>Notes saved per project folder.</div>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])
    proj_names = [o["name"] for o in objectives] + ["Out of Scope"]

    tab1, tab2 = st.tabs(["Write Note", "Browse Notes"])

    with tab1:
        with st.form("add_note"):
            n1, n2  = st.columns(2)
            proj    = n1.selectbox("Project Folder", proj_names)
            title   = n2.text_input("Note Title *", placeholder="Quick summary")
            content = st.text_area("Note Content", height=200)
            tags    = st.text_input("Tags (comma separated)", placeholder="e.g. meeting, q2")
            if st.form_submit_button("Save Note"):
                if title and content:
                    tag_list = [x.strip() for x in tags.split(",") if x.strip()]
                    save_note(proj, title, content, tag_list)
                    st.success(f"Note saved to '{proj}' folder!")
                    st.rerun()
                else:
                    st.error("Title and content are required.")

    with tab2:
        sel_proj  = st.selectbox("Project Folder", ["All"] + proj_names, key="note_proj")
        all_notes = load_notes()
        if sel_proj != "All":
            all_notes = [n for n in all_notes if n.get("project") == sel_proj]
        search = st.text_input("Search notes", placeholder="keyword...")
        if search:
            all_notes = [n for n in all_notes
                         if search.lower() in n.get("title","").lower()
                         or search.lower() in n.get("content","").lower()]
        st.markdown(f"<div style='color:#7b72a8;font-size:0.85rem;margin:8px 0;'>{len(all_notes)} note(s)</div>", unsafe_allow_html=True)
        for note in all_notes:
            created = note.get("created_at","")[:10]
            with st.expander(f"{note['title']}  |  {note.get('project','')}  |  {created}"):
                st.markdown(note["content"])
                tags_val = note.get("tags") or []
                if isinstance(tags_val, str):
                    try: tags_val = json.loads(tags_val)
                    except: tags_val = []
                if tags_val:
                    st.markdown(" ".join([f"<span class='tag tag-todo'>{tg}</span>" for tg in tags_val]), unsafe_allow_html=True)
                if st.button("Delete Note", key=f"dn_{note['id']}"):
                    delete_note(note["id"]); st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# REPORTS — only go/px, no figure_factory
# ════════════════════════════════════════════════════════════════════════════
elif page == "📊 Reports":

    st.markdown("<h1>Reports</h1>", unsafe_allow_html=True)
    tasks      = tasks_data["tasks"]
    objectives = ogsm_data.get("objectives", [])

    if not tasks:
        st.info("No tasks yet. Add tasks to generate reports.")
    else:
        tab1, tab2, tab3 = st.tabs(["Overview", "Weekly / Monthly", "Export"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                statuses = [t.get("status","To Do") for t in tasks]
                sc = {s: statuses.count(s) for s in ["To Do","In Progress","Done"]}
                fig = go.Figure(go.Pie(
                    labels=list(sc.keys()), values=list(sc.values()),
                    hole=0.55, marker_colors=["#b79eff","#89d4f5","#72efb0"]
                ))
                fig.update_layout(title="Tasks by Status",
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#ede9ff"),
                                  margin=dict(t=50,b=20,l=20,r=20))
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                priorities = [t.get("priority","Medium") for t in tasks]
                pc = {p: priorities.count(p) for p in ["High","Medium","Low"]}
                fig2 = go.Figure(go.Bar(
                    x=list(pc.keys()), y=list(pc.values()),
                    marker_color=["#ff8fab","#ffd97d","#72efb0"],
                    text=list(pc.values()), textposition="outside"
                ))
                fig2.update_layout(title="Tasks by Priority",
                                   paper_bgcolor="rgba(0,0,0,0)",
                                   plot_bgcolor="rgba(0,0,0,0)",
                                   font=dict(color="#ede9ff"),
                                   margin=dict(t=50,b=40,l=40,r=20),
                                   xaxis=dict(color="#7b72a8"),
                                   yaxis=dict(color="#7b72a8"))
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("<h3>Project Completion</h3>", unsafe_allow_html=True)
            all_proj = [o["name"] for o in objectives] + ["Out of Scope"]
            for proj in all_proj:
                pt  = [t for t in tasks if t.get("project") == proj]
                dn  = len([t for t in pt if t.get("status") == "Done"])
                tot = len(pt)
                pct = int((dn / tot * 100) if tot else 0)
                ca, cb = st.columns([3,1])
                ca.markdown(f"**{proj}**")
                ca.progress(pct/100)
                cb.markdown(f"<div style='text-align:right;font-size:1.1rem;font-weight:700;color:#b79eff;'>{pct}%</div>", unsafe_allow_html=True)

        with tab2:
            df = pd.DataFrame(tasks)
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
                df = df.dropna(subset=["created_at"])
                df["week"]  = df["created_at"].dt.isocalendar().week.astype(int)
                df["month"] = df["created_at"].dt.month_name()
                period = st.radio("Group by", ["Week","Month"], horizontal=True)
                if period == "Week":
                    grp  = df.groupby("week").size().reset_index(name="count")
                    fig3 = px.bar(grp, x="week", y="count", title="Tasks Added per Week",
                                  color_discrete_sequence=["#b79eff"])
                else:
                    mo   = ["January","February","March","April","May","June",
                            "July","August","September","October","November","December"]
                    grp  = df.groupby("month").size().reset_index(name="count")
                    grp["month"] = pd.Categorical(grp["month"], categories=mo, ordered=True)
                    grp  = grp.sort_values("month")
                    fig3 = px.bar(grp, x="month", y="count", title="Tasks Added per Month",
                                  color_discrete_sequence=["#b79eff"])
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                   plot_bgcolor="rgba(0,0,0,0)",
                                   font=dict(color="#ede9ff"),
                                   xaxis=dict(color="#7b72a8"),
                                   yaxis=dict(color="#7b72a8"))
                st.plotly_chart(fig3, use_container_width=True)

        with tab3:
            df_e = pd.DataFrame(tasks)
            if not df_e.empty:
                csv = df_e.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "abdullah_tasks.csv", "text/csv")
                try:
                    buf = io.BytesIO()
                    df_e.to_excel(buf, index=False, engine="openpyxl")
                    st.download_button("Download Excel", buf.getvalue(),
                                       "abdullah_tasks.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.info(f"Excel export unavailable: {e}")

# ════════════════════════════════════════════════════════════════════════════
# CALENDAR
# ════════════════════════════════════════════════════════════════════════════
elif page == "📆 Calendar":
    st.markdown("<h1>Calendar</h1>", unsafe_allow_html=True)
    tasks = tasks_data["tasks"]
    now   = datetime.now()
    c1, c2 = st.columns(2)
    sel_month = c1.selectbox("Month", list(range(1,13)), index=now.month-1,
                              format_func=lambda m: calendar.month_name[m])
    sel_year  = c2.number_input("Year", 2024, 2030, now.year)

    cal = calendar.monthcalendar(sel_year, sel_month)
    days_with_tasks = {}
    for t in tasks:
        due = t.get("due_date","")
        if due:
            try:
                d = datetime.strptime(due, "%Y-%m-%d")
                if d.month == sel_month and d.year == sel_year:
                    days_with_tasks.setdefault(d.day, []).append(t)
            except: pass

    dn = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdr = "".join([f"<th style='padding:8px;color:#7b72a8;font-size:0.78rem;text-transform:uppercase;'>{d}</th>" for d in dn])
    rows = ""
    for week in cal:
        rows += "<tr>"
        for day in week:
            if day == 0:
                rows += "<td style='padding:4px;'></td>"
            else:
                tlist = days_with_tasks.get(day,[])
                dots  = ""
                for t in tlist[:3]:
                    pc = {"High":"#ff8fab","Medium":"#ffd97d","Low":"#72efb0"}.get(t.get("priority",""),"#b79eff")
                    dots += f"<div style='font-size:0.65rem;color:{pc};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:88px;'>• {t['title'][:16]}</div>"
                if len(tlist) > 3: dots += f"<div style='font-size:0.62rem;color:#7b72a8;'>+{len(tlist)-3} more</div>"
                is_today = (day==now.day and sel_month==now.month and sel_year==now.year)
                bg     = "#2a2540" if is_today else "#1a1726"
                border = "2px solid #b79eff" if is_today else "1px solid #2e2848"
                day_color = "color:#b79eff;" if is_today else "color:#ede9ff;"
                rows += f"""<td style='vertical-align:top;padding:4px;'>
                    <div style='background:{bg};border:{border};border-radius:10px;padding:8px;min-height:72px;min-width:88px;'>
                        <div style='font-weight:700;font-size:0.82rem;margin-bottom:4px;{day_color}'>{day}</div>
                        {dots}
                    </div></td>"""
        rows += "</tr>"

    st.markdown(f"""
    <div style='overflow-x:auto;'>
    <table style='width:100%;border-collapse:separate;border-spacing:3px;'>
        <thead><tr>{hdr}</tr></thead>
        <tbody>{rows}</tbody>
    </table>
    </div>
    <div style='color:#7b72a8;font-size:0.75rem;margin-top:14px;'>
        Red = High priority &nbsp;&nbsp; Yellow = Medium &nbsp;&nbsp; Green = Low
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# INBOX
# ════════════════════════════════════════════════════════════════════════════
elif "Inbox" in page:
    st.markdown("<h1>Abdullah's Inbox</h1>", unsafe_allow_html=True)
    requests = requests_data["requests"]
    pending  = [r for r in requests if r.get("status") == "pending"]
    archived = [r for r in requests if r.get("status") != "pending"]

    if not pending:
        st.success("All clear, Abdullah! No pending requests.")
    else:
        st.markdown(f"<div style='color:#ff8fab;margin-bottom:16px;font-weight:700;'>{len(pending)} pending request(s)</div>", unsafe_allow_html=True)

    for i, r in enumerate(sorted(pending, key=lambda x: x.get("submitted_at",""), reverse=True)):
        with st.expander(f"{r.get('task_title','Untitled')}  |  from {r.get('requester_name','Unknown')}", expanded=True):
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"**From:** {r.get('requester_name','—')} · {r.get('requester_email','—')}")
                st.markdown(f"**Project:** {r.get('project','—')}  |  **Priority:** {r.get('priority','—')}")
                if r.get("due_date"): st.markdown(f"**Requested by:** {r['due_date']}")
                st.markdown(f"**Details:** {r.get('description','—')}")
                st.markdown(f"<div style='color:#7b72a8;font-size:0.78rem;'>Submitted: {r.get('submitted_at','')[:16]}</div>", unsafe_allow_html=True)
            with col2:
                if st.button("Accept as Task", key=f"acc_{i}"):
                    tasks_data["tasks"].append({
                        "id": len(tasks_data["tasks"])+1,
                        "title": r.get("task_title",""),
                        "project": r.get("project","Out of Scope"),
                        "description": r.get("description",""),
                        "priority": r.get("priority","Medium"),
                        "status": "To Do",
                        "due_date": r.get("due_date",""),
                        "created_at": str(datetime.now()),
                        "source": f"Request from {r.get('requester_name','')}",
                    })
                    save_data("tasks", tasks_data)
                    idx = next((j for j,x in enumerate(requests_data["requests"]) if x.get("submitted_at")==r.get("submitted_at")), None)
                    if idx is not None:
                        requests_data["requests"][idx]["status"] = "accepted"
                        save_data("requests", requests_data)
                    st.success("Task added!")
                    st.rerun()
                if st.button("Dismiss", key=f"dis_{i}"):
                    idx = next((j for j,x in enumerate(requests_data["requests"]) if x.get("submitted_at")==r.get("submitted_at")), None)
                    if idx is not None:
                        requests_data["requests"][idx]["status"] = "dismissed"
                        save_data("requests", requests_data)
                    st.rerun()

    if archived:
        with st.expander(f"Archived ({len(archived)})"):
            for r in sorted(archived, key=lambda x: x.get("submitted_at",""), reverse=True):
                sc    = r.get("status","—")
                color = "#72efb0" if sc=="accepted" else "#ff8fab"
                st.markdown(f"""
                <div class='card' style='padding:10px 16px;'>
                    <strong style='color:#ede9ff;'>{r.get('task_title','—')}</strong>
                    &nbsp;<span style='color:{color};font-size:0.8rem;'>{sc}</span>
                    &nbsp;<span style='color:#7b72a8;font-size:0.78rem;'>from {r.get('requester_name','—')} · {r.get('submitted_at','')[:10]}</span>
                </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# REQUEST A TASK (public form)
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔗 Request a Task":
    st.markdown("<h1>Request a Task from Abdullah</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#7b72a8;margin-bottom:24px;'>Fill in the form — your request goes straight to Abdullah's inbox.</div>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])
    proj_names = [o["name"] for o in objectives] + ["Out of Scope", "New Project"]

    with st.form("request_task"):
        r1, r2 = st.columns(2)
        req_name  = r1.text_input("Your Name *")
        req_email = r2.text_input("Your Email *")
        task_title  = st.text_input("Task Title *", placeholder="What do you need Abdullah to do?")
        description = st.text_area("Details / Context", height=100)
        c1, c2, c3 = st.columns(3)
        project  = c1.selectbox("Related Project", proj_names)
        priority = c2.selectbox("Suggested Priority", ["Low","Medium","High"])
        due_date = c3.date_input("Desired Completion Date", value=None)
        if st.form_submit_button("Submit Request"):
            if req_name and req_email and task_title:
                requests_data["requests"].append({
                    "requester_name":  req_name,
                    "requester_email": req_email,
                    "task_title":      task_title,
                    "description":     description,
                    "project":         project,
                    "priority":        priority,
                    "due_date":        str(due_date) if due_date else "",
                    "status":          "pending",
                    "submitted_at":    str(datetime.now()),
                })
                save_data("requests", requests_data)
                st.success("Request submitted! Abdullah will review it shortly.")
                st.balloons()
            else:
                st.error("Please fill in your name, email and task title.")
