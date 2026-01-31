import argparse
from datetime import datetime, timedelta
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os

# ======================
# CONFIGURATION
# ======================

# Argument Parser
parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["update", "report"], required=True, help="Mode: update (data only) or report (send email)")
args = parser.parse_args()
# Google Sheet CSV export URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Trao2R-1gF1M1_ejVExiOgJzGPx5AZ4WhuWS893PQp8/export?format=csv&gid=1281822850"

# Folder to store CSVs (relative path, works in GitHub Actions)
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Paths
MONTHLY_SUMMARY_CSV = os.path.join(DATA_FOLDER, "monthly_summary.csv")
ALL_EXPENSES_CSV = os.path.join(DATA_FOLDER, "all_expenses.csv")

# Email from environment variables (set as GitHub Secrets)
EMAIL = os.environ.get("EMAIL_USER")
APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")

# ======================
# STEP 1: READ SHEET
# ======================
df = pd.read_csv(SHEET_URL)

# Clean column names
df.columns = df.columns.str.strip()

# Columns for expenses
cols = [
    "Food Amount",
    "Travel Amount",
    "Investment Amount",
    "Hard Cash Amount",
    "Other stuffs"
]

# Convert to numeric safely
for c in cols:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# Save full backup CSV
df.to_csv(ALL_EXPENSES_CSV, index=False)

# ======================
# STEP 2: AGGREGATE DATA
# ======================
# Extract Month from Timestamp (assumes format like "30/01/2026 21:52:53")
df["Month"] = df["Timestamp"].str[3:10]  # MM/YYYY

# Monthly totals per category
monthly = df.groupby("Month")[cols].sum()
monthly["Total"] = monthly.sum(axis=1)

# Save monthly summary CSV
monthly.to_csv(MONTHLY_SUMMARY_CSV)

# ======================
# STEP 3: INSIGHTS FOR EMAIL
# ======================
if args.mode == "report":
    # Calculate previous month (e.g., if today is Feb 1st, we want Jan)
    today = datetime.now()
    first_of_month = today.replace(day=1)
    last_month_date = first_of_month - timedelta(days=1)
    report_month = last_month_date.strftime("%m/%Y")
    
    m = df[df["Month"] == report_month]

    if not m.empty:
        summary = m[cols].sum()
        total = summary.sum()
        avg_daily = total / m["Timestamp"].nunique()
        top_category = summary.idxmax()
    else:
        summary = pd.Series(0, index=cols)
        total = 0
        avg_daily = 0
        top_category = "None"

    # Email body
    body = f"""
    Monthly Expense Report – {report_month}

    Food: {summary['Food Amount']}
    Travel: {summary['Travel Amount']}
    Investment: {summary['Investment Amount']}
    Hard Cash: {summary['Hard Cash Amount']}
    Other Stuffs: {summary['Other stuffs']}

    --------------------------
    Total Spend: {total}
    Daily Average: {round(avg_daily,2)}
    Highest Category: {top_category}

    Great job tracking your expenses 👍
    """

    # ======================
    # STEP 4: SEND EMAIL
    # ======================
    msg = MIMEText(body)
    msg["Subject"] = f"Monthly Expense Summary – {report_month}"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    try:
        print(f"DEBUG: Starting email send process...")
        print(f"DEBUG: EMAIL_USER present: {'Yes' if EMAIL else 'No'}")
        print(f"DEBUG: EMAIL_APP_PASSWORD present: {'Yes' if APP_PASSWORD else 'No'}")
        if EMAIL:
            print(f"DEBUG: EMAIL_USER length: {len(EMAIL)}")
        if APP_PASSWORD:
            print(f"DEBUG: EMAIL_APP_PASSWORD length: {len(APP_PASSWORD)}")
            
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Monthly email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)
        raise e
else:
    print("Mode is 'update', skipping email.")

# ======================
# STEP 5: PRINT SUMMARY
# ======================
print("\nRaw Form Data:\n")
print(df)
print("\nMonthly Summary:\n")
print(monthly)
print("\nSaved and email sent successfully at", datetime.now())
