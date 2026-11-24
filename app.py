"""
Smart To-Do Routine
-------------------
Organize your tasks. Plan your day. Get things done.

A Streamlit app that combines a smart To-Do list with AI-powered daily
routine planning using the Anthropic (Claude) API.

Run locally with:  streamlit run app.py
"""

from __future__ import annotations

import html
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo, available_timezones

import anthropic
import pandas as pd
import streamlit as st

# =============================================================================
# 1. CONSTANTS
# =============================================================================

APP_NAME = "Smart To-Do Routine"
TAGLINE = "Organize your tasks. Plan your day. Get things done."

CATEGORIES = [
    "Study",
    "Work",
    "Coding",
    "Graphic Design",
    "Personal",
    "Exercise",
    "Reading",
    "Other",
]
CATEGORY_ICONS = {
    "Study": "📚",
    "Work": "💼",
    "Coding": "💻",
    "Graphic Design": "🎨",
    "Personal": "🏡",
    "Exercise": "🏃",
    "Reading": "📖",
    "Other": "📌",
}
PRIORITIES = ["High", "Medium", "Low"]
PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}

PERIODS = [
    ("Morning", "🌅"),
    ("Afternoon", "☀️"),
    ("Evening", "🌆"),
    ("Night", "🌙"),
]

STATUS_FILTERS = [
    "All",
    "Today",
    "Completed",
    "Pending",
    "High Priority",
    "Medium Priority",
    "Low Priority",
]
SORT_OPTIONS = ["Priority", "Time", "Deadline", "Duration"]

DEFAULT_MODEL = "claude-sonnet-5-5"
MODEL_OPTIONS = {
    "Claude Sonnet 5.5 (balanced, recommended)": "claude-sonnet-5-5",
    "Claude Haiku 5.5 (fastest)": "claude-haiku-5-5",
    "Claude Opus 5.5 (most capable)": "claude-opus-5-5",
}

NAV_ITEMS = ["🏠 Dashboard", "✅ My Tasks", "🤖 AI Routine", "📊 Progress", "⚙️ Settings"]

RESET_CHOICES = [
    "Clear the generated routine only",
    "Clear the routine and mark today's tasks as pending again",
    "Clear the routine and delete today's tasks",
]

st.set_page_config(
    page_title=APP_NAME,
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 2. STYLING
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --primary: #4F46E5;
  --primary-soft: #EEF2FF;
  --ink: #0F172A;
  --muted: #64748B;
  --line: #E2E8F0;
  --card: #FFFFFF;
  --ok: #16A34A;
  --warn: #D97706;
  --bad: #DC2626;
}
html, body, [class*="css"], .stMarkdown, button, input, textarea {
  font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }
h1, h2, h3, h4, h5 { color: var(--ink); letter-spacing: -0.01em; }

