import streamlit as st
import pandas as pd
import io
import json
from pathlib import Path

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="مراجع التشريعات",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800;900&family=Amiri:wght@400;700&display=swap');

:root {
    --bg:        #0f1117;
    --bg2:       #161b27;
    --bg3:       #1e2536;
    --card:      #1a2035;
    --border:    #2a3352;
    --accent:    #4f8ef7;
    --accent2:   #7c5cbf;
    --gold:      #f5c842;
    --green:     #2ecc8a;
    --red:       #e05c6a;
    --orange:    #f7944f;
    --text:      #e8ecf4;
    --text2:     #8a95b0;
    --text3:     #5a6480;
    --radius:    14px;
    --shadow:    0 4px 24px rgba(0,0,0,0.35);
}

html, body, [class*="css"] {
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Hide streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem 2rem !important; max-width: 1400px !important; }

/* ── Hero Header ── */
.hero {
    background: linear-gradient(135deg, #1a2a5e 0%, #0f1117 50%, #1a1535 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 30% 50%, rgba(79,142,247,0.12) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 50%, rgba(124,92,191,0.10) 0%, transparent 60%);
    pointer-events: none;
}
.hero-icon { font-size: 3.5rem; margin-bottom: 0.5rem; }
.hero h1 {
    font-family: 'Amiri', serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #fff;
    margin: 0 0 0.4rem 0;
    text-shadow: 0 2px 20px rgba(79,142,247,0.4);
}
.hero p { color: var(--text2); font-size: 1.05rem; margin: 0; }

/* ── Upload Zone ── */
.upload-hint {
    background: var(--bg2);
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    color: var(--text2);
    transition: all 0.3s;
}

/* ── Stats Bar ── */
.stats-bar {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.stat-card {
    flex: 1;
    min-width: 140px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    text-align: center;
}
.stat-num { font-size: 2rem; font-weight: 800; }
.stat-lbl { font-size: 0.8rem; color: var(--text2); margin-top: 2px; }

/* ── Law Card ── */
.law-card {
    background: linear-gradient(135deg, #1e2a4a 0%, #1a2035 100%);
    border: 1px solid #2e4080;
    border-right: 4px solid var(--accent);
    border-radius: var(--radius);
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem;
}
.law-name {
    font-family: 'Amiri', serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #c8d8ff;
    line-height: 1.6;
}
.law-meta { font-size: 0.82rem; color: var(--text3); margin-top: 4px; }

/* ── Audit Row ── */
.audit-row {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: all 0.2s;
}
.audit-row:hover { border-color: var(--accent); }

/* ── Status Badge ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.badge-new    { background: rgba(138,149,176,0.15); color: #8a95b0; border: 1px solid #3a4460; }
.badge-ok     { background: rgba(46,204,138,0.15);  color: var(--green); border: 1px solid rgba(46,204,138,0.3); }
.badge-edited { background: rgba(247,148,79,0.15);  color: var(--orange); border: 1px solid rgba(247,148,79,0.3); }

/* ── Progress ── */
.progress-wrap {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem;
}
.progress-bar-outer {
    background: var(--bg3);
    border-radius: 99px;
    height: 10px;
    overflow: hidden;
    margin-top: 8px;
}
.progress-bar-inner {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transition: width 0.5s ease;
}

/* ── Nav Buttons ── */
.stButton > button {
    font-family: 'Tajawal', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.5rem !important;
    font-size: 0.95rem !important;
    border: none !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    font-family: 'Tajawal', sans-serif !important;
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    direction: rtl !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(79,142,247,0.2) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    direction: rtl !important;
}

/* ── Labels ── */
.stTextInput label, .stTextArea label, .stSelectbox label {
    color: var(--text2) !important;
    font-family: 'Tajawal', sans-serif !important;
    font-size: 0.85rem !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── Completed Banner ── */
.done-banner {
    background: linear-gradient(135deg, rgba(46,204,138,0.15), rgba(79,142,247,0.1));
    border: 1px solid rgba(46,204,138,0.35);
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    margin: 1rem 0;
}
.done-banner h2 { color: var(--green); font-family: 'Amiri', serif; font-size: 2rem; margin: 0 0 0.5rem 0; }
.done-banner p  { color: var(--text2); margin: 0; }

/* ── Row number chip ── */
.row-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px; height: 26px;
    border-radius: 50%;
    background: var(--bg);
    border: 1px solid var(--border);
    font-size: 0.75rem;
    color: var(--text3);
    margin-left: 8px;
}

/* Checkbox styling */
.stCheckbox > label {
    font-family: 'Tajawal', sans-serif !important;
    color: var(--text) !important;
}

/* Info / warning boxes */
.stAlert {
    border-radius: var(--radius) !important;
    font-family: 'Tajawal', sans-serif !important;
}

/* Metric */
[data-testid="stMetric"] { background: var(--card); border-radius: var(--radius); padding: 1rem; border: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ───────────────────────────────────────────────────────────────────
def load_file(uploaded_file):
    ext = Path(uploaded_file.name).suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    else:
        df = pd.read_excel(uploaded_file)
    return df, ext


def init_audit_state(df):
    """Build audit records grouped by leg_name."""
    records = []
    for idx, row in df.iterrows():
        records.append({
            "orig_idx":      idx,
            "leg_name":      str(row.get("leg_name", "")),
            "entity_final":  str(row.get("entity_final", "")),
            "type":          str(row.get("type", "")),
            "entity_audited": str(row.get("entity_final", "")),
            "type_audited":   str(row.get("type", "")),
            "audit_status":  "لم يُراجع",   # لم يُراجع / معتمد / معدّل
            "audit_notes":   "",
        })
    # Group by leg_name preserving order
    seen = {}
    groups = []
    for r in records:
        name = r["leg_name"]
        if name not in seen:
            seen[name] = len(groups)
            groups.append({"leg_name": name, "rows": []})
        groups[seen[name]]["rows"].append(r)
    return groups


def export_df(original_df, groups, ext):
    """Merge audit data back into original dataframe."""
    df_out = original_df.copy()
    df_out["entity_audited"] = df_out["entity_final"].astype(str)
    df_out["type_audited"]   = df_out["type"].astype(str)
    df_out["audit_status"]   = "لم يُراجع"
    df_out["audit_notes"]    = ""

    for group in groups:
        for r in group["rows"]:
            i = r["orig_idx"]
            df_out.at[i, "entity_audited"] = r["entity_audited"]
            df_out.at[i, "type_audited"]   = r["type_audited"]
            df_out.at[i, "audit_status"]   = r["audit_status"]
            df_out.at[i, "audit_notes"]    = r["audit_notes"]

    buf = io.BytesIO()
    if ext == ".csv":
        df_out.to_csv(buf, index=False, encoding="utf-8-sig")
        mime = "text/csv"
    else:
        df_out.to_excel(buf, index=False)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    buf.seek(0)
    return buf, mime


# ─── Session State ─────────────────────────────────────────────────────────────
if "groups"       not in st.session_state: st.session_state.groups       = None
if "cur_law"      not in st.session_state: st.session_state.cur_law      = 0
if "cur_row"      not in st.session_state: st.session_state.cur_row      = 0
if "original_df"  not in st.session_state: st.session_state.original_df  = None
if "file_ext"     not in st.session_state: st.session_state.file_ext     = ".csv"
if "file_name"    not in st.session_state: st.session_state.file_name    = "audit_output"
if "show_filter"  not in st.session_state: st.session_state.show_filter  = "الكل"


# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-icon">⚖️</div>
  <h1>منظومة مراجعة التشريعات</h1>
  <p>مراجعة وتدقيق الجهات والأنواع المرتبطة بالقوانين والأنظمة</p>
</div>
""", unsafe_allow_html=True)


# ─── Upload ────────────────────────────────────────────────────────────────────
if st.session_state.groups is None:
    st.markdown("### 📂 رفع الملف")
    uploaded = st.file_uploader(
        "اختر ملف CSV أو Excel يحتوي على الأعمدة: leg_name · entity_final · type",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )
    if uploaded:
        try:
            df, ext = load_file(uploaded)
            required = {"leg_name", "entity_final", "type"}
            missing = required - set(df.columns)
            if missing:
                st.error(f"❌ الأعمدة التالية غير موجودة في الملف: {', '.join(missing)}")
            else:
                st.session_state.original_df = df
                st.session_state.file_ext    = ext
                st.session_state.file_name   = Path(uploaded.name).stem
                st.session_state.groups      = init_audit_state(df)
                st.session_state.cur_law     = 0
                st.session_state.cur_row     = 0
                st.rerun()
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {e}")

    st.markdown("""
    <div class="upload-hint">
        <div style="font-size:2.5rem;margin-bottom:0.5rem">📄</div>
        <div style="font-size:1rem;color:#8a95b0">اسحب الملف هنا أو انقر للاختيار</div>
        <div style="font-size:0.82rem;color:#5a6480;margin-top:6px">يدعم: CSV · XLSX · XLS</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─── Main App ──────────────────────────────────────────────────────────────────
groups   = st.session_state.groups
cur_law  = st.session_state.cur_law
cur_row  = st.session_state.cur_row

total_laws = len(groups)
total_rows = sum(len(g["rows"]) for g in groups)
reviewed   = sum(1 for g in groups for r in g["rows"] if r["audit_status"] != "لم يُراجع")
modified   = sum(1 for g in groups for r in g["rows"] if r["audit_status"] == "معدّل")
approved   = sum(1 for g in groups for r in g["rows"] if r["audit_status"] == "معتمد")
laws_done  = sum(1 for g in groups if all(r["audit_status"] != "لم يُراجع" for r in g["rows"]))

# ── Stats Bar ──
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num" style="color:#4f8ef7">{total_laws}</div>
        <div class="stat-lbl">إجمالي القوانين</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num" style="color:#c8d8ff">{total_rows}</div>
        <div class="stat-lbl">إجمالي السجلات</div>
    </div>""", unsafe_allow_html=True)
with col3:
    pct = int(reviewed / total_rows * 100) if total_rows else 0
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num" style="color:#7c5cbf">{pct}%</div>
        <div class="stat-lbl">نسبة المراجعة</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num" style="color:#2ecc8a">{approved}</div>
        <div class="stat-lbl">سجلات معتمدة</div>
    </div>""", unsafe_allow_html=True)
with col5:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num" style="color:#f7944f">{modified}</div>
        <div class="stat-lbl">سجلات معدّلة</div>
    </div>""", unsafe_allow_html=True)

# ── Progress ──
st.markdown(f"""
<div class="progress-wrap">
    <div style="display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:700;font-size:0.95rem">📊 تقدم المراجعة</span>
        <span style="color:#8a95b0;font-size:0.85rem">{laws_done} / {total_laws} قانون مكتمل · {reviewed} / {total_rows} سجل</span>
    </div>
    <div class="progress-bar-outer">
        <div class="progress-bar-inner" style="width:{pct}%"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Done? ──
all_done = reviewed == total_rows
if all_done:
    st.markdown("""
    <div class="done-banner">
        <h2>🎉 تمت مراجعة جميع السجلات!</h2>
        <p>يمكنك الآن تنزيل الملف المعدّل أدناه</p>
    </div>
    """, unsafe_allow_html=True)

# ─── Audit Interface ───────────────────────────────────────────────────────────
if cur_law >= total_laws:
    cur_law = total_laws - 1
    st.session_state.cur_law = cur_law

group   = groups[cur_law]
rows    = group["rows"]

if cur_row >= len(rows):
    cur_row = len(rows) - 1
    st.session_state.cur_row = cur_row

st.markdown("---")

# ── Law Header ──
law_status_counts = {"لم يُراجع": 0, "معتمد": 0, "معدّل": 0}
for r in rows:
    law_status_counts[r["audit_status"]] += 1

law_done_pct = int((law_status_counts["معتمد"] + law_status_counts["معدّل"]) / len(rows) * 100) if rows else 0

st.markdown(f"""
<div class="law-card">
    <div class="law-name">📜 {group["leg_name"]}</div>
    <div class="law-meta">
        القانون {cur_law + 1} من {total_laws} &nbsp;·&nbsp;
        {len(rows)} سجل &nbsp;·&nbsp;
        <span style="color:#2ecc8a">{law_status_counts["معتمد"]} معتمد</span> &nbsp;·&nbsp;
        <span style="color:#f7944f">{law_status_counts["معدّل"]} معدّل</span> &nbsp;·&nbsp;
        <span style="color:#8a95b0">{law_status_counts["لم يُراجع"]} لم يُراجع</span>
        &nbsp;&nbsp; ▪ &nbsp;{law_done_pct}% مكتمل
    </div>
</div>
""", unsafe_allow_html=True)

# ── Current Row ──
row = rows[cur_row]

badge_map = {
    "لم يُراجع": "badge-new",
    "معتمد":    "badge-ok",
    "معدّل":    "badge-edited",
}
badge_cls = badge_map.get(row["audit_status"], "badge-new")

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.8rem">
    <span style="color:#8a95b0;font-size:0.9rem">السجل {cur_row + 1} من {len(rows)}</span>
    <span class="badge {badge_cls}">{row["audit_status"]}</span>
</div>
""", unsafe_allow_html=True)

# ── Three-column layout: Entity | VS | Type ──
c_entity, c_mid, c_type = st.columns([5, 1, 5])

with c_entity:
    st.markdown(f"""
    <div style="background:#151c2e;border:1px solid #2a3352;border-radius:10px;padding:1rem;margin-bottom:0.8rem">
        <div style="font-size:0.75rem;color:#8a95b0;margin-bottom:4px">القيمة الأصلية</div>
        <div style="font-size:1.05rem;font-weight:600;color:#c8d8ff">{row["entity_final"]}</div>
    </div>
    """, unsafe_allow_html=True)
    new_entity = st.text_input(
        "✏️ الجهة المعدّلة",
        value=row["entity_audited"],
        key=f"entity_{cur_law}_{cur_row}",
        placeholder="اكتب اسم الجهة...",
    )

with c_mid:
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;height:100%;padding-top:2rem">
        <div style="font-size:1.8rem;color:#3a4460">⟷</div>
    </div>
    """, unsafe_allow_html=True)

with c_type:
    st.markdown(f"""
    <div style="background:#151c2e;border:1px solid #2a3352;border-radius:10px;padding:1rem;margin-bottom:0.8rem">
        <div style="font-size:0.75rem;color:#8a95b0;margin-bottom:4px">النوع الأصلي</div>
        <div style="font-size:1.05rem;font-weight:600;color:#c8d8ff">{row["type"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Collect unique types for suggestions
    all_types = sorted(set(
        r["type_audited"] for g in groups for r in g["rows"] if r["type_audited"]
    ))
    type_options = list(dict.fromkeys([row["type_audited"]] + all_types))

    new_type = st.selectbox(
        "✏️ النوع المعدّل",
        options=type_options,
        index=type_options.index(row["type_audited"]) if row["type_audited"] in type_options else 0,
        key=f"type_{cur_law}_{cur_row}",
    )
    # Allow free text override
    custom_type = st.text_input(
        "أو أدخل نوعاً جديداً",
        value="" if new_type == row["type_audited"] else "",
        key=f"custom_type_{cur_law}_{cur_row}",
        placeholder="نوع جديد...",
    )
    if custom_type.strip():
        new_type = custom_type.strip()

# Notes
notes = st.text_area(
    "💬 ملاحظات (اختياري)",
    value=row["audit_notes"],
    key=f"notes_{cur_law}_{cur_row}",
    placeholder="أضف ملاحظة على هذا السجل...",
    height=80,
)

st.markdown("---")

# ── Action Buttons ──
col_prev, col_approve, col_save_next, col_next = st.columns([2, 3, 3, 2])

def save_current(status):
    """Save edits to current row and update status."""
    entity_val = st.session_state.get(f"entity_{cur_law}_{cur_row}", row["entity_audited"])
    type_val   = st.session_state.get(f"type_{cur_law}_{cur_row}", row["type_audited"])
    ct         = st.session_state.get(f"custom_type_{cur_law}_{cur_row}", "").strip()
    notes_val  = st.session_state.get(f"notes_{cur_law}_{cur_row}", "")

    if ct:
        type_val = ct

    changed = (
        entity_val != row["entity_final"] or
        type_val   != row["type"]
    )
    if status == "auto":
        status = "معدّل" if changed else "معتمد"

    groups[cur_law]["rows"][cur_row]["entity_audited"] = entity_val
    groups[cur_law]["rows"][cur_row]["type_audited"]   = type_val
    groups[cur_law]["rows"][cur_row]["audit_status"]   = status
    groups[cur_law]["rows"][cur_row]["audit_notes"]    = notes_val
    st.session_state.groups = groups


def go_next():
    if st.session_state.cur_row < len(rows) - 1:
        st.session_state.cur_row += 1
    elif st.session_state.cur_law < total_laws - 1:
        st.session_state.cur_law += 1
        st.session_state.cur_row  = 0

def go_prev():
    if st.session_state.cur_row > 0:
        st.session_state.cur_row -= 1
    elif st.session_state.cur_law > 0:
        st.session_state.cur_law -= 1
        prev_len = len(groups[st.session_state.cur_law]["rows"])
        st.session_state.cur_row = prev_len - 1

with col_prev:
    if st.button("◀ السابق", use_container_width=True):
        save_current("auto")
        go_prev()
        st.rerun()

with col_approve:
    if st.button("✅ اعتماد والتالي", use_container_width=True, type="primary"):
        save_current("معتمد")
        go_next()
        st.rerun()

with col_save_next:
    if st.button("💾 حفظ التعديل والتالي", use_container_width=True):
        save_current("معدّل")
        go_next()
        st.rerun()

with col_next:
    if st.button("التالي ▶", use_container_width=True):
        save_current("auto")
        go_next()
        st.rerun()

# ── Law Navigation ──
st.markdown("---")
st.markdown("**⚡ انتقال سريع بين القوانين**")
law_cols = st.columns(min(8, total_laws))
for i, g in enumerate(groups):
    done_all = all(r["audit_status"] != "لم يُراجع" for r in g["rows"])
    has_edit = any(r["audit_status"] == "معدّل"     for r in g["rows"])
    icon = "✅" if done_all and not has_edit else ("✏️" if has_edit else "○")
    with law_cols[i % len(law_cols)]:
        lbl = f"{icon} {i+1}"
        if i == cur_law:
            lbl = f"▶ {i+1}"
        if st.button(lbl, key=f"nav_{i}", use_container_width=True):
            save_current("auto")
            st.session_state.cur_law = i
            st.session_state.cur_row = 0
            st.rerun()

# ── Row mini-map for current law ──
st.markdown(f"**سجلات القانون الحالي** ({len(rows)} سجل)")
row_cols = st.columns(min(10, len(rows)))
for j, r in enumerate(rows):
    sc = {"لم يُراجع": "○", "معتمد": "✅", "معدّل": "✏️"}.get(r["audit_status"], "○")
    with row_cols[j % len(row_cols)]:
        lbl = f"{sc} {j+1}"
        if j == cur_row:
            lbl = f"▶{j+1}"
        if st.button(lbl, key=f"rowbtn_{cur_law}_{j}", use_container_width=True):
            save_current("auto")
            st.session_state.cur_row = j
            st.rerun()

# ─── Download ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📥 تنزيل الملف المعدّل")

dcol1, dcol2 = st.columns([3, 1])
with dcol1:
    buf, mime = export_df(st.session_state.original_df, groups, st.session_state.file_ext)
    ext_show = st.session_state.file_ext
    fname = f"{st.session_state.file_name}_مراجعة{ext_show}"
    st.download_button(
        label="⬇️ تنزيل الملف المعدّل",
        data=buf,
        file_name=fname,
        mime=mime,
        use_container_width=True,
        type="primary",
    )
with dcol2:
    if st.button("🔄 رفع ملف جديد", use_container_width=True):
        for key in ["groups", "original_df", "cur_law", "cur_row", "file_ext", "file_name"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
