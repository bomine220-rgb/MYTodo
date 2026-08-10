import html
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

STORAGE_FILE = Path(__file__).parent / "todos.json"
CATEGORIES = ["업무", "개인", "기타"]
CATEGORY_COLORS = {"업무": "#4f6df5", "개인": "#16a34a", "기타": "#d97706"}
ACCENT = "#4f6df5"

# 사용자가 카테고리를 직접 선택하기 전까지, 입력 텍스트의 키워드로 카테고리를 자동 추정
CATEGORY_KEYWORDS = {
    "업무": ["회의", "미팅", "보고서", "발표", "업무", "프로젝트", "메일", "이메일", "출근", "퇴근", "회사", "계약", "클라이언트", "결재", "문서", "기획", "마감", "거래처", "팀장", "상사", "출장"],
    "개인": ["운동", "헬스", "병원", "가족", "친구", "생일", "여행", "쇼핑", "취미", "독서", "영화", "데이트", "다이어트", "약속", "산책", "청소", "빨래", "요리", "부모님"],
}


def classify_category(text):
    trimmed = text.strip()
    if not trimmed:
        return None
    for cat in ("업무", "개인"):
        if any(keyword in trimmed for keyword in CATEGORY_KEYWORDS[cat]):
            return cat
    return None

st.set_page_config(page_title="할 일 관리", page_icon="📝", layout="centered")

