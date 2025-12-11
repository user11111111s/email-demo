# 📧 IEI Automated Email Dispatch System

An automated bulk email dispatching system built with Python and Flask. This powerful tool allows you to schedule campaigns, track open/click rates, and manage recipients via CSV/Excel uploads.

## 🚀 Features
- **Secure Authentication**: Uses App-Specific Passwords for Gmail/SMTP integration.
- **Bulk Sending**: Efficiently handles email dispatching.
- **Campaign Management**: Organize emails into campaigns.
- **Analytics Dashboard**: Real-time tracking of:
  - 📩 Sent Emails
  - 👁️ Opened Emails (Pixel Tracking)
  - 🔗 Clicked Links
  - ❌ Bounced/Failed Deliveries
- **Rich Editor**: WYSIWYG editor for composing beautiful emails.

---

## 🛠️ Setup Instructions

### 1. Prerequisites
- **Python 3.8+** must be installed.
- **Git** (optional, for cloning).

### 2. Installation
1.  **Open a Terminal** in the project folder:
    ```bash
    cd "path/to/IEI_Automated_Email_dispatch"
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment**:
    - **Windows**:
      ```powershell
      .\venv\Scripts\activate
      ```
    - **Mac/Linux**:
      ```bash
      source venv/bin/activate
      ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Running the Application
1.  **Initialize the Database** (First time only):
    The app will automatically create `app.db` when you run it for the first time.

2.  **Start the Server**:
    ```bash
    python run.py
    ```

3.  **Access the App**:
    Open your browser and navigate to:
    👉 **http://127.0.0.1:5000**

---

## ⚙️ Configuration Notes
- **App Passwords**: If using Gmail, you MUST enable 2-Factor Authentication and generate an "App Password". Do not use your regular login password.
- **Tracking**: For open/click tracking to work effectively, the application must be running. If sending to real external users, this app needs to be hosted on a public server or exposed via a tunnel (like `ngrok`).

---
**Created for IEI Lab**
