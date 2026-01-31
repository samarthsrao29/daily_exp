import argparse
from datetime import datetime, timedelta

# ======================
# CONFIGURATION
# ======================

# Argument Parser
parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["update", "report"], required=True, help="Mode: update (data only) or report (send email)")
args = parser.parse_args()

# ... (rest of config)

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
