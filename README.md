# ✅ Smart To-Do Routine

> **Organize your tasks. Plan your day. Get things done.**

Smart To-Do Routine is an AI-powered productivity app built with **Python, Streamlit, and the Claude API**. It combines a smart task list with daily routine planning: add tasks, set priorities and durations, and let Claude turn them into a realistic, balanced schedule with breaks and flexible time.

---

## ✨ Features

- **Dashboard**: greeting, today's date, task statistics, completion percentage, and a progress bar
- **Task management**: add, edit, delete, complete/undo, change priority, filter, sort, and search
- **Task details**: name, description, category, date, start time, estimated duration, priority, optional deadline
- **AI Smart Routine**: Claude builds an optimized schedule that respects priorities, deadlines, durations, and your preferred focus time, adds breaks, avoids overlaps, and leaves flexible time
- **Daily timeline**: grouped into 🌅 Morning, ☀️ Afternoon, 🌆 Evening, 🌙 Night, with a short AI note per item and an explanation of the plan
- **Smart Prioritize**: what to do first, what matters most, what can wait, and what to group together
- **Quick Add**: type a sentence such as *"Complete English homework by 7 PM"* and review the extracted task. Missing details stay editable and are never invented
- **AI Suggestions**: short, practical tips about your day
- **Progress tracking**: today's progress, weekly chart, completion rate, and current streak
- **Safe resets**: confirmation before resetting the routine or deleting data
- **Friendly error handling**: missing API key, invalid input, API/network errors, empty task list, and invalid AI responses never crash the app

## 🖼️ Screenshots

> Add your screenshots here after running the app. **Do not include screenshots that show your API key.**

| Dashboard | AI Routine |
|-----------|------------|
| _screenshot placeholder_ | _screenshot placeholder_ |

## 🛠️ Technologies Used

- [Python](https://www.python.org/) 3.10 or newer
- [Streamlit](https://streamlit.io/)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) (Claude API)
- [pandas](https://pandas.pydata.org/) (charts)

## 📁 Project Structure

```text
smart-todo-routine/
│
├── app.py                         # The complete application
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── .gitignore                     # Keeps secrets out of GitHub
│
└── .streamlit/
    ├── secrets.toml.example       # Template for your API key (safe to commit)
    └── config.toml                # Theme settings
```

Your real key goes in `.streamlit/secrets.toml`, which is **ignored by Git** and must never be uploaded.

## 🚀 Installation

### 1. Get the project

Create a folder named `smart-todo-routine` and place all the files inside it, keeping the structure above (including the `.streamlit` folder).

### 2. Create a virtual environment

**Windows (PowerShell)**

```bash
cd smart-todo-routine
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
cd smart-todo-routine
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔑 API Key Setup

1. Create an account at [console.anthropic.com](https://console.anthropic.com/) and generate an API key.
2. Make sure your account has credit available.
3. Keep the key private. Never paste it into `app.py`, the README, screenshots, or GitHub.

### Streamlit secrets setup (local)

1. Inside `.streamlit/`, copy `secrets.toml.example` to a new file named `secrets.toml`.
2. Open `secrets.toml` and replace the placeholder:

```toml
ANTHROPIC_API_KEY = "your_api_key_here"
```

The app reads the key with `st.secrets["ANTHROPIC_API_KEY"]`. If it is missing, the app still works for tasks and shows a clear message for AI features.

## ▶️ Run Locally

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually http://localhost:8501).

**Tip:** on the Dashboard or in Settings, click **Load sample tasks**, then open **🤖 AI Routine** and click **Generate My Smart Routine**.

## 💾 About Your Data

This first version stores tasks in **Streamlit session state**. Tasks stay available while you use the app, but they are cleared when you refresh the page or close the session. Use **Settings → Export tasks** to download a JSON backup.

All task reading and writing lives in one section of `app.py` ("SESSION STATE & TASK STORAGE"), so a database such as SQLite can be added later without rewriting the interface.

## 🐙 Upload to GitHub

1. Make a ZIP backup of your folder (optional but recommended).
2. Check that `.streamlit/secrets.toml` is **not** going to be uploaded (the included `.gitignore` already excludes it).
3. Create a new empty repository on [github.com](https://github.com/new) named `smart-todo-routine`.
4. In your project folder, run:

```bash
git init
git add .
git status        # confirm secrets.toml is NOT in the list
git commit -m "Initial commit: Smart To-Do Routine"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/smart-todo-routine.git
git push -u origin main
```

> ⚠️ If you ever commit a real API key by accident, **revoke it immediately** in the Anthropic Console and create a new one. Deleting the file later is not enough because Git keeps history.

## ☁️ Deploy on Streamlit Community Cloud

1. Push your project to GitHub (see above).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. Click **Create app** and choose your repository, the `main` branch, and `app.py` as the main file.
4. Open **Advanced settings → Secrets** and paste:

```toml
ANTHROPIC_API_KEY = "your_real_key_here"
```

5. Click **Deploy**. Your app will be live at a `*.streamlit.app` URL.

The app detects your browser's timezone automatically. You can change it in **Settings**.

## 🧰 Troubleshooting

| Problem | Fix |
|---|---|
| "API key not found" | Create `.streamlit/secrets.toml` (local) or add the secret in Streamlit Cloud, then restart the app |
| "Your API key was rejected" | Check for typos or extra spaces, or create a new key |
| "Model was not found" | Pick another model in **Settings → Claude model** |
| "No available credit" | Add credit in the Anthropic Console |
| Greeting or times look wrong | Set your timezone in **Settings** |

## 🔮 Future Improvements

- Persistent storage (SQLite, Supabase, or Firebase) and user accounts
- Recurring tasks and reminders
- Drag-and-drop timeline editing
- Calendar import/export (Google Calendar, `.ics`)
- Task subtasks and tags
- Weekly AI review and habit insights
- Dark mode theme
- Voice input for Quick Add
- Notifications by email or Telegram

## 📄 License

Add the license of your choice (for example MIT) before publishing.
