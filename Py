import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WorkOS – Year Organizer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
NOTES_DIR = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

OGSM_FILE      = DATA_DIR / "ogsm.json"
TASKS_FILE     = DATA_DIR / "tasks.json"
REQUESTS_FILE  = DATA_DIR / "requests.json"

# ── helpers ───────────────────────────────────────────────────────────────────
def load_json(path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def init_data():
    if not OGSM_FILE.exists():
        save_json(OGSM_FILE, {"objectives": []})
    if not TASKS_FILE.exists():
        save_json(TASKS_FILE, {"tasks": []})
    if not REQUESTS_FILE.exists():
        save_json(REQUESTS_FILE, {"requests": []})

init_data()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
    --bg: #0d0f14;
    --bg2: #14171f;
    --bg3: #1c2030;
    --accent: #6c8aff;
    --accent2: #ff6b6b;
    --accent3: #43e97b;
    --accent4: #f7c948;
    --text: #e8eaf0;
    --muted: #6b7280;
    --border: #252a38;
    --card-shadow: 0 4px 24px rgba(0,0,0,0.4);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

h1,h2,h3,h4 { font-family: 'Syne', sans-serif !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Metric cards */
.metric-card {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: var(--card-shadow);
}
.metric-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--accent);
    line-height: 1;
}
.metric-label {
    font-size: 0.78rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 6px;
}

