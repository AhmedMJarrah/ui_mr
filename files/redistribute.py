"""
redistribute.py
Run ONCE from Streamlit to redistribute unreviewed laws between 4 users.
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time

SPREADSHEET_ID = "1svY3lp6RUTp4K-bigbx2JDAeh8RNLACsuXCYqxP4QgQ"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.title("⚙️ إعادة توزيع القوانين — تشغيل مرة واحدة فقط")
st.info("""
**الخطة:**
- leen (النصف 1): تحتفظ بـ 461 قانون غير مراجَع (الأوائل)
- diwan (النصف 2): تحتفظ بـ 461 قانون غير مراجَع (الأوائل)
- law1 (النصف 3): يحصل على آخر 458 قانون من leen
- law2 (النصف 4): يحصل على آخر 464 قانون من diwan
- جميع السجلات المراجَعة تبقى كما هي ✅
""")

if st.button("🚀 تنفيذ إعادة التوزيع", type="primary"):
    try:
        # Connect
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
        client = gspread.authorize(creds)
        sp     = client.open_by_key(SPREADSHEET_ID)
        ws     = sp.worksheet("master_data")

        st.info("جارٍ تحميل البيانات...")
        all_values = ws.get_all_values()
        headers    = all_values[0]
        rows       = all_values[1:]

        # Find column indices
        idx_row_id      = headers.index("row_id")
        idx_leg_name    = headers.index("leg_name")
        idx_status      = headers.index("audit_status")
        idx_assigned    = headers.index("assigned_to")

        st.info(f"تم تحميل {len(rows)} سجل")

        # Separate unreviewed by user
        u1_unreviewed_laws = []  # ordered list of unique laws
        u2_unreviewed_laws = []
        u1_seen = set()
        u2_seen = set()

        for row in rows:
            assigned = str(row[idx_assigned]).strip()
            status   = str(row[idx_status]).strip()
            law      = str(row[idx_leg_name]).strip()
            if status == "لم يُراجع":
                if assigned == "1" and law not in u1_seen:
                    u1_unreviewed_laws.append(law)
                    u1_seen.add(law)
                elif assigned == "2" and law not in u2_seen:
                    u2_unreviewed_laws.append(law)
                    u2_seen.add(law)

        st.info(f"قوانين leen غير المراجَعة: {len(u1_unreviewed_laws)}")
        st.info(f"قوانين diwan غير المراجَعة: {len(u2_unreviewed_laws)}")

        # Calculate split — keep first ~461, give away the rest from the end
        total    = len(u1_unreviewed_laws) + len(u2_unreviewed_laws)
        each     = total // 4

        give_u1  = len(u1_unreviewed_laws) - each   # 458
        give_u2  = len(u2_unreviewed_laws) - each   # 464

        laws_to_law1 = set(u1_unreviewed_laws[-give_u1:])  # last 458 from u1
        laws_to_law2 = set(u2_unreviewed_laws[-give_u2:])  # last 464 from u2

        st.info(f"قوانين تنتقل من leen → law1: {len(laws_to_law1)}")
        st.info(f"قوانين تنتقل من diwan → law2: {len(laws_to_law2)}")

        # Build batch updates
        updates = []
        assigned_col_letter = chr(ord('A') + idx_assigned)  # column letter

        for i, row in enumerate(rows):
            assigned = str(row[idx_assigned]).strip()
            status   = str(row[idx_status]).strip()
            law      = str(row[idx_leg_name]).strip()
            sheet_row = i + 2  # +1 for header, +1 for 1-indexed

            if status == "لم يُراجع":
                if assigned == "1" and law in laws_to_law1:
                    updates.append({
                        "range": f"{assigned_col_letter}{sheet_row}",
                        "values": [["3"]]
                    })
                elif assigned == "2" and law in laws_to_law2:
                    updates.append({
                        "range": f"{assigned_col_letter}{sheet_row}",
                        "values": [["4"]]
                    })

        st.info(f"إجمالي الخلايا المحدَّثة: {len(updates)}")

        # Batch update in chunks of 500
        chunk_size = 500
        total_chunks = (len(updates) + chunk_size - 1) // chunk_size
        progress = st.progress(0)

        for idx_c, i in enumerate(range(0, len(updates), chunk_size)):
            chunk = updates[i:i + chunk_size]
            for attempt in range(4):
                try:
                    ws.batch_update(chunk)
                    break
                except gspread.exceptions.APIError as e:
                    if "429" in str(e) and attempt < 3:
                        time.sleep(8 * (attempt + 1))
                    else:
                        raise
            progress.progress((idx_c + 1) / total_chunks)
            time.sleep(1)  # avoid rate limits

        st.success(f"""
        ✅ تم إعادة التوزيع بنجاح!
        - leen: تحتفظ بـ {each} قانون غير مراجَع
        - diwan: تحتفظ بـ {each} قانون غير مراجَع
        - law1: حصل على {give_u1} قانون جديد
        - law2: حصل على {give_u2} قانون جديد
        """)
        st.warning("⚠️ احذف هذا الملف من GitHub بعد التشغيل!")

    except Exception as e:
        st.error(f"خطأ: {e}")
        st.exception(e)
