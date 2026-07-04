# 🎂 Birthday Wish Assistant

A modern full-stack web application that automatically opens WhatsApp with a pre-filled birthday message at your scheduled time — no WhatsApp API required.

---

## 🗂 Folder Structure

```
Message-Timer-For-Whatsapp/
├── backend/
│   ├── app.py            # Flask entry-point
│   ├── models.py         # SQLAlchemy DB models
│   ├── routes.py         # REST API routes
│   ├── scheduler.py      # APScheduler logic
│   ├── requirements.txt
│   └── birthday.db       # SQLite DB (auto-created)
└── frontend/
    ├── src/
    │   ├── components/   # React components
    │   ├── hooks/        # Custom hooks
    │   ├── App.jsx
    │   └── index.css
    ├── package.json
    └── vite.config.js
```

---

## ⚡ Quick Setup

### 1. Backend (Python Flask)

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Backend runs on → **http://localhost:5000**

### 2. Frontend (React + Vite)

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on → **http://localhost:5173**

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/schedules` | Get all scheduled wishes |
| POST | `/api/schedule` | Create a new wish |
| DELETE | `/api/schedule/<id>` | Delete a wish |
| PUT | `/api/schedule/<id>` | Edit a wish |

### Sample POST body

```json
{
  "name": "Priya Sharma",
  "phone": "+919876543210",
  "message": "Happy Birthday Priya! 🎉 Wishing you an amazing day!",
  "scheduled_datetime": "2025-12-25T10:00:00"
}
```

---

## ⏰ How the Scheduler Works

- APScheduler runs a **background job every minute**
- Checks for any scheduled wishes where `scheduled_datetime <= now` and `sent = False`
- Generates the WhatsApp link: `https://wa.me/<phone>?text=<encoded_message>`
- Opens the link in the system default browser
- Marks the record as `sent = True`

---

## ✨ Features

- 🎨 **6 message templates** — Funny, Formal, Friendly, Sweet, Inspirational, Party
- ✏️ **Edit** scheduled wishes before they're sent
- 🗑️ **Delete** any wish
- 🟢 **Test** WhatsApp link instantly
- 🌙 **Dark mode** with local storage persistence
- ✅ Full **form validation** (phone regex, future-date check)
- 🔄 **Auto-polling** every 60s to refresh sent status

---

## 🧪 Sample Test Data

| Name | Phone | Message | Time |
|------|-------|---------|------|
| Akash | +919876543210 | Happy Birthday Akash! 🎉 | 2 minutes from now |
| Priya | +917654321098 | Wishing you all the joy! 🌸 | Tomorrow 9:00 AM |