/* Sidebar */
section[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
.brand { display:flex; align-items:center; gap:10px; margin: 4px 0 2px 0; }
.brand-logo { width:38px; height:38px; border-radius:11px; display:flex; align-items:center;
  justify-content:center; font-size:20px; color:#fff;
  background: linear-gradient(135deg,#4F46E5,#7C3AED); box-shadow: 0 6px 14px rgba(79,70,229,.30); }
.brand-name { font-weight:800; font-size:1.05rem; color: var(--ink); line-height:1.1; }
.brand-tag { font-size:.72rem; color: var(--muted); margin-bottom: 14px; }
.pill { display:inline-block; padding:4px 10px; border-radius:999px; font-size:.75rem; font-weight:600; }
.pill-ok { background:#DCFCE7; color:#166534; }
.pill-bad { background:#FEE2E2; color:#991B1B; }

/* Hero */
.hero { background: linear-gradient(135deg,#4F46E5 0%,#7C3AED 100%); color:#fff; border-radius:22px;
  padding: 26px 30px; box-shadow: 0 14px 30px rgba(79,70,229,.25); margin-bottom: 18px; }
.hero h1 { color:#fff; margin:0; font-size:1.9rem; font-weight:800; }
.hero .date { opacity:.92; font-weight:500; margin-top:4px; }
.hero .tagline { opacity:.85; margin-top:10px; font-size:.95rem; }

/* Stat cards */
.stat-card { background: var(--card); border:1px solid var(--line); border-radius:18px; padding:16px 18px;
  box-shadow: 0 2px 10px rgba(15,23,42,.04); }
.stat-top { display:flex; justify-content:space-between; align-items:center; }
.stat-label { color: var(--muted); font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
.stat-icon { width:32px; height:32px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:16px; }
.stat-value { font-size:1.9rem; font-weight:800; color: var(--ink); margin-top:6px; line-height:1.1; }
.stat-sub { color: var(--muted); font-size:.78rem; margin-top:2px; }

/* Task rows / badges */
.task-name { font-weight:700; color: var(--ink); font-size:1.0rem; }
.task-name.done { text-decoration: line-through; color: var(--muted); font-weight:600; }
.task-meta { color: var(--muted); font-size:.82rem; margin-top:4px; display:flex; flex-wrap:wrap; gap:6px 14px; align-items:center; }
.task-desc { color:#475569; font-size:.85rem; margin-top:4px; }
.badge { display:inline-block; padding:2px 9px; border-radius:999px; font-size:.72rem; font-weight:700; }
.pri-high { background:#FEE2E2; color:#B91C1C; }
.pri-medium { background:#FEF3C7; color:#B45309; }
.pri-low { background:#DCFCE7; color:#15803D; }
.st-done { background:#DCFCE7; color:#15803D; }
.st-pending { background:#E0E7FF; color:#4338CA; }
.st-overdue { background:#FEE2E2; color:#B91C1C; }
.row-card { background: var(--card); border:1px solid var(--line); border-radius:14px; padding:12px 16px; margin-bottom:8px; }

/* AI cards */
.ai-card { background: var(--primary-soft); border:1px solid #C7D2FE; border-radius:16px; padding:14px 18px; margin: 8px 0 14px 0; color:#312E81; }
.ai-card b { color:#1E1B4B; }
.sug { border-radius:14px; padding:12px 14px; margin-bottom:8px; font-size:.9rem; border:1px solid var(--line); background:#fff; }
.sug-warning { border-left:5px solid var(--warn); }
.sug-tip { border-left:5px solid var(--primary); }
.sug-info { border-left:5px solid #0EA5E9; }
.rank { display:inline-flex; width:26px; height:26px; border-radius:50%; background: var(--primary); color:#fff;
  align-items:center; justify-content:center; font-weight:700; font-size:.8rem; margin-right:8px; }

/* Timeline */
.tl-header { font-weight:800; font-size:1.15rem; margin: 20px 0 8px 0; color: var(--ink); }
.tl-item { display:flex; gap:14px; align-items:stretch; }
.tl-time { width:118px; flex-shrink:0; text-align:right; padding-top:12px; font-weight:700; color: var(--ink); font-size:.85rem; }
.tl-time span { display:block; color: var(--muted); font-weight:500; font-size:.74rem; }
.tl-rail { position:relative; width:18px; flex-shrink:0; }
.tl-rail::before { content:''; position:absolute; left:8px; top:0; bottom:0; width:2px; background: var(--line); }
.tl-dot { position:absolute; left:3px; top:16px; width:12px; height:12px; border-radius:50%; background: var(--primary); border:2px solid #fff; box-shadow: 0 0 0 2px #C7D2FE; }
.tl-item.break .tl-dot, .tl-item.meal .tl-dot, .tl-item.flex .tl-dot { background:#94A3B8; box-shadow: 0 0 0 2px #E2E8F0; }
.tl-card { flex:1; background: var(--card); border:1px solid var(--line); border-radius:14px; padding:10px 14px; margin-bottom:10px; }
.tl-item.break .tl-card, .tl-item.meal .tl-card, .tl-item.flex .tl-card { background:#F8FAFC; }
.tl-title { font-weight:700; color: var(--ink); }
.tl-badges { margin-top:4px; display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.badge-soft { background:#F1F5F9; color:#475569; }
.tl-note { color:#475569; font-size:.84rem; margin-top:5px; }

/* Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  border-radius: 12px; font-weight: 600; padding: .45rem 1rem; transition: all .15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 14px rgba(79,70,229,.18); }
div[data-testid="stForm"] { border-radius: 18px; border:1px solid var(--line); background:#fff; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:16px; }
div[data-baseweb="tab-list"] { gap: 6px; }

@media (max-width: 760px) {
  .tl-time { width:84px; font-size:.78rem; }
  .hero { padding:20px; } .hero h1 { font-size:1.45rem; }
}
</style>
"""

# =============================================================================
# 3. SMALL HELPERS (dates, times, formatting)
# =============================================================================


def esc(value: Any) -> str:
    """HTML-escape any user/AI text before putting it into custom HTML."""
    return html.escape(str(value if value is not None else ""))


def to_int(value: Any) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def parse_hhmm(value: Any) -> Optional[time]:
    if isinstance(value, time):
        return value
    if not value:
        return None
    match = re.match(r"^\s*(\d{1,2}):(\d{2})", str(value))
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if 0 <= hour < 24 and 0 <= minute < 60:
        return time(hour, minute)
    return None


def parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", ""))
    except ValueError:
        return None


def to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def fmt_clock(total_minutes: int) -> str:
    """Minutes since midnight -> '09:05 AM'."""
    total_minutes %= 1440
    hour, minute = divmod(total_minutes, 60)
    suffix = "AM" if hour < 12 else "PM"
    return f"{(hour % 12) or 12:02d}:{minute:02d} {suffix}"


def fmt_hhmm(value: str) -> str:
    parsed = parse_hhmm(value)
    return fmt_clock(to_minutes(parsed)) if parsed else ""


def fmt_duration(minutes: int) -> str:
    minutes = int(minutes)
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    return f"{hours}h" if rest == 0 else f"{hours}h {rest}m"


def detect_timezone() -> str:
    """Use the browser's timezone when Streamlit exposes it, otherwise UTC."""
    try:
        tz_name = st.context.timezone  # available in recent Streamlit versions
        if tz_name:
            return str(tz_name)
    except Exception:
        pass
    return "UTC"


def get_tz():
    name = st.session_state.get("settings", {}).get("timezone") or "UTC"
    try:
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def now() -> datetime:
    return datetime.now(get_tz())


def today() -> date:
    return now().date()


def nice_date(d: date) -> str:
    t = today()
    if d == t:
        return "Today"
    if d == t + timedelta(days=1):
        return "Tomorrow"
    if d == t - timedelta(days=1):
        return "Yesterday"
    return d.strftime("%a, %b %d")


def greeting() -> tuple[str, str]:
    hour = now().hour
    if 5 <= hour < 12:
        return "Good morning", "🌅"
    if 12 <= hour < 17:
        return "Good afternoon", "☀️"
    return "Good evening", "🌆"


def period_for(minute_of_day: int) -> str:
    hour = (minute_of_day // 60) % 24
    if 5 <= hour < 12:
        return "Morning"
    if 12 <= hour < 17:
        return "Afternoon"
    if 17 <= hour < 21:
        return "Evening"
    return "Night"


# =============================================================================
# 4. SESSION STATE & TASK STORAGE
#    (All data access goes through the functions below, so a database can be
#     plugged in later by replacing only this section.)
# =============================================================================


def default_settings() -> dict:
    return {
        "work_start": "08:00",
        "work_end": "21:00",
        "focus_time": "Morning",
        "break_minutes": 10,
        "flex_minutes": 30,
        "include_meals": True,
        "notes": "",
        "timezone": detect_timezone(),
        "model": DEFAULT_MODEL,
    }


def init_state() -> None:
    ss = st.session_state
    if ss.get("initialized"):
        return
    ss.tasks = []
    ss.next_id = 1
    ss.routine = None
    ss.prioritization = None
    ss.suggestions = None
    ss.quick_draft = None
    ss.draft_counter = 0
    ss.editing_id = None
    ss.confirm_delete = None
    ss.settings = default_settings()
    ss.initialized = True


def get_task(task_id: int) -> Optional[dict]:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            return task
    return None


def add_task(data: dict) -> dict:
    ss = st.session_state
    task = {
        "id": ss.next_id,
        "name": data["name"],
        "description": data.get("description", ""),
        "category": data.get("category", "Other"),
        "priority": data.get("priority", "Medium"),
        "date": data["date"],
        "start_time": data.get("start_time", ""),
        "duration": int(data.get("duration", 30)),
        "deadline": data.get("deadline", ""),
        "completed": False,
        "completed_on": "",
        "created_at": now().isoformat(timespec="seconds"),
    }
    ss.next_id += 1
    ss.tasks.append(task)
    return task


def update_task(task_id: int, data: dict) -> None:
    task = get_task(task_id)
    if task:
        task.update(data)


def delete_task(task_id: int) -> None:
    ss = st.session_state
    ss.tasks = [t for t in ss.tasks if t["id"] != task_id]
    if ss.editing_id == task_id:
        ss.editing_id = None
    if ss.confirm_delete == task_id:
        ss.confirm_delete = None


def set_completed(task_id: int, value: bool) -> None:
    task = get_task(task_id)
    if task:
        task["completed"] = bool(value)
        task["completed_on"] = today().isoformat() if value else ""


def name_of(task_id: Any) -> str:
    task = get_task(to_int(task_id)) if to_int(task_id) is not None else None
    return task["name"] if task else "Unknown task"


def is_overdue(task: dict) -> bool:
    if task["completed"] or not task["deadline"]:
        return False
    deadline = parse_dt(task["deadline"])
    return bool(deadline and deadline < now().replace(tzinfo=None))


def pending_tasks_for(target: date, include_overdue: bool = True) -> list[dict]:
    """Pending tasks planned for `target` (plus earlier unfinished ones)."""
    result = []
    for task in st.session_state.tasks:
        if task["completed"]:
            continue
        task_date = parse_date(task["date"])
        if task_date is None:
            continue
        if task_date == target or (include_overdue and task_date < target):
            result.append(task)
    return result


def compute_stats() -> dict:
    tasks = st.session_state.tasks
    today_iso = today().isoformat()
    todays = [t for t in tasks if t["date"] == today_iso]
    todays_done = [t for t in todays if t["completed"]]
    done_all = [t for t in tasks if t["completed"]]
    pending_all = [t for t in tasks if not t["completed"]]
    high_pending = [t for t in pending_all if t["priority"] == "High"]
    pct = round(100 * len(todays_done) / len(todays)) if todays else 0
    return {
        "total": len(tasks),
        "completed": len(done_all),
        "pending": len(pending_all),
        "high": len(high_pending),
        "today_total": len(todays),
        "today_done": len(todays_done),
        "today_remaining": len(todays) - len(todays_done),
        "pct": pct,
    }


def compute_streak() -> int:
    """Consecutive days (ending today or yesterday) with >= 1 completed task."""
    days = {
        parse_date(t["completed_on"])
        for t in st.session_state.tasks
        if t["completed"] and t["completed_on"]
    }
    days.discard(None)
    cursor = today()
    if cursor not in days:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def load_sample_tasks() -> None:
    t = today().isoformat()
    samples = [
        ("Mathematics revision", "Chapters 4 and 5, practice problems", "Study", "High", "", 60),
        ("Coding practice", "Solve two algorithm problems", "Coding", "High", "", 60),
        ("Graphic design project", "Finish the poster draft", "Graphic Design", "Medium", "", 60),
        ("Read 20 pages", "Current book", "Reading", "Low", "", 30),
        ("Workout", "Light cardio and stretching", "Exercise", "Medium", "", 30),
        ("Reply to emails", "", "Work", "Low", "", 20),
    ]
    for name, desc, cat, pri, start, dur in samples:
        add_task(
            {
                "name": name,
                "description": desc,
                "category": cat,
                "priority": pri,
                "date": t,
                "start_time": start,
                "duration": dur,
                "deadline": "",
            }
        )


# =============================================================================
# 5. AI LAYER (Anthropic / Claude)
# =============================================================================


class AIError(Exception):
    """A friendly, user-readable AI problem."""


SYSTEM_PROMPT = """You are the planning engine inside "Smart To-Do Routine", a productivity app.
You help one person organize their day. Follow these rules strictly:

1. Use ONLY the information provided. Never invent tasks, deadlines, appointments, or commitments.
   Breaks, meals, and flexible buffer time are allowed as routine structure, but label them
   clearly as breaks/meals/flex and never present them as the user's commitments.
2. Be practical and concise. Short notes, plain language, no fluff, no motivational filler.
3. Respect the user's available time window and preferences. Never schedule outside it.
4. Never let scheduled items overlap. Each item starts at or after the previous one ends.
5. Prioritize what is both urgent (deadlines) and important (High priority) first, while
   considering the user's preferred focus time of day.
6. Use the estimated duration of each task. Do not shorten or inflate durations.
7. Add realistic breaks, avoid stacking several demanding tasks back to back, and keep some
   flexible time free so the day is achievable.
8. If everything cannot fit, schedule the most important tasks and list the rest as
   unscheduled with a short reason. Do not squeeze or overlap tasks to force a fit.
9. Tasks with a "fixed_start" time must be kept at exactly that start time.
10. Refer to tasks by the numeric "task_id" you were given. Never make up ids.
11. Explain your recommendations clearly and briefly.
12. Respond with ONE valid JSON object that matches the requested schema. No markdown,
    no code fences, no text before or after the JSON. Use 24-hour "HH:MM" times."""

ROUTINE_SCHEMA = """{
  "summary": "one-sentence overview of the day",
  "items": [
    {"start": "HH:MM", "duration_min": 60, "type": "task | break | meal | flex",
     "task_id": 1 or null, "title": "short title", "note": "short note, max 18 words"}
  ],
  "unscheduled": [{"task_id": 1, "reason": "short reason"}],
  "explanation": "3-6 sentences explaining why the day is organized this way",
  "warnings": ["optional short warnings, can be empty"]
}"""

PRIORITIZE_SCHEMA = """{
  "summary": "2-3 sentences explaining the overall recommendation",
  "do_first_task_id": 1,
  "most_important_task_id": 1,
  "ranked": [{"task_id": 1, "reason": "short reason"}],
  "can_wait": [{"task_id": 2, "reason": "short reason"}],
  "groups": [{"label": "short group name", "task_ids": [1, 2], "reason": "why they go together"}]
}"""

QUICK_SCHEMA = """{
  "name": "short task name",
  "description": "string or null",
  "category": "one of the allowed categories or null",
  "date": "YYYY-MM-DD or null",
  "start_time": "HH:MM (24h) or null",
  "duration_min": integer or null,
  "priority": "High | Medium | Low | null",
  "deadline": "YYYY-MM-DD HH:MM, or YYYY-MM-DD if no time was given, or null"
}"""

SUGGEST_SCHEMA = """{
  "suggestions": [
    {"type": "warning | tip | info", "text": "one short, practical sentence"}
  ]
}"""


def get_api_key() -> Optional[str]:
    """Read the key from Streamlit secrets. Never hard-coded."""
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None
    key = str(key).strip()
    if not key or key == "your_api_key_here":
        return None
    return key


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key, timeout=90.0, max_retries=2)


def call_claude(user_prompt: str, max_tokens: int = 3000) -> str:
    """Send one request to Claude and return the text. Raises AIError."""
    api_key = get_api_key()
    if not api_key:
        raise AIError(
            "No API key found. Add ANTHROPIC_API_KEY to your Streamlit secrets "
            "(see the README, section 'API key setup')."
        )
    model = st.session_state.settings.get("model") or DEFAULT_MODEL
    try:
        client = get_client(api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.AuthenticationError:
        raise AIError("Your API key was rejected. Please check that it is correct and active.")
    except anthropic.PermissionDeniedError:
        raise AIError("Your API key does not have permission to use this model.")
    except anthropic.NotFoundError:
        raise AIError(
            f"The model '{model}' was not found. Pick another model in Settings."
        )
    except anthropic.RateLimitError:
        raise AIError("Too many requests right now. Please wait a moment and try again.")
    except anthropic.APITimeoutError:
        raise AIError("The AI took too long to respond. Please try again.")
    except anthropic.APIConnectionError:
        raise AIError("Could not reach the AI service. Check your internet connection and try again.")
    except anthropic.BadRequestError as exc:
        message = str(exc)
        if "credit" in message.lower() or "billing" in message.lower():
            raise AIError("Your Anthropic account has no available credit. Please check your billing.")
        raise AIError("The AI request was not accepted. Please try again with fewer tasks.")
    except anthropic.APIStatusError as exc:
        raise AIError(f"The AI service returned an error (status {exc.status_code}). Please try again shortly.")
    except anthropic.AnthropicError:
        raise AIError("Something went wrong while contacting the AI. Please try again.")

    text = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ).strip()
    if getattr(response, "stop_reason", "") == "max_tokens":
        raise AIError("The AI response was cut off. Try again with fewer tasks.")
    if not text:
        raise AIError("The AI returned an empty response. Please try again.")
    return text


def extract_json(text: str) -> dict:
    """Parse the JSON object in Claude's reply, tolerating stray code fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise AIError("The AI answer could not be read. Please try again.")
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            raise AIError("The AI answer was not valid. Please try again.")
    if not isinstance(data, dict):
        raise AIError("The AI answer had an unexpected format. Please try again.")
    return data


def ask_json(prompt: str, max_tokens: int = 3000) -> dict:
    return extract_json(call_claude(prompt, max_tokens))


def task_for_ai(task: dict) -> dict:
    deadline = parse_dt(task["deadline"])
    return {
        "task_id": task["id"],
        "name": task["name"],
        "description": task["description"] or None,
        "category": task["category"],
        "priority": task["priority"],
        "duration_min": task["duration"],
        "planned_date": task["date"],
        "fixed_start": task["start_time"] or None,
        "deadline": deadline.strftime("%Y-%m-%d %H:%M") if deadline else None,
    }


# ---- 5a. Smart routine ------------------------------------------------------


def ai_generate_routine(target: date, tasks: list[dict], user_note: str) -> dict:
    settings = st.session_state.settings
    current = now()
    work_start = parse_hhmm(settings["work_start"]) or time(8, 0)
    work_end = parse_hhmm(settings["work_end"]) or time(21, 0)
    earliest = to_minutes(work_start)
    if target == current.date():
        now_min = current.hour * 60 + current.minute
        now_min = ((now_min + 4) // 5) * 5  # round up to next 5 minutes
        earliest = max(earliest, now_min)

    payload = {
        "date": target.isoformat(),
        "weekday": target.strftime("%A"),
        "current_time": current.strftime("%H:%M") if target == current.date() else None,
        "available_window": {
            "earliest_start": f"{earliest // 60 % 24:02d}:{earliest % 60:02d}",
            "end": work_end.strftime("%H:%M"),
        },
        "preferences": {
            "preferred_focus_time": settings["focus_time"],
            "break_minutes_between_tasks": settings["break_minutes"],
            "flexible_free_time_minutes": settings["flex_minutes"],
            "include_meals": settings["include_meals"],
            "extra_preferences": settings["notes"] or None,
            "note_for_today": user_note or None,
        },
        "tasks": [task_for_ai(t) for t in tasks],
    }
    prompt = (
        "Create an optimized, realistic daily routine for the user. Do NOT just repeat the "
        "task list: order tasks by urgency and importance, place demanding tasks in the "
        "preferred focus time, add breaks, "
        + ("add simple meal blocks (breakfast/lunch/dinner) at sensible times, " if settings["include_meals"] else "do not add meal blocks, ")
        + "and keep the requested flexible free time. Include every given task either in "
        "'items' (type 'task') or in 'unscheduled'.\n\n"
        f"INPUT:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        f"Return JSON with exactly this shape:\n{ROUTINE_SCHEMA}"
    )
    raw = ask_json(prompt, max_tokens=4500)
    return normalize_routine(raw, tasks, target)


def normalize_routine(raw: dict, tasks: list[dict], target: date) -> dict:
    """Validate Claude's output so the UI can never break on bad data."""
    valid = {t["id"]: t for t in tasks}
    items: list[dict] = []
    raw_items = raw.get("items")
    if not isinstance(raw_items, list):
        raise AIError("The AI did not return a schedule. Please try again.")

    for entry in raw_items:
        if not isinstance(entry, dict):
            continue
        start = parse_hhmm(entry.get("start"))
        if start is None:
            continue
        duration = to_int(entry.get("duration_min"))
        if not duration or duration <= 0:
            end = parse_hhmm(entry.get("end"))
            if end is not None and to_minutes(end) > to_minutes(start):
                duration = to_minutes(end) - to_minutes(start)
        if not duration or duration <= 0:
            continue
        duration = min(duration, 720)

        task_id = to_int(entry.get("task_id"))
        kind = str(entry.get("type", "")).lower().strip()
        if kind not in {"task", "break", "meal", "flex"}:
            kind = "task" if task_id in valid else "break"
        if kind == "task" and task_id not in valid:
            kind = "flex"  # unknown task id: show it, but never as a real task

        title = str(entry.get("title") or "").strip()
        priority, category = None, None
        if kind == "task":
            local = valid[task_id]
            title = title or local["name"]
            priority, category = local["priority"], local["category"]
        title = title or {"break": "Break", "meal": "Meal", "flex": "Flexible time"}.get(kind, "Item")

        items.append(
            {
                "start_min": to_minutes(start),
                "duration": duration,
                "type": kind,
                "task_id": task_id if kind == "task" else None,
                "title": title[:120],
                "note": str(entry.get("note") or "").strip()[:240],
                "priority": priority,
                "category": category,
            }
        )

    if not items:
        raise AIError("The AI returned an empty schedule. Please try again.")
    items.sort(key=lambda i: i["start_min"])

    warnings: list[str] = []
    prev_end, prev_title = None, ""
    for item in items:
        if prev_end is not None and item["start_min"] < prev_end:
            warnings.append(f"“{item['title']}” overlaps with “{prev_title}”. Consider regenerating.")
        prev_end = item["start_min"] + item["duration"]
        prev_title = item["title"]

    for extra in raw.get("warnings") or []:
        if isinstance(extra, str) and extra.strip():
            warnings.append(extra.strip()[:200])

    unscheduled, seen = [], {i["task_id"] for i in items if i["task_id"] is not None}
    for entry in raw.get("unscheduled") or []:
        if isinstance(entry, dict) and to_int(entry.get("task_id")) in valid:
            tid = to_int(entry["task_id"])
            if tid in seen:
                continue
            unscheduled.append({"task_id": tid, "name": valid[tid]["name"], "reason": str(entry.get("reason") or "No reason given.")[:200]})
            seen.add(tid)
    for tid, task in valid.items():
        if tid not in seen:
            unscheduled.append({"task_id": tid, "name": task["name"], "reason": "The AI did not place this task. Try regenerating."})

    return {
        "date": target.isoformat(),
        "summary": str(raw.get("summary") or "").strip()[:300],
        "explanation": str(raw.get("explanation") or "").strip()[:1500],
        "items": items,
        "unscheduled": unscheduled,
        "warnings": warnings,
        "generated_at": now().strftime("%I:%M %p"),
    }


# ---- 5b. Smart prioritization ----------------------------------------------


def ai_prioritize(tasks: list[dict]) -> dict:
    payload = {
        "today": today().isoformat(),
        "current_time": now().strftime("%H:%M"),
        "tasks": [task_for_ai(t) for t in tasks],
    }
    prompt = (
        "Analyze these pending tasks. Decide which should be done first, which is most "
        "important, which can wait, and which tasks could be grouped together (same "
        "category or similar focus). Rank every task. Keep each reason to one short sentence.\n\n"
        f"INPUT:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        f"Return JSON with exactly this shape:\n{PRIORITIZE_SCHEMA}"
    )
    raw = ask_json(prompt, max_tokens=2500)

    valid = {t["id"] for t in tasks}

    def reason_list(key: str) -> list[dict]:
        out, used = [], set()
        for entry in raw.get(key) or []:
            if not isinstance(entry, dict):
                continue
            tid = to_int(entry.get("task_id"))
            if tid in valid and tid not in used:
                used.add(tid)
                out.append({"task_id": tid, "reason": str(entry.get("reason") or "")[:240]})
        return out

    ranked = reason_list("ranked")
    if not ranked:
        raise AIError("The AI did not return a usable ranking. Please try again.")
    groups = []
    for entry in raw.get("groups") or []:
        if not isinstance(entry, dict):
            continue
        ids = [to_int(i) for i in (entry.get("task_ids") or [])]
        ids = [i for i in ids if i in valid]
        if len(ids) >= 2:
            groups.append({"label": str(entry.get("label") or "Group")[:60], "task_ids": ids, "reason": str(entry.get("reason") or "")[:240]})

    first = to_int(raw.get("do_first_task_id"))
    important = to_int(raw.get("most_important_task_id"))
    return {
        "summary": str(raw.get("summary") or "").strip()[:600],
        "do_first": first if first in valid else ranked[0]["task_id"],
        "most_important": important if important in valid else ranked[0]["task_id"],
        "ranked": ranked,
        "can_wait": reason_list("can_wait"),
        "groups": groups,
        "generated_at": now().strftime("%I:%M %p"),
    }


# ---- 5c. Quick add ----------------------------------------------------------


def ai_parse_quick_task(text: str) -> dict:
    current = now()
    prompt = (
        "Turn the user's sentence into one task. Extract only what is stated or clearly "
        "implied. If something is not mentioned, use null. Never guess a duration, priority, "
        "or time that the sentence does not support. Resolve relative dates (today, tomorrow, "
        "Friday...) using the current date below. 'by 7 PM' with no date means today.\n\n"
        f"Current date: {current.strftime('%Y-%m-%d')} ({current.strftime('%A')}), "
        f"current time: {current.strftime('%H:%M')}\n"
        f"Allowed categories: {', '.join(CATEGORIES)}\n"
        f"User sentence: {json.dumps(text, ensure_ascii=False)}\n\n"
        f"Return JSON with exactly this shape:\n{QUICK_SCHEMA}"
    )
    raw = ask_json(prompt, max_tokens=800)

    name = str(raw.get("name") or "").strip()
    if not name:
        raise AIError("I could not find a task in that sentence. Try rephrasing it.")

    detected: list[str] = ["name"]
    category = raw.get("category")
    if category not in CATEGORIES:
        category = None
    else:
        detected.append("category")

    task_date = parse_date(raw.get("date")) if raw.get("date") else None
    start = parse_hhmm(raw.get("start_time")) if raw.get("start_time") else None
    duration = to_int(raw.get("duration_min"))
    if duration is None or not (5 <= duration <= 720):
        duration = None
    priority = str(raw.get("priority") or "").strip().capitalize()
    priority = priority if priority in PRIORITIES else None

    deadline_raw = str(raw.get("deadline") or "").strip()
    deadline = None
    if deadline_raw:
        deadline = parse_dt(deadline_raw)
        if deadline and len(deadline_raw) <= 10:
            deadline = deadline.replace(hour=23, minute=59)  # date only: end of that day

    if task_date:
        detected.append("date")
    if start:
        detected.append("start time")
    if duration:
        detected.append("duration")
    if priority:
        detected.append("priority")
    if deadline:
        detected.append("deadline")

    missing = [
        label
        for label, value in [
            ("category", category),
            ("duration", duration),
            ("priority", priority),
        ]
        if value is None
    ]

    defaults = {
        "name": name[:120],
        "description": str(raw.get("description") or "").strip()[:500],
        "category": category or "Other",
        "priority": priority or "Medium",
        "date": task_date or today(),
        "has_start": start is not None,
        "start": start or time(9, 0),
        "duration": duration or 30,
        "has_deadline": deadline is not None,
        "deadline_date": deadline.date() if deadline else (task_date or today()),
        "deadline_time": deadline.time().replace(second=0, microsecond=0) if deadline else time(17, 0),
    }
    return {"defaults": defaults, "detected": detected, "missing": missing}


# ---- 5d. Suggestions --------------------------------------------------------


def ai_suggestions(tasks: list[dict]) -> dict:
    settings = st.session_state.settings
    start = parse_hhmm(settings["work_start"]) or time(8, 0)
    end = parse_hhmm(settings["work_end"]) or time(21, 0)
    window = max(0, to_minutes(end) - to_minutes(start))
    pending = [t for t in tasks if not t["completed"]]
    done = [t for t in tasks if t["completed"]]
    facts = {
        "today": today().isoformat(),
        "current_time": now().strftime("%H:%M"),
        "available_window": f"{start.strftime('%H:%M')} to {end.strftime('%H:%M')} ({window} minutes)",
        "pending_count": len(pending),
        "pending_high_priority_count": sum(1 for t in pending if t["priority"] == "High"),
        "pending_total_minutes": sum(t["duration"] for t in pending),
        "completed_count": len(done),
        "overdue_count": sum(1 for t in pending if is_overdue(t)),
        "preferences": {
            "preferred_focus_time": settings["focus_time"],
            "break_minutes_between_tasks": settings["break_minutes"],
        },
        "tasks": [task_for_ai(t) | {"completed": t["completed"]} for t in tasks],
    }
    prompt = (
        "Give 3 to 5 short, practical suggestions about the user's day. Examples of useful "
        "suggestions: too many high-priority tasks, moving one task to tomorrow, a free "
        "period of a given length, taking a break after several focused tasks. Base them only "
        "on the facts given. One sentence each.\n\n"
        f"INPUT:\n{json.dumps(facts, ensure_ascii=False)}\n\n"
        f"Return JSON with exactly this shape:\n{SUGGEST_SCHEMA}"
    )
    raw = ask_json(prompt, max_tokens=900)
    out = []
    for entry in raw.get("suggestions") or []:
        if isinstance(entry, dict) and str(entry.get("text") or "").strip():
            kind = str(entry.get("type") or "tip").lower()
            out.append({"type": kind if kind in {"warning", "tip", "info"} else "tip", "text": str(entry["text"]).strip()[:260]})
    if not out:
        raise AIError("The AI did not return any suggestions. Please try again.")
    return {"items": out[:6], "generated_at": now().strftime("%I:%M %p")}


def run_ai(spinner_text: str, func: Callable, *args: Any) -> Any:
    """Run an AI function with a spinner and friendly error messages."""
    try:
        with st.spinner(spinner_text):
            return func(*args)
    except AIError as exc:
        st.error(f"🤖 {exc}")
    except Exception as exc:  # last safety net so the app never crashes
        st.error(
            "Something unexpected happened while using the AI. Please try again. "
            f"(Technical detail: {type(exc).__name__})"
        )
    return None


def api_key_banner() -> bool:
    """Show a clear setup message if the key is missing. Returns True if OK."""
    if get_api_key():
        return True
    st.error(
        "🔑 **Claude API key not found.** AI features are turned off until you add it. "
        "Create `.streamlit/secrets.toml` with `ANTHROPIC_API_KEY = \"your_key\"` "
        "(locally) or add it under *App settings → Secrets* (Streamlit Community Cloud). "
        "Your tasks still work without AI."
    )
    return False


# =============================================================================
# 6. REUSABLE UI COMPONENTS
# =============================================================================


def stat_card(icon: str, label: str, value: Any, sub: str, bg: str) -> str:
    return (
        f'<div class="stat-card"><div class="stat-top"><span class="stat-label">{esc(label)}</span>'
        f'<span class="stat-icon" style="background:{bg}">{icon}</span></div>'
        f'<div class="stat-value">{esc(value)}</div><div class="stat-sub">{esc(sub)}</div></div>'
    )


def priority_badge(priority: str) -> str:
    return f'<span class="badge pri-{esc(priority).lower()}">{esc(priority)}</span>'


def status_badge(task: dict) -> str:
    if task["completed"]:
        return '<span class="badge st-done">✓ Completed</span>'
    if is_overdue(task):
        return '<span class="badge st-overdue">Overdue</span>'
    return '<span class="badge st-pending">Pending</span>'


def task_body_html(task: dict, show_description: bool = True) -> str:
    icon = CATEGORY_ICONS.get(task["category"], "📌")
    time_text = f"🕒 {fmt_hhmm(task['start_time'])}" if task["start_time"] else "🕒 Flexible time"
    task_date = parse_date(task["date"])
    meta = [
        f"{icon} {esc(task['category'])}",
        time_text,
        f"⏱️ {esc(fmt_duration(task['duration']))}",
        f"📅 {esc(nice_date(task_date))}" if task_date else "",
    ]
    deadline = parse_dt(task["deadline"])
    if deadline:
        meta.append(f"⏳ Due {esc(deadline.strftime('%b %d, %I:%M %p'))}")
    meta_html = "".join(f"<span>{m}</span>" for m in meta if m)
    meta_html += priority_badge(task["priority"]) + status_badge(task)
    desc = (
        f'<div class="task-desc">{esc(task["description"])}</div>'
        if show_description and task["description"]
        else ""
    )
    cls = "task-name done" if task["completed"] else "task-name"
    return f'<div class="{cls}">{esc(task["name"])}</div>{desc}<div class="task-meta">{meta_html}</div>'


# ---- Task form (used for Add, Edit and Quick Add review) -------------------


def empty_defaults() -> dict:
    return {
        "name": "",
        "description": "",
        "category": "Study",
        "priority": "Medium",
        "date": today(),
        "has_start": False,
        "start": time(9, 0),
        "duration": 30,
        "has_deadline": False,
        "deadline_date": today(),
        "deadline_time": time(17, 0),
    }


def task_to_defaults(task: dict) -> dict:
    deadline = parse_dt(task["deadline"])
    return {
        "name": task["name"],
        "description": task["description"],
        "category": task["category"],
        "priority": task["priority"],
        "date": parse_date(task["date"]) or today(),
        "has_start": bool(task["start_time"]),
        "start": parse_hhmm(task["start_time"]) or time(9, 0),
        "duration": task["duration"],
        "has_deadline": deadline is not None,
        "deadline_date": deadline.date() if deadline else today(),
        "deadline_time": deadline.time() if deadline else time(17, 0),
    }


def task_form(key: str, defaults: dict, submit_label: str, clear_on_submit: bool = False) -> Optional[dict]:
    """Render a task form. Returns validated task data on submit, else None."""
    with st.form(key, clear_on_submit=clear_on_submit):
        name = st.text_input("Task name *", value=defaults["name"], placeholder="e.g. Mathematics revision", max_chars=120)
        description = st.text_area("Description", value=defaults["description"], height=80, placeholder="Optional details", max_chars=500)

        c1, c2 = st.columns(2)
        category = c1.selectbox("Category", CATEGORIES, index=CATEGORIES.index(defaults["category"]) if defaults["category"] in CATEGORIES else 0)
        priority = c2.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(defaults["priority"]) if defaults["priority"] in PRIORITIES else 1)

        c3, c4, c5 = st.columns(3)
        task_date = c3.date_input("Date", value=defaults["date"])
        duration = c4.number_input(
            "Estimated duration (minutes)",
            min_value=5,
            max_value=720,
            step=5,
            value=int(min(max(defaults["duration"], 5), 720)),
        )
        with c5:
            has_start = st.checkbox("Fixed start time", value=defaults["has_start"], help="Leave unticked to let the AI choose the best time.")
            start = st.time_input("Start time", value=defaults["start"])

        c6, c7, c8 = st.columns(3)
        has_deadline = c6.checkbox("Set a deadline", value=defaults["has_deadline"])
        deadline_date = c7.date_input("Deadline date", value=defaults["deadline_date"])
        deadline_time = c8.time_input("Deadline time", value=defaults["deadline_time"])

        submitted = st.form_submit_button(submit_label, type="primary")

    if not submitted:
        return None

    name = name.strip()
    if not name:
        st.error("Please enter a task name.")
        return None
    deadline_iso = ""
    if has_deadline:
        deadline_dt = datetime.combine(deadline_date, deadline_time)
        if deadline_dt.date() < task_date:
            st.error("The deadline is earlier than the task date. Please fix one of them.")
            return None
        deadline_iso = deadline_dt.isoformat(timespec="minutes")

    return {
        "name": name,
        "description": description.strip(),
        "category": category,
        "priority": priority,
        "date": task_date.isoformat(),
        "start_time": start.strftime("%H:%M") if has_start else "",
        "duration": int(duration),
        "deadline": deadline_iso,
    }


# ---- Quick add --------------------------------------------------------------


def cb_discard_draft() -> None:
    st.session_state.quick_draft = None


def render_quick_add(prefix: str) -> None:
    ss = st.session_state
    st.markdown("##### ⚡ Quick Add")
    with st.form(f"{prefix}_quick_form", clear_on_submit=True):
        text = st.text_input(
            "What do you need to do?",
            placeholder="e.g. Complete English homework by 7 PM",
            max_chars=300,
        )
        go = st.form_submit_button("✨ Create task from sentence")

    if go:
        if not text.strip():
            st.warning("Please type a short sentence first.")
        elif not api_key_banner():
            pass
        else:
            result = run_ai("Reading your task…", ai_parse_quick_task, text.strip())
            if result:
                ss.quick_draft = result
                ss.draft_counter += 1

    draft = ss.quick_draft
    if draft:
        detected = ", ".join(draft["detected"])
        st.markdown(
            f'<div class="ai-card">🧠 <b>Review your task.</b> Detected: {esc(detected)}.'
            + (f" Not mentioned (please check): {esc(', '.join(draft['missing']))}." if draft["missing"] else "")
            + "</div>",
            unsafe_allow_html=True,
        )
        data = task_form(f"{prefix}_draft_{ss.draft_counter}", draft["defaults"], "💾 Save task")
        if data:
            add_task(data)
            ss.quick_draft = None
            ss.flash = f"Task “{data['name']}” added ✅"
            st.rerun()
        st.button("Discard draft", key=f"{prefix}_discard", on_click=cb_discard_draft)


# ---- Suggestions panel ------------------------------------------------------


def render_suggestions_panel(prefix: str) -> None:
    ss = st.session_state
    if st.button("✨ Get AI suggestions", key=f"{prefix}_sug_btn"):
        tasks = [t for t in ss.tasks if t["date"] == today().isoformat()] + [
            t for t in pending_tasks_for(today(), True) if t["date"] != today().isoformat()
        ]
        if not tasks:
            st.info("Add some tasks first so I have something to analyze.")
        elif api_key_banner():
            result = run_ai("Thinking about your day…", ai_suggestions, tasks)
            if result:
                ss.suggestions = result

    sug = ss.suggestions
    if sug:
        icons = {"warning": "⚠️", "tip": "💡", "info": "ℹ️"}
        for item in sug["items"]:
            st.markdown(
                f'<div class="sug sug-{esc(item["type"])}">{icons[item["type"]]} {esc(item["text"])}</div>',
                unsafe_allow_html=True,
            )
        st.caption(f"Generated at {sug['generated_at']}")
    else:
        st.caption("Click the button for short, practical tips about your day.")


# =============================================================================
# 7. CALLBACKS
# =============================================================================


def cb_checkbox(task_id: int) -> None:
    set_completed(task_id, bool(st.session_state.get(f"chk_{task_id}")))


def cb_toggle(task_id: int) -> None:
    task = get_task(task_id)
    if task:
        set_completed(task_id, not task["completed"])


def cb_priority(task_id: int) -> None:
    value = st.session_state.get(f"pri_{task_id}")
    if value in PRIORITIES:
        update_task(task_id, {"priority": value})


def cb_edit(task_id: int) -> None:
    st.session_state.editing_id = task_id
    st.session_state.confirm_delete = None


def cb_cancel_edit() -> None:
    st.session_state.editing_id = None


def cb_ask_delete(task_id: int) -> None:
    st.session_state.confirm_delete = task_id


def cb_cancel_delete() -> None:
    st.session_state.confirm_delete = None


def cb_confirm_delete(task_id: int) -> None:
    name = name_of(task_id)
    delete_task(task_id)
    st.session_state.flash = f"Deleted “{name}”."


def cb_reset(prefix: str) -> None:
    ss = st.session_state
    choice = ss.get(f"{prefix}_reset_choice", RESET_CHOICES[0])
    today_iso = today().isoformat()
    ss.routine = None
    ss.suggestions = None
    ss.prioritization = None
    message = "Today's routine was cleared."
    if choice == RESET_CHOICES[1]:
        for task in ss.tasks:
            if task["date"] == today_iso:
                task["completed"], task["completed_on"] = False, ""
        message = "Routine cleared and today's tasks marked as pending."
    elif choice == RESET_CHOICES[2]:
        ss.tasks = [t for t in ss.tasks if t["date"] != today_iso]
        ss.editing_id = None
        ss.confirm_delete = None
        message = "Routine cleared and today's tasks deleted."
    ss[f"{prefix}_reset_sure"] = False
    ss.flash = message


def cb_delete_all() -> None:
    ss = st.session_state
    ss.tasks, ss.routine, ss.prioritization, ss.suggestions = [], None, None, None
    ss.editing_id, ss.confirm_delete = None, None
    ss.del_all_sure = False
    ss.flash = "All tasks were deleted."


def cb_load_samples() -> None:
    load_sample_tasks()
    st.session_state.flash = "Sample tasks added. Try the AI Routine page!"


def render_reset(prefix: str) -> None:
    with st.expander("🔄 Reset Today's Routine"):
        st.radio("What should be reset?", RESET_CHOICES, key=f"{prefix}_reset_choice")
        st.warning("This cannot be undone. Please confirm before continuing.")
        sure = st.checkbox("Yes, I understand and want to reset", key=f"{prefix}_reset_sure")
        st.button(
            "Reset now",
            key=f"{prefix}_reset_btn",
            type="primary",
            disabled=not sure,
            on_click=cb_reset,
            args=(prefix,),
        )


# =============================================================================
# 8. PAGES
# =============================================================================


def page_dashboard() -> None:
    stats = compute_stats()
    current = now()
    greet, icon = greeting()
    st.markdown(
        f'<div class="hero"><h1>{icon} {esc(greet)}!</h1>'
        f'<div class="date">📅 {esc(current.strftime("%A, %B %d, %Y"))}</div>'
        f'<div class="tagline">{esc(TAGLINE)}</div></div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    cards = [
        ("🗂️", "Total tasks", stats["total"], "all tasks", "#EEF2FF"),
        ("✅", "Completed", stats["completed"], "finished so far", "#DCFCE7"),
        ("⏳", "Pending", stats["pending"], "still to do", "#E0F2FE"),
        ("🔥", "High priority", stats["high"], "pending & important", "#FEE2E2"),
        ("🎯", "Today", f"{stats['pct']}%", f"{stats['today_done']} of {stats['today_total']} done", "#FEF3C7"),
    ]
    for col, card in zip(cols, cards):
        col.markdown(stat_card(*card), unsafe_allow_html=True)

    st.write("")
    st.markdown(f"**Today's progress** · {stats['today_done']} of {stats['today_total']} tasks completed")
    st.progress(stats["pct"] / 100)
    st.write("")

    if not st.session_state.tasks:
        st.info("👋 Welcome! Add your first task in **My Tasks**, or load a few sample tasks to explore the app.")
        st.button("Load sample tasks", on_click=cb_load_samples, key="dash_samples")

    left, right = st.columns([3, 2], gap="large")
    with left:
        render_quick_add("dash")
        st.markdown("#### 📌 Today's tasks")
        todays = sorted(
            [t for t in st.session_state.tasks if t["date"] == today().isoformat()],
            key=lambda t: (t["completed"], PRIORITY_RANK[t["priority"]], t["start_time"] or "99:99"),
        )
        if not todays:
            st.caption("No tasks planned for today yet.")
        for task in todays[:8]:
            st.markdown(f'<div class="row-card">{task_body_html(task, show_description=False)}</div>', unsafe_allow_html=True)
        if len(todays) > 8:
            st.caption(f"+ {len(todays) - 8} more in My Tasks")
    with right:
        st.markdown("#### 💡 AI Suggestions")
        render_suggestions_panel("dash")


def render_task_card(task: dict) -> None:
    ss = st.session_state
    tid = task["id"]
    ss[f"chk_{tid}"] = task["completed"]
    ss[f"pri_{tid}"] = task["priority"]

    with st.container(border=True):
        c_chk, c_body, c_pri, c_btn = st.columns([0.5, 5, 1.6, 3.4], vertical_alignment="center")
        c_chk.checkbox("Done", key=f"chk_{tid}", label_visibility="collapsed", on_change=cb_checkbox, args=(tid,))
        c_body.markdown(task_body_html(task), unsafe_allow_html=True)
        c_pri.selectbox("Priority", PRIORITIES, key=f"pri_{tid}", label_visibility="collapsed", on_change=cb_priority, args=(tid,))
        b1, b2, b3 = c_btn.columns(3)
        b1.button("↩️ Undo" if task["completed"] else "✓ Done", key=f"tog_{tid}", on_click=cb_toggle, args=(tid,))
        b2.button("✏️ Edit", key=f"edit_{tid}", on_click=cb_edit, args=(tid,))
        b3.button("🗑️ Delete", key=f"del_{tid}", on_click=cb_ask_delete, args=(tid,))

        if ss.confirm_delete == tid:
            st.warning(f"Delete “{task['name']}”? This cannot be undone.")
            d1, d2, _ = st.columns([1, 1, 4])
            d1.button("Yes, delete", key=f"yes_{tid}", type="primary", on_click=cb_confirm_delete, args=(tid,))
            d2.button("Cancel", key=f"no_{tid}", on_click=cb_cancel_delete)


def apply_filters(tasks: list[dict], status: str, categories: list[str], sort_by: str, query: str) -> list[dict]:
    today_iso = today().isoformat()
    result = []
    for task in tasks:
        if status == "Today" and task["date"] != today_iso:
            continue
        if status == "Completed" and not task["completed"]:
            continue
        if status == "Pending" and task["completed"]:
            continue
        if status.endswith("Priority") and status != "All" and task["priority"] != status.split()[0]:
            continue
        if categories and task["category"] not in categories:
            continue
        if query and query.lower() not in (task["name"] + " " + task["description"]).lower():
            continue
        result.append(task)

    rank = lambda t: PRIORITY_RANK[t["priority"]]
    if sort_by == "Priority":
        key = lambda t: (t["completed"], rank(t), t["date"], t["start_time"] or "99:99")
    elif sort_by == "Time":
        key = lambda t: (t["date"], t["start_time"] or "99:99", rank(t))
    elif sort_by == "Deadline":
        key = lambda t: (t["deadline"] or "9999-12-31T23:59", rank(t))
    else:  # Duration (shortest first)
        key = lambda t: (t["duration"], rank(t))
    return sorted(result, key=key)


def page_tasks() -> None:
    ss = st.session_state
    st.title("✅ My Tasks")
    st.caption("Add, organize, and track everything you need to do.")

    tab_add, tab_quick = st.tabs(["➕ Add Task", "⚡ Quick Add"])
    with tab_add:
        data = task_form("add_task_form", empty_defaults(), "➕ Add Task", clear_on_submit=True)
        if data:
            add_task(data)
            st.success(f"Task “{data['name']}” added ✅")
    with tab_quick:
        render_quick_add("tasks")

    # ---- Edit panel ---------------------------------------------------------
    if ss.editing_id is not None:
        task = get_task(ss.editing_id)
        if task is None:
            ss.editing_id = None
        else:
            st.markdown("### ✏️ Edit task")
            updated = task_form(f"edit_form_{task['id']}", task_to_defaults(task), "💾 Save changes")
            if updated:
                update_task(task["id"], updated)
                ss.editing_id = None
                ss.flash = "Task updated ✅"
                st.rerun()
            st.button("Cancel editing", key="cancel_edit", on_click=cb_cancel_edit)

    # ---- Filters ------------------------------------------------------------
    st.markdown("### 🗂️ Your tasks")
    if not ss.tasks:
        st.info("No tasks yet. Add one above, or load a few examples.")
        st.button("Load sample tasks", on_click=cb_load_samples, key="tasks_samples")
        return

    f1, f2, f3, f4 = st.columns([1.4, 1.6, 1.2, 1.8])
    status = f1.selectbox("Show", STATUS_FILTERS, key="flt_status")
    cats = f2.multiselect("Category", CATEGORIES, key="flt_cat", placeholder="All categories")
    sort_by = f3.selectbox("Sort by", SORT_OPTIONS, key="flt_sort")
    query = f4.text_input("Search", key="flt_query", placeholder="Search tasks…")

    shown = apply_filters(ss.tasks, status, cats, sort_by, query.strip())
    st.caption(f"Showing {len(shown)} of {len(ss.tasks)} tasks")
    if not shown:
        st.info("No tasks match these filters.")
    for task in shown:
        render_task_card(task)


# ---- AI Routine page --------------------------------------------------------


def render_timeline(routine: dict) -> None:
    groups: dict[str, list[dict]] = {name: [] for name, _ in PERIODS}
    for item in routine["items"]:
        groups[period_for(item["start_min"])].append(item)

    type_icons = {"break": "☕", "meal": "🍽️", "flex": "🌿"}
    for name, icon in PERIODS:
        items = groups[name]
        if not items:
            continue
        parts = [f'<div class="tl-header">{icon} {name}</div>']
        for item in items:
            start = fmt_clock(item["start_min"])
            end = fmt_clock(item["start_min"] + item["duration"])
            if item["type"] == "task":
                title_icon = CATEGORY_ICONS.get(item["category"], "📌")
            else:
                title_icon = type_icons.get(item["type"], "•")
            badges = f'<span class="badge badge-soft">⏱️ {esc(fmt_duration(item["duration"]))}</span>'
            if item["priority"]:
                badges += priority_badge(item["priority"])
            else:
                badges += f'<span class="badge badge-soft">{esc(item["type"].capitalize())}</span>'
            note = f'<div class="tl-note">💬 {esc(item["note"])}</div>' if item["note"] else ""
            parts.append(
                f'<div class="tl-item {esc(item["type"])}">'
                f'<div class="tl-time">{esc(start)}<span>to {esc(end)}</span></div>'
                f'<div class="tl-rail"><div class="tl-dot"></div></div>'
                f'<div class="tl-card"><div class="tl-title">{title_icon} {esc(item["title"])}</div>'
                f'<div class="tl-badges">{badges}</div>{note}</div></div>'
            )
        st.markdown("".join(parts), unsafe_allow_html=True)


def tab_routine() -> None:
    ss = st.session_state
    c1, c2 = st.columns([1, 2])
    target = c1.date_input("Plan the day for", value=today(), key="routine_date")
    include_overdue = c2.checkbox("Include unfinished tasks from earlier days", value=True, key="routine_overdue")
    user_note = st.text_input(
        "Anything the AI should know today? (optional)",
        key="routine_note",
        placeholder="e.g. I have a class from 2 PM to 3 PM",
        max_chars=250,
    )
    s = ss.settings
    st.caption(
        f"Using your preferences: {fmt_hhmm(s['work_start'])} – {fmt_hhmm(s['work_end'])}, "
        f"focus time: {s['focus_time'].lower()}, {s['break_minutes']}-min breaks. Change them in ⚙️ Settings."
    )

    if st.button("🚀 Generate My Smart Routine", type="primary", key="gen_routine"):
        tasks = pending_tasks_for(target, include_overdue)
        if not ss.tasks:
            st.info("Your task list is empty. Add a few tasks first, then come back.")
        elif not tasks:
            st.info("There are no pending tasks for that day. Pick another date or add a task.")
        elif api_key_banner():
            result = run_ai("Claude is building your routine…", ai_generate_routine, target, tasks, user_note.strip())
            if result:
                ss.routine = result
                st.toast("Routine ready ✨")

    routine = ss.routine
    if not routine:
        st.caption("Your routine will appear here as a timeline.")
        return

    day = parse_date(routine["date"])
    st.markdown(f"### 🗓️ Routine for {esc(nice_date(day) if day else routine['date'])}")
    if routine["summary"]:
        st.markdown(f'<div class="ai-card">✨ <b>{esc(routine["summary"])}</b></div>', unsafe_allow_html=True)
    for warning in routine["warnings"]:
        st.warning(warning)

    render_timeline(routine)

    if routine["unscheduled"]:
        st.markdown("#### 📥 Not scheduled")
        for entry in routine["unscheduled"]:
            st.markdown(
                f'<div class="row-card"><b>{esc(entry["name"])}</b><div class="task-desc">{esc(entry["reason"])}</div></div>',
                unsafe_allow_html=True,
            )
    if routine["explanation"]:
        with st.expander("🧠 Why this schedule?", expanded=True):
            st.write(routine["explanation"])
    st.caption(f"Generated at {routine['generated_at']}")


def tab_prioritize() -> None:
    ss = st.session_state
    st.caption("Claude looks at all your pending tasks and tells you what to do first, what matters most, and what can wait.")
    if st.button("🎯 Smart Prioritize Tasks", type="primary", key="prioritize_btn"):
        tasks = [t for t in ss.tasks if not t["completed"]]
        if not ss.tasks:
            st.info("Your task list is empty. Add a few tasks first.")
        elif not tasks:
            st.success("🎉 Nothing pending. All your tasks are complete!")
        elif api_key_banner():
            result = run_ai("Analyzing your tasks…", ai_prioritize, tasks)
            if result:
                ss.prioritization = result

    result = ss.prioritization
    if not result:
        return
    if result["summary"]:
        st.markdown(f'<div class="ai-card">🧠 {esc(result["summary"])}</div>', unsafe_allow_html=True)

    a, b = st.columns(2)
    a.markdown(f'<div class="stat-card"><div class="stat-label">🥇 Do this first</div><div class="task-name" style="margin-top:8px">{esc(name_of(result["do_first"]))}</div></div>', unsafe_allow_html=True)
    b.markdown(f'<div class="stat-card"><div class="stat-label">⭐ Most important</div><div class="task-name" style="margin-top:8px">{esc(name_of(result["most_important"]))}</div></div>', unsafe_allow_html=True)

    st.markdown("#### 📋 Recommended order")
    for index, entry in enumerate(result["ranked"], start=1):
        st.markdown(
            f'<div class="row-card"><span class="rank">{index}</span><b>{esc(name_of(entry["task_id"]))}</b>'
            f'<div class="task-desc">{esc(entry["reason"])}</div></div>',
            unsafe_allow_html=True,
        )
    if result["can_wait"]:
        st.markdown("#### 🕰️ Can wait")
        for entry in result["can_wait"]:
            st.markdown(
                f'<div class="row-card"><b>{esc(name_of(entry["task_id"]))}</b>'
                f'<div class="task-desc">{esc(entry["reason"])}</div></div>',
                unsafe_allow_html=True,
            )
    if result["groups"]:
        st.markdown("#### 🧩 Group together")
        for group in result["groups"]:
            names = ", ".join(name_of(i) for i in group["task_ids"])
            st.markdown(
                f'<div class="row-card"><b>{esc(group["label"])}</b>: {esc(names)}'
                f'<div class="task-desc">{esc(group["reason"])}</div></div>',
                unsafe_allow_html=True,
            )
    st.caption(f"Generated at {result['generated_at']}")


def page_ai_routine() -> None:
    st.title("🤖 AI Routine")
    st.caption("Let Claude turn your task list into a realistic, balanced day.")
    api_key_banner()
    tab1, tab2, tab3 = st.tabs(["🗓️ Smart Routine", "🎯 Prioritize", "💡 Suggestions"])
    with tab1:
        tab_routine()
    with tab2:
        tab_prioritize()
    with tab3:
        st.caption("Quick, practical tips based on today's tasks.")
        render_suggestions_panel("ai")
    st.write("")
    render_reset("ai")


# ---- Progress page ----------------------------------------------------------


def page_progress() -> None:
    ss = st.session_state
    st.title("📊 Progress")
    st.caption("See how you are doing today and across the week.")
    stats = compute_stats()
    streak = compute_streak()

    cols = st.columns(4)
    cards = [
        ("✅", "Completed today", stats["today_done"], "tasks done", "#DCFCE7"),
        ("⏳", "Remaining today", stats["today_remaining"], "tasks left", "#E0F2FE"),
        ("🎯", "Completion", f"{stats['pct']}%", "of today's tasks", "#FEF3C7"),
        ("🔥", "Current streak", f"{streak}", "day" + ("" if streak == 1 else "s") + " in a row", "#FEE2E2"),
    ]
    for col, card in zip(cols, cards):
        col.markdown(stat_card(*card), unsafe_allow_html=True)

    st.write("")
    st.markdown("**Today**")
    st.progress(stats["pct"] / 100)

    # Weekly data (last 7 days)
    days = [today() - timedelta(days=i) for i in range(6, -1, -1)]
    rows = []
    for d in days:
        iso = d.isoformat()
        planned = sum(1 for t in ss.tasks if t["date"] == iso)
        done = sum(1 for t in ss.tasks if t["completed"] and t["completed_on"] == iso)
        rows.append({"Day": d.strftime("%a %d"), "Completed": done, "Planned": planned})
    frame = pd.DataFrame(rows).set_index("Day")
    week_done, week_planned = int(frame["Completed"].sum()), int(frame["Planned"].sum())
    week_pct = min(100, round(100 * week_done / week_planned)) if week_planned else 0

    st.markdown("### 📅 This week")
    st.markdown(f"**{week_done}** completed · **{week_planned}** planned in the last 7 days")
    st.progress(week_pct / 100)
    st.bar_chart(frame, color=["#4F46E5", "#CBD5E1"])

    by_cat: dict[str, int] = {}
    for t in ss.tasks:
        if t["completed"]:
            by_cat[t["category"]] = by_cat.get(t["category"], 0) + 1
    st.markdown("### 🏷️ Completed by category")
    if by_cat:
        st.bar_chart(pd.DataFrame({"Completed": by_cat}), color="#7C3AED")
    else:
        st.caption("Complete a task to see your category breakdown.")
    if not ss.tasks:
        st.info("No data yet. Add tasks and complete them to see your progress.")


# ---- Settings page ----------------------------------------------------------


def page_settings() -> None:
    ss = st.session_state
    s = ss.settings
    st.title("⚙️ Settings")
    st.caption("These preferences are sent to Claude when it plans your routine.")

    zones = sorted(available_timezones()) or ["UTC"]
    if s["timezone"] not in zones:
        zones = ["UTC"] + [z for z in zones if z != "UTC"]
    models = list(MODEL_OPTIONS.keys())
    current_model = next((label for label, mid in MODEL_OPTIONS.items() if mid == s["model"]), models[0])

    with st.form("settings_form"):
        st.markdown("##### 🕒 Your day")
        c1, c2 = st.columns(2)
        work_start = c1.time_input("Day starts", value=parse_hhmm(s["work_start"]) or time(8, 0))
        work_end = c2.time_input("Day ends", value=parse_hhmm(s["work_end"]) or time(21, 0))
        focus_options = ["Morning", "Afternoon", "Evening", "Night", "No preference"]
        focus = st.selectbox("Preferred working / study time", focus_options, index=focus_options.index(s["focus_time"]) if s["focus_time"] in focus_options else 0)
        c3, c4 = st.columns(2)
        break_minutes = c3.slider("Break between tasks (minutes)", 5, 30, int(s["break_minutes"]), step=5)
        flex_minutes = c4.slider("Flexible free time (minutes)", 0, 120, int(s["flex_minutes"]), step=15)
        include_meals = st.checkbox("Include meals in my routine", value=s["include_meals"])
        notes = st.text_area("Other preferences (optional)", value=s["notes"], height=80, placeholder="e.g. I prefer lighter tasks right after lunch", max_chars=400)

        st.markdown("##### 🌍 Region & AI model")
        timezone_name = st.selectbox("Timezone", zones, index=zones.index(s["timezone"]) if s["timezone"] in zones else 0)
        model_label = st.selectbox("Claude model", models, index=models.index(current_model))
        saved = st.form_submit_button("💾 Save settings", type="primary")

    if saved:
        if to_minutes(work_end) - to_minutes(work_start) < 60:
            st.error("Your day should be at least one hour long. Please adjust the start and end times.")
        else:
            ss.settings = {
                "work_start": work_start.strftime("%H:%M"),
                "work_end": work_end.strftime("%H:%M"),
                "focus_time": focus,
                "break_minutes": int(break_minutes),
                "flex_minutes": int(flex_minutes),
                "include_meals": include_meals,
                "notes": notes.strip(),
                "timezone": timezone_name,
                "model": MODEL_OPTIONS[model_label],
            }
            st.success("Settings saved ✅")

    st.markdown("### 🔑 API status")
    if get_api_key():
        st.success("Claude API key found in Streamlit secrets.")
    else:
        api_key_banner()

    st.markdown("### 🗃️ Your data")
    st.caption("Tasks live in this browser session only. Refreshing the page clears them. Export a backup if you need one.")
    export = json.dumps(ss.tasks, indent=2, ensure_ascii=False)
    d1, d2 = st.columns([1, 1])
    d1.download_button("⬇️ Export tasks (JSON)", data=export, file_name="smart_todo_tasks.json", mime="application/json", disabled=not ss.tasks)
    d2.button("Load sample tasks", on_click=cb_load_samples, key="settings_samples")

    render_reset("settings")
    with st.expander("🗑️ Delete ALL tasks"):
        st.warning("This removes every task and every AI result. It cannot be undone.")
        sure = st.checkbox("Yes, delete everything", key="del_all_sure")
        st.button("Delete all tasks", type="primary", disabled=not sure or not ss.tasks, on_click=cb_delete_all, key="del_all_btn")


# =============================================================================
# 9. SIDEBAR & MAIN
# =============================================================================


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f'<div class="brand"><div class="brand-logo">✓</div><div class="brand-name">{esc(APP_NAME)}</div></div>'
            f'<div class="brand-tag">{esc(TAGLINE)}</div>',
            unsafe_allow_html=True,
        )
        st.radio("Navigation", NAV_ITEMS, key="nav", label_visibility="collapsed")
        st.divider()
        stats = compute_stats()
        st.caption(f"Today: {stats['today_done']}/{stats['today_total']} done · {stats['pct']}%")
        st.progress(stats["pct"] / 100)
        if get_api_key():
            st.markdown('<span class="pill pill-ok">● Claude connected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="pill pill-bad">● API key missing</span>', unsafe_allow_html=True)


PAGES = {
    "🏠 Dashboard": page_dashboard,
    "✅ My Tasks": page_tasks,
    "🤖 AI Routine": page_ai_routine,
    "📊 Progress": page_progress,
    "⚙️ Settings": page_settings,
}


def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    render_sidebar()
    flash = st.session_state.pop("flash", None)
    if flash:
        st.toast(flash)
    page = PAGES.get(st.session_state.get("nav"), page_dashboard)
    try:
        page()
    except Exception as exc:  # final safety net: never show a raw traceback
        st.error(
            "Something went wrong while showing this page. Try another page or refresh. "
            f"(Technical detail: {type(exc).__name__}: {exc})"
        )


main()
