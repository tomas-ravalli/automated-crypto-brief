import os
import smtplib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.utils import make_msgid
from coinbase.wallet.client import Client
from dotenv import load_dotenv
from datetime import date
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
SENDER_EMAIL = os.getenv("GMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
CURRENCY_PAIR = 'XRP-EUR'
PURCHASE_PRICES_STR = os.getenv("PURCHASE_PRICES")
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def get_xrp_price():
    """Fetches the current XRP-EUR spot price from Coinbase."""
    try:
        client = Client(COINBASE_API_KEY, COINBASE_API_SECRET)
        price_data = client.get_spot_price(currency_pair=CURRENCY_PAIR)
        return float(price_data.amount)
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def calculate_average_purchase_price(prices_str):
    """Calculates the simple average of purchase prices."""
    if not prices_str:
        return None
    try:
        prices = [float(p) for p in prices_str.strip().split(';') if p]
        return sum(prices) / len(prices) if prices else None
    except (ValueError, Exception) as e:
        print(f"Error processing prices: {e}")
        return None

def get_news_summary(api_key, crypto_name):
    """Fetches a news summary for a given crypto using the Gemini API."""
    if not api_key:
        print("Gemini API key not found. Skipping news summary.")
        return "News summary feature is not configured."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"In one short paragraph, what is the most relevant news or milestone for {crypto_name} in the last 72 hours? Be concise."
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error fetching news from Gemini: {e}")
        return "News summary could not be retrieved at this time."

def update_data_and_create_chart(today_str, return_pct):
    """
    Updates the historical data CSV and generates the performance chart.
    Returns the file path of the generated chart.
    """
    csv_file = 'data/historical_data.csv'
    
    new_data = pd.DataFrame([{
        'date': pd.to_datetime(today_str, dayfirst=True),
        'return_pct': round(return_pct, 2)
    }])
    
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file, parse_dates=['date'])
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
    
    df.to_csv(csv_file, index=False)
    
    weekly_avg_return = df.set_index('date')['return_pct'].resample('W-SUN').mean().round(2)
    
    if len(weekly_avg_return) < 2:
        print("Not enough data to generate a meaningful chart. Skipping chart generation.")
        return None
        
    plt.style.use('default')
    plt.rcParams['font.family'] = 'monospace'
    fig, ax = plt.subplots(figsize=(4.24, 2.25))
    ax.plot(weekly_avg_return.index, weekly_avg_return, marker='o', linestyle='-', color='grey', markersize=3, linewidth=1, label='Weekly Avg. Return')
    
    valid_points = weekly_avg_return.dropna()
    if len(valid_points) > 2:
        x_vals = mdates.date2num(valid_points.index)
        m, b = np.polyfit(x_vals, valid_points, 1)
        ax.plot(weekly_avg_return.index, m * mdates.date2num(weekly_avg_return.index) + b, '--', color='#ff9999', linewidth=1, label='Trend')

    ax.set_title('Weekly Average Return (%)', fontsize=9)
    ax.set_ylabel('Avg. Return', fontsize=8)
    ax.tick_params(axis='y', labelsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.SU))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.tick_params(axis='x', labelsize=8, rotation=45)
    ax.axhline(0, color='grey', linewidth=0.6)
    
    y_min, y_max = weekly_avg_return.min(), weekly_avg_return.max()
    y_range = y_max - y_min if y_max > y_min else 1
    y_buffer = y_range * 0.1
    ax.set_ylim([y_min - y_buffer, y_max + y_buffer])

    if not valid_points.empty:
        x_min_date = valid_points.index.min()
        x_max_date = valid_points.index.max()
        ax.set_xlim(x_min_date - pd.Timedelta(days=3), x_max_date + pd.Timedelta(days=3))
    
    ax.legend(fontsize=8)
    chart_path = 'reports/weekly_report_chart.png'
    plt.savefig(chart_path, bbox_inches='tight', pad_inches=0.1, dpi=200)
    plt.close()
    
    return chart_path

def send_email(current_price, avg_purchase_price, chart_path, news_summary):
    """Sends an email with the price report, news, and embedded chart."""
    if current_price is None or avg_purchase_price is None:
        return

    # --- Calculations ---
    return_pct = ((current_price - avg_purchase_price) / avg_purchase_price) * 100 if avg_purchase_price else 0
    profit_per_unit = current_price - avg_purchase_price
    return_multiplier = current_price / avg_purchase_price if avg_purchase_price else 0

    today_str = date.today().strftime("%d/%m/%Y")
    
    msg = EmailMessage()
    msg['Subject'] = f'Daily {CURRENCY_PAIR} Report: {today_str}'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    # --- Define Email Body Components ---
    # Plain text versions
    body_top_metrics = f"Return: {return_pct:+.2f}%\nReturn Multiplier: x{return_multiplier:.2f}"
    body_bottom_metrics = f"Current Price: €{current_price:,.2f}\nAvg. Purchase Price: €{avg_purchase_price:,.2f}\nProfit/Loss per Unit: €{profit_per_unit:,.2f}"
    body_news_plain = f"Latest News:\n{news_summary}"
    body_signature = f"(Report generated by bot)\n🌐 © 2025 t.r."

    # HTML-specific version for the top metrics
    body_top_metrics_html = f"<b>Return:</b> {return_pct:+.2f}%\n<b>Return Multiplier:</b> x{return_multiplier:.2f}"
    
    # --- Set Plain Text Content ---
    # This provides a fallback for email clients that don't render HTML.
    msg.set_content(f"{body_top_metrics}\n\n[Chart]\n\n{body_bottom_metrics}\n\n{body_news_plain}\n\n\n{body_signature}")

    # --- Set HTML Content ---
    if chart_path:
        image_cid = make_msgid(domain='t-ravalli-report')[1:-1]
    
        html_body = f"""
        <html><body>
            <pre style="font-family: sans-serif; margin: 0;">{body_top_metrics_html}</pre>
            <img src="cid:{image_cid}" width="400" style="display:block; max-width:400px; width:100%; height:auto; margin-top:15px; margin-bottom:15px;">
            <pre style="font-family: sans-serif; margin: 0;">{body_bottom_metrics}</pre>
            <p style="font-family: sans-serif; margin-top: 15px; margin-bottom: 5px;"><b>Latest News:</b></p>
            <p style="font-family: sans-serif; margin-top: 0;">{news_summary}</p>
            <br>
            <pre style="font-family: monospace; margin: 0;">{body_signature}</pre>
        </body></html>"""
        msg.add_alternative(html_body, subtype='html')
        
        # Embed the image
        with open(chart_path, 'rb') as f:
            img_data = f.read()
        img = MIMEImage(img_data)
        img.add_header('Content-ID', f'<{image_cid}>')
        img.add_header('Content-Disposition', 'inline', filename='return_chart.png')
        msg.attach(img)
    
    # --- Send Email ---
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    avg_price = calculate_average_purchase_price(PURCHASE_PRICES_STR)
    if avg_price is not None:
        current_price = get_xrp_price()
        if current_price is not None:
            return_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price != 0 else 0
            today_str = date.today().strftime("%d/%m/%Y")
            
            crypto_name = CURRENCY_PAIR.split('-')[0]
            news_summary = get_news_summary(GEMINI_API_KEY, crypto_name)
            
            chart_path = update_data_and_create_chart(today_str, return_pct)
            
            send_email(current_price, avg_price, chart_path, news_summary)