st.markdown(
    f"""
    <style>
      .stApp {{ background: #f5f6f8; }}
      .block-container {{ max-width: 560px; padding-top: 2rem; }}
      .todo-card {{
        background: #ffffff;
        border: 1px solid #e4e6ea;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(20,20,30,0.06);
      }}
      .todo-item {{
        background: #ffffff;
        border: 1px solid #e4e6ea;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
      }}
      .todo-item.done .todo-text {{ text-decoration: line-through; color: #8a8f98; }}
      .todo-text {{ font-size: 14px; word-break: break-word; }}
      .tag {{
        font-size: 11px;
        padding: 3px 9px;
        border-radius: 20px;
        color: #fff;
        margin-left: 8px;
        white-space: nowrap;
      }}
      .dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 5px;
      }}
      .cat-progress-row {{ font-size: 12px; color: #8a8f98; margin-bottom: 4px; }}
      .footer-count {{ text-align: center; color: #8a8f98; font-size: 12px; margin-top: 8px; }}
      .empty-box {{ text-align: center; color: #8a8f98; font-size: 13px; padding: 40px 0; }}
      div[data-testid="stProgress"] > div > div > div > div {{ background-color: {ACCENT}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def load_todos():
    if STORAGE_FILE.exists():
        try:
            return json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_todos(todos):
    STORAGE_FILE.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")


def add_todo(text, category):
    trimmed = text.strip()
    if not trimmed:
        return
    st.session_state.todos.insert(
        0,
        {
            "id": uuid.uuid4().hex,
            "text": trimmed,
            "category": category,
            "completed": False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
    )
    save_todos(st.session_state.todos)


def delete_todo(todo_id):
    st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo_id]
    save_todos(st.session_state.todos)


def toggle_todo(todo_id):
    for t in st.session_state.todos:
        if t["id"] == todo_id:
            t["completed"] = not t["completed"]
            break
    save_todos(st.session_state.todos)


def update_todo(todo_id, new_text, new_category):
    trimmed = new_text.strip()
    for t in st.session_state.todos:
        if t["id"] == todo_id:
            if trimmed:
                t["text"] = trimmed
            if new_category:
                t["category"] = new_category
            break
    save_todos(st.session_state.todos)


def compute_progress(todos_list):
    if not todos_list:
        return 0
    done = sum(1 for t in todos_list if t["completed"])
    return round(done / len(todos_list) * 100)


if "todos" not in st.session_state:
    st.session_state.todos = load_todos()
if "current_filter" not in st.session_state:
    st.session_state.current_filter = "전체"
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "new_todo_text" not in st.session_state:
    st.session_state.new_todo_text = ""
if "new_todo_category" not in st.session_state:
    st.session_state.new_todo_category = "기타"
if "category_manual" not in st.session_state:
    st.session_state.category_manual = False

todos = st.session_state.todos

st.markdown("<h1 style='text-align:center; font-size:22px;'>📝 할 일 관리</h1>", unsafe_allow_html=True)

# 진행률 영역
with st.container():
    st.markdown('<div class="todo-card">', unsafe_allow_html=True)
    overall_pct = compute_progress(todos)
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.markdown("<span style='font-size:13px; color:#8a8f98;'>전체 진행률</span>", unsafe_allow_html=True)
    with top_col2:
        st.markdown(
            f"<div style='text-align:right; font-size:15px; font-weight:600;'>{overall_pct}%</div>",
            unsafe_allow_html=True,
        )
    st.progress(overall_pct / 100)

    cat_html = ""
    for cat in CATEGORIES:
        cat_list = [t for t in todos if t["category"] == cat]
        cat_pct = compute_progress(cat_list)
        cat_done = sum(1 for t in cat_list if t["completed"])
        cat_html += (
            f"<span class='cat-progress-row' style='margin-right:14px;'>"
            f"<span class='dot' style='background:{CATEGORY_COLORS[cat]};'></span>"
            f"{cat} {cat_pct}% ({cat_done}/{len(cat_list)})</span>"
        )
    st.markdown(f"<div style='margin-top:10px;'>{cat_html}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# 입력 영역
if st.session_state.pop("_reset_add_form", False):
    st.session_state["new_todo_text"] = ""
    st.session_state["new_todo_category"] = "기타"
    st.session_state["category_manual"] = False

if not st.session_state.get("category_manual", False):
    detected = classify_category(st.session_state.get("new_todo_text", ""))
    if detected:
        st.session_state["new_todo_category"] = detected


def _mark_category_manual():
    st.session_state["category_manual"] = True


col1, col2, col3 = st.columns([5, 2, 1.4])
with col1:
    st.text_input(
        "todo_input", placeholder="할 일을 입력하세요", max_chars=200, label_visibility="collapsed", key="new_todo_text"
    )
with col2:
    st.selectbox(
        "category_input",
        CATEGORIES,
        label_visibility="collapsed",
        key="new_todo_category",
        on_change=_mark_category_manual,
    )
with col3:
    add_clicked = st.button("추가", use_container_width=True)

if not st.session_state.get("category_manual", False) and detected:
    st.caption(f'🤖 "{detected}"로 자동 분류됨 (직접 선택 시 해제)')

if add_clicked:
    text_value = st.session_state.get("new_todo_text", "")
    if not text_value.strip():
        st.warning("할 일을 입력해주세요.")
    else:
        add_todo(text_value, st.session_state.get("new_todo_category", "기타"))
        st.session_state["_reset_add_form"] = True
        st.rerun()

# 필터 탭
filter_cols = st.columns(len(["전체"] + CATEGORIES))
for col, label in zip(filter_cols, ["전체"] + CATEGORIES):
    is_active = st.session_state.current_filter == label
    with col:
        if st.button(label, key=f"filter_{label}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.current_filter = label
            st.rerun()

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# 목록 영역
current_filter = st.session_state.current_filter
filtered = todos if current_filter == "전체" else [t for t in todos if t["category"] == current_filter]
filtered = sorted(filtered, key=lambda t: t["completed"])

if not filtered:
    st.markdown("<div class='empty-box'>할 일이 없습니다.</div>", unsafe_allow_html=True)
else:
    for todo in filtered:
        tid = todo["id"]
        if st.session_state.editing_id == tid:
            with st.form(f"edit_form_{tid}"):
                ecol1, ecol2, ecol3, ecol4 = st.columns([4, 2, 1, 1])
                with ecol1:
                    edit_text = st.text_input(
                        "edit_text", value=todo["text"], max_chars=200, label_visibility="collapsed"
                    )
                with ecol2:
                    edit_category = st.selectbox(
                        "edit_category",
                        CATEGORIES,
                        index=CATEGORIES.index(todo["category"]),
                        label_visibility="collapsed",
                    )
                with ecol3:
                    save_clicked = st.form_submit_button("저장")
                with ecol4:
                    cancel_clicked = st.form_submit_button("취소")
                if save_clicked:
                    update_todo(tid, edit_text, edit_category)
                    st.session_state.editing_id = None
                    st.rerun()
                if cancel_clicked:
                    st.session_state.editing_id = None
                    st.rerun()
        else:
            row_cols = st.columns([0.6, 5, 1, 1])
            with row_cols[0]:
                checked = st.checkbox("done", value=todo["completed"], key=f"chk_{tid}", label_visibility="collapsed")
                if checked != todo["completed"]:
                    toggle_todo(tid)
                    st.rerun()
            with row_cols[1]:
                text_style = "text-decoration:line-through; color:#8a8f98;" if todo["completed"] else ""
                st.markdown(
                    f"<span class='todo-text' style='{text_style}'>{html.escape(todo['text'])}</span>"
                    f"<span class='tag' style='background:{CATEGORY_COLORS[todo['category']]};'>{todo['category']}</span>",
                    unsafe_allow_html=True,
                )
            with row_cols[2]:
                if st.button("✏️", key=f"edit_{tid}"):
                    st.session_state.editing_id = tid
                    st.rerun()
            with row_cols[3]:
                if st.button("🗑️", key=f"del_{tid}"):
                    delete_todo(tid)
                    st.rerun()

total = len(todos)
done = sum(1 for t in todos if t["completed"])
if total > 0:
    st.markdown(f"<div class='footer-count'>완료됨 {done}개 / 전체 {total}개</div>", unsafe_allow_html=True)
