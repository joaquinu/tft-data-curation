# Email Notification Setup

## Quick Setup (Gmail)

To enable email alerts for the data collection pipeline:

### 1. Get a Gmail App Password
*Note: You cannot use your main Gmail password.*

1.  Go to **[Google Account Security](https://myaccount.google.com/security)**.
2.  Enable **2-Step Verification** (if not already enabled).
3.  Search for **"App passwords"** in the top search bar.
4.  Create a new app password (name it "TFT Project").
5.  **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`).

### 2. Configure Environment Access
Securely store credentials in your `.env` file (DO NOT commit this file).

**Command Line:**
```bash
echo 'EMAIL_PASSWORD="abcd efgh ijkl mnop"' >> .env
```

### 3. Update Configuration
Edit `config/config.yaml` to enable notifications:

```yaml
notifications:
  enabled: true
  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    use_tls: true
    from_address: your.email@gmail.com   # Your Gmail
    to_addresses:
      - your.email@gmail.com             # Who receives alerts
    username: your.email@gmail.com       # Your Gmail
    password: ${EMAIL_PASSWORD}          # Reads from env var
```

---

## 🧪 Testing

Verify the setup immediately with this one-liner script:

```python
# Create test_email.py
from scripts.notification_system import EmailNotificationSystem
import os

# Mock configuration
config = {
    'notifications': {
        'enabled': True,
        'email': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'from_address': 'your.email@gmail.com', # Update this
            'to_addresses': ['your.email@gmail.com'], # Update this
            'username': 'your.email@gmail.com', # Update this
            'password': os.getenv('EMAIL_PASSWORD') # Reads env var
        }
    }
}

try:
    notifier = EmailNotificationSystem(config)
    notifier.send_collection_summary({
        'success': True,
        'players_collected': 1,
        'matches_collected': 1,
        'total_errors': 0
    }, 'TEST-RUN')
    print("✅ Test email sent successfully!")
except Exception as e:
    print(f"❌ Failed: {e}")
```

Run it:
```bash
python3 test_email.py
```

---

## 🔔 Notification Triggers

The system automatically sends emails for:

1.  **Collection Summary**: After every automated weekly run.
2.  **Quality Warning**: If `quality_score < 70`.
3.  **Error Alert**: If `error_count > 10`.
4.  **Critical Failure**: Pipeline crash.

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Username and Password not accepted` | Ensure you are using the **App Password**, not your Google password. |
| `ConnectionRefusedError` | Check if `smtp_port` is 587 and `use_tls` is `true`. |
| No email received | Check Spam/Junk folder. |

**Security Note**: Never commit `EMAIL_PASSWORD` to GitHub. Always use `.env`.

