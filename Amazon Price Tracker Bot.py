import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import schedule
import time
import smtplib
from email.mime.text import MIMEText

URL = "https://www.amazon.co.uk/dp/B0D33HYLMD"

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# CSV File for Price Tracking
FILE_NAME = "file_name.csv" # Specify you file name

# Email Configuration
EMAIL = "your.emailh@gmail.com"
PASSWORD = "you_password"  # Use an App Password, NOT your regular Gmail password
TARGET_PRICE = 600.00  # Target price for email alerts


def get_price():
    """Scrape the price from Amazon product page."""
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    price = soup.find("span", class_="a-offscreen")  # Amazon uses 'a-offscreen' for price
    if price:
        price_text = price.get_text().strip()

        # Remove currency symbols and commas
        price_text = price_text.replace("£", "").replace("$", "").replace(",", "")

        try:
            return float(price_text)
        except ValueError:
            print(f"Error: Unable to convert '{price_text}' to float")
            return None

    return None


def save_price(price):
    """Save the price to CSV file."""
    if price is None:
        return

    # Create DataFrame
    df = pd.DataFrame([[datetime.now(), price]], columns=["Date", "Price"])

    # Save to CSV (append if file exists)
    if os.path.exists(FILE_NAME):
        df.to_csv(FILE_NAME, mode='a', header=False, index=False)
    else:
        df.to_csv(FILE_NAME, index=False)


def plot_prices():
    """Plot the price trend from CSV data."""
    if not os.path.exists(FILE_NAME):
        print("No data available.")
        return

    df = pd.read_csv(FILE_NAME)
    df["Date"] = pd.to_datetime(df["Date"])

    plt.figure(figsize=(10, 5))
    plt.plot(df["Date"], df["Price"], marker='o', linestyle='-')
    plt.xlabel("Date")
    plt.ylabel("Price (GBP)")
    plt.title("Amazon Product Price Trend")
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()


def send_email(price):
    """Send an email alert if the price drops below target."""
    msg = MIMEText(f"Price Alert! The product price dropped to £{price}\nCheck it here: {URL}")
    msg["Subject"] = "Amazon Price Drop Alert"
    msg["From"] = EMAIL
    msg["To"] = EMAIL  # Send email to yourself

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, EMAIL, msg.as_string())
        print(f"✅ Email sent: Price dropped to £{price}!")
    except Exception as e:
        print(f"❌ Email failed: {e}")


def check_price():
    """Check the price, save it, and send email if price drops below target."""
    price = get_price()
    if price is None:
        print("❌ Failed to get price.")
        return

    save_price(price)
    print(f"✅ Checked price: £{price}")

    if price <= TARGET_PRICE:
        send_email(price)


# Run price check every 24 hours
schedule.every(24).hours.do(check_price)

# Run once at script start
check_price()

# Plot prices immediately after checking the price
plot_prices()  # This ensures the chart appears before the loop starts

# Keep running the script every 24 hours
try:
    while True:
        print("⏳ Waiting for the next scheduled price check...")
        schedule.run_pending()
        time.sleep(60)  # Check every 1 minute
except KeyboardInterrupt:
    print("\nScript stopped by user. Exiting gracefully...")