/* Cards */
.card {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: var(--card-shadow);
}
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 6px;
}
.tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-right: 6px;
}
.tag-high   { background: rgba(255,107,107,0.18); color: #ff6b6b; }
.tag-medium { background: rgba(247,201,72,0.18);  color: #f7c948; }
.tag-low    { background: rgba(67,233,123,0.18);  color: #43e97b; }
.tag-todo   { background: rgba(108,138,255,0.18); color: #6c8aff; }
.tag-inprog { background: rgba(247,201,72,0.18);  color: #f7c948; }
.tag-done   { background: rgba(67,233,123,0.18);  color: #43e97b; }

/* Progress bar override */
.stProgress > div > div { background: var(--accent) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
}
.stMultiSelect > div { background: var(--bg2) !important; border-radius: 10px !important; }

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Tab styling */
.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
}
.stTabs [aria-selected="true"] { color: var(--accent) !important; }
.stTabs [data-baseweb="tab-border"] { background: var(--accent) !important; }

/* Badge */
.badge {
    background: var(--accent2);
    color: #fff;
    border-radius: 999px;
    padding: 1px 8px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-left: 6px;
}

/* Kanban column */
.kanban-col {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px;
    min-height: 200px;
}
.kanban-header {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Alert/info override */
.stAlert { border-radius: 12px !important; }

/* Expander */
.streamlit-expanderHeader {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    background: var(--bg3) !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── load data ─────────────────────────────────────────────────────────────────
ogsm_data     = load_json(OGSM_FILE,     {"objectives": []})
tasks_data    = load_json(TASKS_FILE,    {"tasks": []})
requests_data = load_json(REQUESTS_FILE, {"requests": []})

pending_requests = [r for r in requests_data["requests"] if r.get("status") == "pending"]
badge_count = len(pending_requests)

# ── sidebar nav ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:10px 0 24px 0'>
        <div style='font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;color:#6c8aff;'>WorkOS</div>
        <div style='font-size:0.75rem;color:#6b7280;margin-top:2px;'>Year Organizer</div>
    </div>
    """, unsafe_allow_html=True)

    inbox_label = f"📥 Inbox" + (f"  🔴 {badge_count}" if badge_count else "")

    page = st.radio("Navigate", [
        "🎯 Dashboard",
        "📋 OGSM Setup",
        "✅ Tasks",
        "🗂️ Kanban Board",
        "📅 Gantt Chart",
        "📓 Notes",
        "📊 Reports",
        "📆 Calendar",
        inbox_label,
        "🔗 Request a Task",
    ], label_visibility="collapsed")

    st.markdown("---")
    year = datetime.now().year
    st.markdown(f"<div style='font-size:0.75rem;color:#6b7280;'>📅 {year} · All data saved locally</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if page == "🎯 Dashboard":
    st.markdown("<h1 style='margin-bottom:4px;'>🎯 Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#6b7280;margin-bottom:28px;'>Welcome back · {datetime.now().strftime('%A, %d %B %Y')}</div>", unsafe_allow_html=True)

    tasks = tasks_data["tasks"]
    total_tasks  = len(tasks)
    done_tasks   = len([t for t in tasks if t.get("status") == "Done"])
    inprog_tasks = len([t for t in tasks if t.get("status") == "In Progress"])
    todo_tasks   = len([t for t in tasks if t.get("status") == "To Do"])
    overdue      = len([t for t in tasks if t.get("due_date") and t.get("status") != "Done"
                        and datetime.strptime(t["due_date"], "%Y-%m-%d").date() < datetime.now().date()])

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, num, label, color in [
        (c1, total_tasks,  "Total Tasks",   "#6c8aff"),
        (c2, done_tasks,   "Completed",     "#43e97b"),
        (c3, inprog_tasks, "In Progress",   "#f7c948"),
        (c4, todo_tasks,   "To Do",         "#6c8aff"),
        (c5, overdue,      "Overdue",       "#ff6b6b"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-num" style="color:{color};">{num}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Project progress
    st.markdown("<h3>Project Progress</h3>", unsafe_allow_html=True)
    objectives = ogsm_data.get("objectives", [])
    if not objectives:
        st.info("No OGSM projects yet — go to **📋 OGSM Setup** to add them.")
    else:
        cols = st.columns(min(len(objectives), 3))
        for i, obj in enumerate(objectives):
            obj_tasks = [t for t in tasks if t.get("project") == obj["name"]]
            done_n    = len([t for t in obj_tasks if t.get("status") == "Done"])
            total_n   = len(obj_tasks)
            pct       = int((done_n / total_n * 100) if total_n else 0)
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">{obj['name']}</div>
                    <div style='color:#6b7280;font-size:0.8rem;margin-bottom:10px;'>{obj.get('objective','')[:70]}</div>
                    <div style='font-size:0.85rem;margin-bottom:6px;'>{done_n} / {total_n} tasks done &nbsp; <strong>{pct}%</strong></div>
                </div>""", unsafe_allow_html=True)
                st.progress(pct / 100)

    st.markdown("---")

    # Recent tasks
    st.markdown("<h3>Recent Tasks</h3>", unsafe_allow_html=True)
    recent = sorted(tasks, key=lambda x: x.get("created_at",""), reverse=True)[:5]
    if not recent:
        st.info("No tasks yet — go to **✅ Tasks** to add some.")
    for t in recent:
        priority = t.get("priority","Medium")
        status   = t.get("status","To Do")
        p_cls    = f"tag-{priority.lower()}"
        s_cls    = "tag-done" if status=="Done" else ("tag-inprog" if status=="In Progress" else "tag-todo")
        st.markdown(f"""
        <div class="card" style="padding:12px 18px;">
            <span class="card-title">{t['title']}</span>
            &nbsp;&nbsp;
            <span class="tag {p_cls}">{priority}</span>
            <span class="tag {s_cls}">{status}</span>
            <span style='color:#6b7280;font-size:0.78rem;margin-left:10px;'>📁 {t.get('project','—')}</span>
            {f"<span style='color:#ff6b6b;font-size:0.78rem;margin-left:10px;'>📅 {t.get('due_date','')}</span>" if t.get('due_date') else ''}
        </div>""", unsafe_allow_html=True)

    if badge_count:
        st.markdown("---")
        st.warning(f"📥 You have **{badge_count}** pending task request(s) in your inbox.")

# ════════════════════════════════════════════════════════════════════════════
# PAGE: OGSM SETUP
# ════════════════════════════════════════════════════════════════════════════
elif page == "📋 OGSM Setup":
    st.markdown("<h1>📋 OGSM Setup</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6b7280;margin-bottom:24px;'>Define your Objectives, Goals, Strategies & Measures for the year.</div>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])

    with st.expander("➕ Add New Project / Objective", expanded=not objectives):
        with st.form("add_obj"):
            n1, n2 = st.columns(2)
            name      = n1.text_input("Project Name *", placeholder="e.g. Udemy Learning")
            objective = n2.text_input("Objective *",    placeholder="What do you want to achieve?")
            goal      = st.text_input("Goal",           placeholder="Measurable outcome")
            strategy  = st.text_area("Strategy",        placeholder="How will you get there?", height=80)
            measure   = st.text_input("KPI / Measure",  placeholder="e.g. Complete 3 courses by Q3")
            target    = st.number_input("KPI Target (%)", 0, 100, 100)
            color     = st.color_picker("Project Color", "#6c8aff")
            if st.form_submit_button("Save Project"):
                if name and objective:
                    objectives.append({
                        "id":        len(objectives)+1,
                        "name":      name,
                        "objective": objective,
                        "goal":      goal,
                        "strategy":  strategy,
                        "measure":   measure,
                        "target":    target,
                        "color":     color,
                        "created_at": str(datetime.now().date()),
                    })
                    ogsm_data["objectives"] = objectives
                    save_json(OGSM_FILE, ogsm_data)
                    st.success(f"✅ Project '{name}' saved!")
                    st.rerun()
                else:
                    st.error("Name and Objective are required.")

    if objectives:
        st.markdown("### Your OGSM Projects")
        for i, obj in enumerate(objectives):
            with st.expander(f"🎯 {obj['name']}", expanded=False):
                e1, e2 = st.columns([3,1])
                with e1:
                    st.markdown(f"""
                    <div class='card'>
                        <div style='font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;'>Objective</div>
                        <div style='margin-bottom:12px;'>{obj.get('objective','—')}</div>
                        <div style='font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;'>Goal</div>
                        <div style='margin-bottom:12px;'>{obj.get('goal','—')}</div>
                        <div style='font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;'>Strategy</div>
                        <div style='margin-bottom:12px;'>{obj.get('strategy','—')}</div>
                        <div style='font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;'>KPI / Measure</div>
                        <div>{obj.get('measure','—')}</div>
                    </div>""", unsafe_allow_html=True)
                with e2:
                    tasks = tasks_data["tasks"]
                    obj_tasks = [t for t in tasks if t.get("project") == obj["name"]]
                    done_n = len([t for t in obj_tasks if t.get("status") == "Done"])
                    total_n = len(obj_tasks)
                    pct = int((done_n / total_n * 100) if total_n else 0)
                    st.markdown(f"""
                    <div class='metric-card' style='text-align:center;'>
                        <div class='metric-num' style='color:{obj.get("color","#6c8aff")};'>{pct}%</div>
                        <div class='metric-label'>KPI Progress</div>
                        <div style='margin-top:8px;font-size:0.8rem;color:#6b7280;'>{done_n}/{total_n} tasks</div>
                    </div>""", unsafe_allow_html=True)

                if st.button(f"🗑️ Delete '{obj['name']}'", key=f"del_{i}"):
                    objectives.pop(i)
                    ogsm_data["objectives"] = objectives
                    save_json(OGSM_FILE, ogsm_data)
                    st.rerun()
    else:
        st.info("No projects yet. Add your first OGSM project above!")

# ════════════════════════════════════════════════════════════════════════════
# PAGE: TASKS
# ════════════════════════════════════════════════════════════════════════════
elif page == "✅ Tasks":
    st.markdown("<h1>✅ Tasks</h1>", unsafe_allow_html=True)

    objectives  = ogsm_data.get("objectives", [])
    proj_names  = [o["name"] for o in objectives] + ["Out of Scope"]
    tasks       = tasks_data["tasks"]

    tab1, tab2 = st.tabs(["➕ Add Task", "📋 All Tasks"])

    with tab1:
        with st.form("add_task"):
            t1, t2 = st.columns(2)
            title    = t1.text_input("Task Title *")
            project  = t2.selectbox("Project", proj_names if proj_names else ["Out of Scope"])
            desc     = st.text_area("Description / Reflection", height=80)
            c1, c2, c3 = st.columns(3)
            priority = c1.selectbox("Priority", ["High","Medium","Low"])
            status   = c2.selectbox("Status", ["To Do","In Progress","Done"])
            due_date = c3.date_input("Due Date", value=None)
            if st.form_submit_button("Save Task"):
                if title:
                    tasks.append({
                        "id":         len(tasks)+1,
                        "title":      title,
                        "project":    project,
                        "description":desc,
                        "priority":   priority,
                        "status":     status,
                        "due_date":   str(due_date) if due_date else "",
                        "created_at": str(datetime.now()),
                    })
                    tasks_data["tasks"] = tasks
                    save_json(TASKS_FILE, tasks_data)
                    st.success("✅ Task saved!")
                    st.rerun()
                else:
                    st.error("Task title is required.")

    with tab2:
        # Filters
        f1, f2, f3, f4 = st.columns(4)
        f_proj   = f1.selectbox("Filter by Project", ["All"] + proj_names, key="fp")
        f_status = f2.selectbox("Filter by Status",  ["All","To Do","In Progress","Done"], key="fs")
        f_prio   = f3.selectbox("Filter by Priority",["All","High","Medium","Low"], key="fpr")
        f_search = f4.text_input("Search", placeholder="keyword…", key="fsrch")

        filtered = tasks
        if f_proj   != "All": filtered = [t for t in filtered if t.get("project") == f_proj]
        if f_status != "All": filtered = [t for t in filtered if t.get("status")  == f_status]
        if f_prio   != "All": filtered = [t for t in filtered if t.get("priority")== f_prio]
        if f_search:          filtered = [t for t in filtered if f_search.lower() in t.get("title","").lower()]

        st.markdown(f"<div style='color:#6b7280;margin:10px 0;font-size:0.85rem;'>{len(filtered)} task(s) found</div>", unsafe_allow_html=True)

        for i, t in enumerate(sorted(filtered, key=lambda x: x.get("created_at",""), reverse=True)):
            priority = t.get("priority","Medium")
            status   = t.get("status","To Do")
            p_cls    = f"tag-{priority.lower()}"
            s_cls    = "tag-done" if status=="Done" else ("tag-inprog" if status=="In Progress" else "tag-todo")
            due      = t.get("due_date","")
            overdue  = due and status != "Done" and datetime.strptime(due, "%Y-%m-%d").date() < datetime.now().date()

            with st.expander(f"{'🔴 ' if overdue else ''}  {t['title']}  ·  {t.get('project','—')}", expanded=False):
                cols = st.columns([2,1])
                with cols[0]:
                    st.markdown(f"""
                    <span class="tag {p_cls}">{priority}</span>
                    <span class="tag {s_cls}">{status}</span>
                    {"<span style='color:#ff6b6b;font-size:0.8rem;margin-left:8px;'>⚠️ Overdue</span>" if overdue else ""}
                    <div style='margin-top:12px;color:#ccc;'>{t.get('description','') or '<em style="color:#6b7280">No description</em>'}</div>
                    """, unsafe_allow_html=True)
                    if due:
                        st.markdown(f"📅 Due: **{due}**")
                    st.markdown(f"🕐 Added: {t.get('created_at','')[:10]}")
                with cols[1]:
                    # Inline status update
                    new_status = st.selectbox("Change Status", ["To Do","In Progress","Done"],
                                              index=["To Do","In Progress","Done"].index(status),
                                              key=f"st_{t['id']}")
                    if new_status != status:
                        idx = next((j for j,x in enumerate(tasks_data["tasks"]) if x.get("id")==t["id"]), None)
                        if idx is not None:
                            tasks_data["tasks"][idx]["status"] = new_status
                            save_json(TASKS_FILE, tasks_data)
                            st.rerun()
                    if st.button("🗑️ Delete", key=f"del_t_{t['id']}"):
                        tasks_data["tasks"] = [x for x in tasks_data["tasks"] if x.get("id")!=t["id"]]
                        save_json(TASKS_FILE, tasks_data)
                        st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PAGE: KANBAN BOARD
# ════════════════════════════════════════════════════════════════════════════
elif page == "🗂️ Kanban Board":
    st.markdown("<h1>🗂️ Kanban Board</h1>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])
    proj_names = [o["name"] for o in objectives] + ["Out of Scope"]
    tasks = tasks_data["tasks"]

    # Project filter
    sel_proj = st.selectbox("Filter by Project", ["All"] + proj_names)
    filtered = tasks if sel_proj == "All" else [t for t in tasks if t.get("project") == sel_proj]

    todo    = [t for t in filtered if t.get("status") == "To Do"]
    inprog  = [t for t in filtered if t.get("status") == "In Progress"]
    done    = [t for t in filtered if t.get("status") == "Done"]

    col1, col2, col3 = st.columns(3)

    def render_kanban_col(container, title, tasks_list, color, status_key):
        with container:
            st.markdown(f"""
            <div class="kanban-col">
                <div class="kanban-header" style="color:{color};">{title} · {len(tasks_list)}</div>
            """, unsafe_allow_html=True)
            for t in tasks_list:
                p = t.get("priority","Medium")
                p_cls = f"tag-{p.lower()}"
                due = t.get("due_date","")
                st.markdown(f"""
                <div class="card" style="margin-bottom:10px;padding:12px 14px;">
                    <div style="font-weight:600;font-size:0.88rem;margin-bottom:6px;">{t['title']}</div>
                    <span class="tag {p_cls}">{p}</span>
                    <div style='font-size:0.75rem;color:#6b7280;margin-top:6px;'>📁 {t.get('project','—')}</div>
                    {f"<div style='font-size:0.75rem;color:#6b7280;'>📅 {due}</div>" if due else ""}
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    render_kanban_col(col1, "📋 To Do",      todo,   "#6c8aff", "To Do")
    render_kanban_col(col2, "⚡ In Progress", inprog, "#f7c948", "In Progress")
    render_kanban_col(col3, "✅ Done",        done,   "#43e97b", "Done")

# ════════════════════════════════════════════════════════════════════════════
# PAGE: GANTT CHART
# ════════════════════════════════════════════════════════════════════════════
elif page == "📅 Gantt Chart":
    import pandas as pd
    import plotly.figure_factory as ff
    import plotly.graph_objects as go

    st.markdown("<h1>📅 Gantt Chart</h1>", unsafe_allow_html=True)

    tasks = tasks_data["tasks"]
    gantt_tasks = [t for t in tasks if t.get("due_date") and t.get("created_at")]

    if not gantt_tasks:
        st.info("Add tasks with due dates to see the Gantt chart.")
    else:
        df = []
        for t in gantt_tasks:
            try:
                start = t["created_at"][:10]
                end   = t["due_date"]
                if start <= end:
                    df.append(dict(
                        Task=t["title"][:35],
                        Start=start,
                        Finish=end,
                        Resource=t.get("project","Unknown"),
                        Status=t.get("status","To Do"),
                    ))
            except:
                pass

        if df:
            projects = list(set(d["Resource"] for d in df))
            colors   = {}
            palette  = ["#6c8aff","#ff6b6b","#43e97b","#f7c948","#a78bfa","#fb923c","#22d3ee"]
            for i, p in enumerate(projects):
                colors[p] = palette[i % len(palette)]

            fig = ff.create_gantt(df, colors=colors, index_col="Resource",
                                  show_colorbar=True, group_tasks=True,
                                  showgrid_x=True, showgrid_y=True)
            fig.update_layout(
                paper_bgcolor="#0d0f14",
                plot_bgcolor="#14171f",
                font=dict(color="#e8eaf0", family="DM Sans"),
                height=500,
                margin=dict(l=180, r=20, t=40, b=60),
            )
            fig.update_xaxes(color="#6b7280")
            fig.update_yaxes(color="#e8eaf0")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No tasks with valid start/end date pairs found.")

# ════════════════════════════════════════════════════════════════════════════
# PAGE: NOTES
# ════════════════════════════════════════════════════════════════════════════
elif page == "📓 Notes":
    st.markdown("<h1>📓 Notes</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6b7280;margin-bottom:24px;'>Notes are saved per project folder.</div>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])
    proj_names = [o["name"] for o in objectives] + ["Out of Scope"]

    tab1, tab2 = st.tabs(["✏️ Write Note", "📂 Browse Notes"])

    with tab1:
        with st.form("add_note"):
            n1, n2 = st.columns(2)
            proj  = n1.selectbox("Project Folder", proj_names)
            title = n2.text_input("Note Title *", placeholder="Quick summary")
            content = st.text_area("Note Content", height=200)
            tags    = st.text_input("Tags (comma separated)", placeholder="e.g. meeting, q2")
            if st.form_submit_button("💾 Save Note"):
                if title and content:
                    folder = NOTES_DIR / proj.replace(" ","_").replace("/","_")
                    folder.mkdir(exist_ok=True)
                    note = {
                        "title":      title,
                        "project":    proj,
                        "content":    content,
                        "tags":       [t.strip() for t in tags.split(",") if t.strip()],
                        "created_at": str(datetime.now()),
                    }
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title[:20].replace(' ','_')}.json"
                    with open(folder / fname, "w") as f:
                        json.dump(note, f, indent=2)
                    st.success(f"✅ Note saved to '{proj}' folder!")
                    st.rerun()
                else:
                    st.error("Title and content are required.")

    with tab2:
        sel_proj = st.selectbox("Select Project Folder", ["All"] + proj_names, key="note_proj")

        all_notes = []
        for folder in NOTES_DIR.iterdir():
            if folder.is_dir():
                for f in folder.glob("*.json"):
                    try:
                        n = json.load(open(f))
                        n["_file"] = str(f)
                        all_notes.append(n)
                    except:
                        pass

        if sel_proj != "All":
            all_notes = [n for n in all_notes if n.get("project") == sel_proj]

        all_notes.sort(key=lambda x: x.get("created_at",""), reverse=True)
        search = st.text_input("🔍 Search notes", placeholder="keyword…")
        if search:
            all_notes = [n for n in all_notes if search.lower() in n.get("title","").lower()
                         or search.lower() in n.get("content","").lower()]

        st.markdown(f"<div style='color:#6b7280;font-size:0.85rem;margin:8px 0;'>{len(all_notes)} note(s)</div>", unsafe_allow_html=True)

        for note in all_notes:
            with st.expander(f"📝 {note['title']}  ·  {note.get('project','—')}  ·  {note.get('created_at','')[:10]}"):
                st.markdown(note["content"])
                if note.get("tags"):
                    tags_html = " ".join([f"<span class='tag tag-todo'>{t}</span>" for t in note["tags"]])
                    st.markdown(tags_html, unsafe_allow_html=True)
                if st.button("🗑️ Delete Note", key=f"del_note_{note['_file']}"):
                    os.remove(note["_file"])
                    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ════════════════════════════════════════════════════════════════════════════
elif page == "📊 Reports":
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px

    st.markdown("<h1>📊 Reports</h1>", unsafe_allow_html=True)

    tasks = tasks_data["tasks"]
    objectives = ogsm_data.get("objectives", [])

    if not tasks:
        st.info("No tasks yet. Add tasks to generate reports.")
    else:
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "📅 Weekly/Monthly", "📤 Export"])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                # Status donut
                statuses = [t.get("status","To Do") for t in tasks]
                status_counts = {s: statuses.count(s) for s in ["To Do","In Progress","Done"]}
                fig = go.Figure(data=[go.Pie(
                    labels=list(status_counts.keys()),
                    values=list(status_counts.values()),
                    hole=0.55,
                    marker_colors=["#6c8aff","#f7c948","#43e97b"],
                )])
                fig.update_layout(
                    title="Tasks by Status",
                    paper_bgcolor="#0d0f14", plot_bgcolor="#0d0f14",
                    font=dict(color="#e8eaf0"), margin=dict(t=50,b=20,l=20,r=20),
                    showlegend=True,
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Priority bar
                priorities = [t.get("priority","Medium") for t in tasks]
                pri_counts = {p: priorities.count(p) for p in ["High","Medium","Low"]}
                fig2 = go.Figure(data=[go.Bar(
                    x=list(pri_counts.keys()),
                    y=list(pri_counts.values()),
                    marker_color=["#ff6b6b","#f7c948","#43e97b"],
                    text=list(pri_counts.values()),
                    textposition="outside",
                )])
                fig2.update_layout(
                    title="Tasks by Priority",
                    paper_bgcolor="#0d0f14", plot_bgcolor="#14171f",
                    font=dict(color="#e8eaf0"), margin=dict(t=50,b=40,l=40,r=20),
                    xaxis=dict(color="#6b7280"), yaxis=dict(color="#6b7280"),
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Project progress horizontal bars
            st.markdown("<h3>Project Completion</h3>", unsafe_allow_html=True)
            for obj in objectives:
                obj_tasks = [t for t in tasks if t.get("project") == obj["name"]]
                done_n = len([t for t in obj_tasks if t.get("status") == "Done"])
                total_n = len(obj_tasks)
                pct = int((done_n / total_n * 100) if total_n else 0)
                col_a, col_b = st.columns([3,1])
                col_a.markdown(f"**{obj['name']}**")
                col_a.progress(pct/100)
                col_b.markdown(f"<div style='text-align:right;font-size:1.1rem;font-weight:700;color:{obj.get('color','#6c8aff')};'>{pct}%</div>", unsafe_allow_html=True)

        with tab2:
            df = pd.DataFrame(tasks)
            if "created_at" in df.columns:
                df["date"] = pd.to_datetime(df["created_at"]).dt.date
                df["week"] = pd.to_datetime(df["created_at"]).dt.isocalendar().week
                df["month"] = pd.to_datetime(df["created_at"]).dt.month_name()

                period = st.radio("Group by", ["Week","Month"], horizontal=True)

                if period == "Week":
                    grp = df.groupby("week").size().reset_index(name="tasks_added")
                    fig3 = px.bar(grp, x="week", y="tasks_added", title="Tasks Added per Week",
                                  color_discrete_sequence=["#6c8aff"])
                else:
                    month_order = ["January","February","March","April","May","June",
                                   "July","August","September","October","November","December"]
                    grp = df.groupby("month").size().reset_index(name="tasks_added")
                    grp["month"] = pd.Categorical(grp["month"], categories=month_order, ordered=True)
                    grp = grp.sort_values("month")
                    fig3 = px.bar(grp, x="month", y="tasks_added", title="Tasks Added per Month",
                                  color_discrete_sequence=["#6c8aff"])

                fig3.update_layout(
                    paper_bgcolor="#0d0f14", plot_bgcolor="#14171f",
                    font=dict(color="#e8eaf0"), xaxis=dict(color="#6b7280"), yaxis=dict(color="#6b7280"),
                )
                st.plotly_chart(fig3, use_container_width=True)

        with tab3:
            import io
            df_export = pd.DataFrame(tasks)
            if not df_export.empty:
                # CSV
                csv = df_export.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download CSV", csv, "tasks_export.csv", "text/csv")

                # Excel
                try:
                    buf = io.BytesIO()
                    df_export.to_excel(buf, index=False, engine="openpyxl")
                    st.download_button("📥 Download Excel", buf.getvalue(),
                                       "tasks_export.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except:
                    st.info("Install openpyxl for Excel export: `pip install openpyxl`")

# ════════════════════════════════════════════════════════════════════════════
# PAGE: CALENDAR
# ════════════════════════════════════════════════════════════════════════════
elif page == "📆 Calendar":
    import pandas as pd
    import plotly.graph_objects as go
    import calendar

    st.markdown("<h1>📆 Calendar View</h1>", unsafe_allow_html=True)

    tasks = tasks_data["tasks"]
    now   = datetime.now()

    sel_month = st.selectbox("Month", list(range(1,13)),
                              index=now.month-1,
                              format_func=lambda m: calendar.month_name[m])
    sel_year  = st.number_input("Year", 2024, 2030, now.year)

    # Build calendar grid
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

    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    header_html = "".join([f"<th style='padding:8px;color:#6b7280;font-size:0.8rem;text-transform:uppercase;'>{d}</th>" for d in day_names])

    rows_html = ""
    for week in cal:
        rows_html += "<tr>"
        for day in week:
            if day == 0:
                rows_html += "<td style='padding:6px;'></td>"
            else:
                task_list = days_with_tasks.get(day, [])
                task_dots = ""
                for t in task_list[:3]:
                    prio_color = {"High":"#ff6b6b","Medium":"#f7c948","Low":"#43e97b"}.get(t.get("priority","Medium"),"#6c8aff")
                    task_dots += f"<div style='font-size:0.68rem;color:{prio_color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:90px;'>• {t['title'][:18]}</div>"
                if len(task_list) > 3:
                    task_dots += f"<div style='font-size:0.65rem;color:#6b7280;'>+{len(task_list)-3} more</div>"
                is_today = (day == now.day and sel_month == now.month and sel_year == now.year)
                bg = "#1c2030" if not is_today else "#252a48"
                border = "2px solid #6c8aff" if is_today else "1px solid #252a38"
                rows_html += f"""
                <td style='vertical-align:top;padding:6px;'>
                    <div style='background:{bg};border:{border};border-radius:10px;padding:8px;min-height:70px;min-width:90px;'>
                        <div style='font-weight:700;font-size:0.85rem;margin-bottom:4px;{"color:#6c8aff;" if is_today else ""}'>{day}</div>
                        {task_dots}
                    </div>
                </td>"""
        rows_html += "</tr>"

    st.markdown(f"""
    <div style='overflow-x:auto;'>
    <table style='width:100%;border-collapse:separate;border-spacing:4px;'>
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"<div style='color:#6b7280;font-size:0.8rem;'>🟥 High &nbsp;&nbsp; 🟨 Medium &nbsp;&nbsp; 🟩 Low priority</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: INBOX
# ════════════════════════════════════════════════════════════════════════════
elif "Inbox" in page:
    st.markdown("<h1>📥 Inbox</h1>", unsafe_allow_html=True)

    requests = requests_data["requests"]
    pending  = [r for r in requests if r.get("status") == "pending"]
    archived = [r for r in requests if r.get("status") != "pending"]

    if not pending:
        st.success("✅ All clear! No pending requests.")
    else:
        st.markdown(f"<div style='color:#ff6b6b;margin-bottom:16px;font-weight:600;'>{len(pending)} pending request(s)</div>", unsafe_allow_html=True)

    for i, r in enumerate(sorted(pending, key=lambda x: x.get("submitted_at",""), reverse=True)):
        with st.expander(f"📌 {r.get('task_title','Untitled')}  ·  from {r.get('requester_name','Unknown')}", expanded=True):
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"**From:** {r.get('requester_name','—')} · {r.get('requester_email','—')}")
                st.markdown(f"**Project:** {r.get('project','—')}")
                st.markdown(f"**Priority:** {r.get('priority','—')}")
                if r.get("due_date"): st.markdown(f"**Requested by:** {r['due_date']}")
                st.markdown(f"**Details:** {r.get('description','—')}")
                st.markdown(f"<div style='color:#6b7280;font-size:0.78rem;'>Submitted: {r.get('submitted_at','')[:16]}</div>", unsafe_allow_html=True)
            with col2:
                if st.button("✅ Accept → Add Task", key=f"acc_{i}"):
                    # Add to tasks
                    tasks_data["tasks"].append({
                        "id":         len(tasks_data["tasks"])+1,
                        "title":      r.get("task_title",""),
                        "project":    r.get("project","Out of Scope"),
                        "description":r.get("description",""),
                        "priority":   r.get("priority","Medium"),
                        "status":     "To Do",
                        "due_date":   r.get("due_date",""),
                        "created_at": str(datetime.now()),
                        "source":     f"Request from {r.get('requester_name','')}",
                    })
                    save_json(TASKS_FILE, tasks_data)
                    # Archive request
                    idx = next((j for j,x in enumerate(requests_data["requests"]) if x.get("submitted_at")==r.get("submitted_at")), None)
                    if idx is not None:
                        requests_data["requests"][idx]["status"] = "accepted"
                        save_json(REQUESTS_FILE, requests_data)
                    st.success("Task added!")
                    st.rerun()
                if st.button("🗑️ Dismiss", key=f"dis_{i}"):
                    idx = next((j for j,x in enumerate(requests_data["requests"]) if x.get("submitted_at")==r.get("submitted_at")), None)
                    if idx is not None:
                        requests_data["requests"][idx]["status"] = "dismissed"
                        save_json(REQUESTS_FILE, requests_data)
                    st.rerun()

    if archived:
        with st.expander(f"📂 Archived Requests ({len(archived)})"):
            for r in sorted(archived, key=lambda x: x.get("submitted_at",""), reverse=True):
                status = r.get("status","—")
                color  = "#43e97b" if status=="accepted" else "#ff6b6b"
                st.markdown(f"""
                <div class='card' style='padding:10px 16px;'>
                    <strong>{r.get('task_title','—')}</strong>
                    &nbsp; <span style='color:{color};font-size:0.8rem;'>{status}</span>
                    &nbsp; <span style='color:#6b7280;font-size:0.78rem;'>from {r.get('requester_name','—')} · {r.get('submitted_at','')[:10]}</span>
                </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: REQUEST A TASK (public-facing)
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔗 Request a Task":
    st.markdown("<h1>🔗 Request a Task</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6b7280;margin-bottom:24px;'>Fill in the form below to submit a task request. It will appear in the owner's inbox.</div>", unsafe_allow_html=True)

    objectives = ogsm_data.get("objectives", [])
    proj_names = [o["name"] for o in objectives] + ["Out of Scope", "New Project"]

    with st.form("request_task"):
        r1, r2 = st.columns(2)
        requester_name  = r1.text_input("Your Name *")
        requester_email = r2.text_input("Your Email *")
        task_title      = st.text_input("Task Title *", placeholder="What do you need done?")
        description     = st.text_area("Details / Context", height=100)
        c1, c2, c3 = st.columns(3)
        project  = c1.selectbox("Related Project", proj_names)
        priority = c2.selectbox("Suggested Priority", ["Low","Medium","High"])
        due_date = c3.date_input("Desired Completion Date", value=None)

        submitted = st.form_submit_button("📤 Submit Request")
        if submitted:
            if requester_name and requester_email and task_title:
                requests_data["requests"].append({
                    "requester_name":  requester_name,
                    "requester_email": requester_email,
                    "task_title":      task_title,
                    "description":     description,
                    "project":         project,
                    "priority":        priority,
                    "due_date":        str(due_date) if due_date else "",
                    "status":          "pending",
                    "submitted_at":    str(datetime.now()),
                })
                save_json(REQUESTS_FILE, requests_data)
                st.success("✅ Your request has been submitted! The team will review it shortly.")
                st.balloons()
            else:
                st.error("Please fill in your name, email, and task title.")
