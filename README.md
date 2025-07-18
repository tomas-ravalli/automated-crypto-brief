# Coinbase Crypto Reporter

This project is a Python script that automatically fetches the price of a specified cryptocurrency from Coinbase, calculates its performance against a predefined purchase price, and sends a daily report via email. The project is designed to be easily configurable and can be automated to run daily using GitHub Actions.

---

## Features

* Fetches the latest cryptocurrency prices from Coinbase.
* Calculates the performance and profit/loss of your investment.
* Sends a formatted email report.
* Can be automated to run on a schedule using GitHub Actions.
* Securely handles API keys and other sensitive information using environment variables.

---

## Prerequisites

Before you begin, ensure you have the following:

* Python 3.6 or higher
* A Coinbase account with API credentials (API Key and API Secret)
* A Gmail account with an App Password
* Git (for cloning the repository)

---

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/tomas-ravalli/coinbase-report.git](https://github.com/tomas-ravalli/coinbase-report.git)
    cd coinbase-report
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage

To use this script, you need to configure your environment variables.

1.  **Create a `.env` file** in the root directory of the project.

2.  **Add the following environment variables** to the `.env` file with your own credentials:
    ```
    COINBASE_API_KEY="YOUR_COINBASE_API_KEY"
    COINBASE_API_SECRET="YOUR_COINBASE_API_SECRET"
    GMAIL_ADDRESS="YOUR_GMAIL_ADDRESS"
    GMAIL_APP_PASSWORD="YOUR_GMAIL_APP_PASSWORD"
    RECIPIENT_EMAIL="THE_EMAIL_ADDRESS_TO_SEND_THE_REPORT_TO"
    ```

3.  **Run the script manually:**
    ```bash
    python report.py
    ```

---

## Automation with GitHub Actions

This repository includes a GitHub Actions workflow to automate the daily execution of the report. To use it, you need to set up secrets in your forked GitHub repository.

1.  **Fork this repository.**

2.  **Go to your repository's settings** > **Secrets and variables** > **Actions**.

3.  **Create the following secrets** with your credentials:
    * `COINBASE_API_KEY`
    * `COINBASE_API_SECRET`
    * `GMAIL_ADDRESS`
    * `GMAIL_APP_PASSWORD`
    * `RECIPIENT_EMAIL`

The workflow is configured to run at 06:00 UTC daily. You can also trigger it manually from the Actions tab in your repository.

---

## Customization

You can customize the script to track a different cryptocurrency or a different purchase price.

1.  **Open the `report.py` file.**

2.  **Change the `CURRENCY_PAIR`** to the desired currency pair (e.g., 'BTC-USD').
    ```python
    CURRENCY_PAIR = 'YOUR-CRYPTO-PAIR'
    ```

3.  **Update the `PURCHASE_PRICE`** to your purchase price.
    ```python
    PURCHASE_PRICE = YOUR_PURCHASE_PRICE
    ```

---

## License

This project is licensed under the MIT License.