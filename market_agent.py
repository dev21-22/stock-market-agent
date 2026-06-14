import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import pytz

# Config
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "2211dax@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "dakshp1104@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD") # App Password from environment variable

INDICES = {
    "NIFTY 50": "NIFTY_50:INDEXNSE",
    "BSE SENSEX": "SENSEX:INDEXBOM"
}

def fetch_index_data(ticker_symbol):
    try:
        url = f'https://www.google.com/finance/quote/{ticker_symbol}'
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        
        price_div = soup.find('div', {'class': 'YMlKec fxKbKc'})
        change_point = soup.find('div', {'class': 'P6K39c'}) # Previous close
        
        if not price_div or not change_point:
            return None
            
        latest_close = float(price_div.text.replace(',', ''))
        prev_close = float(change_point.text.replace(',', ''))
        
        change = latest_close - prev_close
        pct_change = (change / prev_close) * 100
        
        return {
            "close": round(latest_close, 2),
            "change": round(change, 2),
            "pct_change": round(pct_change, 2)
        }
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None

def generate_html_report(data_dict, date_str):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            h2 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 600px; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .positive {{ color: green; font-weight: bold; }}
            .negative {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>Indian Stock Market Daily Update</h2>
        <p><strong>Date:</strong> {date_str}</p>
        <p>Here is your factual, data-driven update on the major indices for today:</p>
        
        <table>
            <tr>
                <th>Index</th>
                <th>Close</th>
                <th>Points Change</th>
                <th>% Change</th>
            </tr>
    """
    
    for name, data in data_dict.items():
        if data is None:
            html += f"<tr><td>{name}</td><td colspan='3'>Data unavailable</td></tr>"
            continue
            
        color_class = "positive" if data['change'] >= 0 else "negative"
        sign = "+" if data['change'] >= 0 else ""
        
        html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td>{data['close']:,.2f}</td>
                <td class="{color_class}">{sign}{data['change']:.2f}</td>
                <td class="{color_class}">{sign}{data['pct_change']:.2f}%</td>
            </tr>
        """
        
    html += """
        </table>
        <p style="font-size: 0.9em; color: #666;">This is an automated factual report. Data is sourced from Google Finance.</p>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    if not SENDER_PASSWORD:
        print("Error: SENDER_PASSWORD environment variable not set. Cannot send email.")
        return False
        
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.close()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def main():
    ist_tz = pytz.timezone('Asia/Kolkata')
    today_ist = datetime.now(ist_tz).strftime('%Y-%m-%d')
    
    print(f"Fetching data for {today_ist}...")
    market_data = {}
    for name, symbol in INDICES.items():
        market_data[name] = fetch_index_data(symbol)
        
    print("Generating report...")
    html_report = generate_html_report(market_data, today_ist)
    
    subject = f"Stock Market Update - {today_ist}"
    
    print("Sending email...")
    send_email(subject, html_report)

if __name__ == "__main__":
    main()
