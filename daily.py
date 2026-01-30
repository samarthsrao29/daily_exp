import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

# ======================
# CONFIGURATION
# ======================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Trao2R-1gF1M1_ejVExiOgJzGPx5AZ4WhuWS893PQp8/export?format=csv&gid=1281822850"
MONTHLY_SUMMARY_CSV = "/Users/samarthrao/LocalFiles/daily_expenses/monthly_summary.csv"

EMAIL = os.environ["EMAIL_USER"]
APP_PASSWORD = os.environ["EMAIL_APP_PASSWORD"]
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
    "Hard Cash Amount"
]

# Convert to numeric safely
for c in cols:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)


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
current_month = datetime.now().strftime("%m/%Y")
m = df[df["Month"] == current_month]

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
Monthly Expense Report – {current_month}

Food: {summary['Food Amount']}
Travel: {summary['Travel Amount']}
Investment: {summary['Investment Amount']}
Hard Cash: {summary['Hard Cash Amount']}

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
msg["Subject"] = f"Monthly Expense Summary – {current_month}"
msg["From"] = EMAIL
msg["To"] = EMAIL

try:
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()
    print("Monthly email sent successfully!")
except Exception as e:
    print("Error sending email:", e)

# ======================
# STEP 5: PRINT SUMMARY
# ======================
print("\nRaw Form Data:\n") 
print(df)
print("\nMonthly Summary:\n")
print(monthly)
print("\nSaved and email sent successfully at", datetime.now())
