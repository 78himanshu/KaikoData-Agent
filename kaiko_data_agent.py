"""
Kaiko Market Data Download Agent

This script uses an OpenAI function-calling style agent to understand
natural-language requests and download Kaiko market data to the filesystem.

Supported data types:
1. Tick-level trade data using /trades
2. OHLCV summary data using /aggregations/ohlcv

Python version used during development:
Python 3.13.2
"""

import argparse
import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI


# -----------------------------
# Basic setup
# -----------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KAIKO_API_KEY = os.getenv("KAIKO_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file")

if not KAIKO_API_KEY:
    raise ValueError("Missing KAIKO_API_KEY in .env file")

client = OpenAI(api_key=OPENAI_API_KEY)

OUTPUT_DIR = Path("downloads")
OUTPUT_DIR.mkdir(exist_ok=True)

KAIKO_BASE_URL = "https://us.market-api.kaiko.io/v1"


# -----------------------------
# Helper functions
# -----------------------------

def normalize_asset(asset):
    """
    Converts common asset names into Kaiko instrument symbols.
    """
    asset = asset.lower().strip()

    asset_map = {
        "bitcoin": "btc",
        "btc": "btc",
        "ethereum": "eth",
        "ether": "eth",
        "eth": "eth",
    }

    if asset not in asset_map:
        raise ValueError(f"Unsupported asset: {asset}. Use Bitcoin/BTC or Ethereum/ETH.")

    return asset_map[asset]


def normalize_exchange(exchange):
    """
    Converts common exchange names into Kaiko exchange codes.
    Coinbase is cbse in Kaiko's examples.
    """
    exchange = exchange.lower().strip()

    exchange_map = {
        "coinbase": "cbse",
        "coinbase exchange": "cbse",
        "cbse": "cbse",
    }

    if exchange not in exchange_map:
        raise ValueError(f"Unsupported exchange: {exchange}. This homework example supports Coinbase/cbse.")

    return exchange_map[exchange]


def make_instrument(base_asset, quote_asset="usd"):
    """
    Creates Kaiko instrument format like btc-usd or eth-usd.
    """
    base = normalize_asset(base_asset)
    quote = quote_asset.lower().strip()

    if quote in ["dollar", "dollars", "usd"]:
        quote = "usd"

    return f"{base}-{quote}"


def safe_filename(text):
    """
    Makes a safe filename from request details.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9_-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def save_json_and_csv(data, base_filename):
    """
    Saves API response data as JSON and CSV.

    JSON stores the full response.
    CSV stores the list inside the 'data' key if it exists.
    """
    json_path = OUTPUT_DIR / f"{base_filename}.json"
    csv_path = OUTPUT_DIR / f"{base_filename}.csv"

    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2)

    rows = data.get("data", [])

    if rows and isinstance(rows, list) and isinstance(rows[0], dict):
        fieldnames = sorted(rows[0].keys())

        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path = None

    return json_path, csv_path


def request_kaiko_data(url, params):
    """
    Sends request to Kaiko API and returns JSON response.
    """
    headers = {
        "X-Api-Key": KAIKO_API_KEY,
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, params=params, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Kaiko API request failed.\n"
            f"Status code: {response.status_code}\n"
            f"Response: {response.text}\n"
            f"URL: {response.url}"
        )

    return response.json()


def download_kaiko_data(
    data_type,
    asset,
    quote_asset,
    exchange,
    start_time,
    end_time,
    interval=None
):
    """
    Main tool function called by the agent.

    data_type:
        - trades
        - ohlcv
    """

    exchange_code = normalize_exchange(exchange)
    instrument = make_instrument(asset, quote_asset)

    data_type = data_type.lower().strip()

    if data_type not in ["trades", "ohlcv"]:
        raise ValueError("data_type must be either 'trades' or 'ohlcv'.")

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "page_size": 10000
    }

    if data_type == "ohlcv":
        if not interval:
            raise ValueError("OHLCV requests require an interval like 1m, 5m, 1h, or 1d.")

        params["interval"] = interval

        url = (
            f"{KAIKO_BASE_URL}/data/trades.latest/exchanges/"
            f"{exchange_code}/spot/{instrument}/aggregations/ohlcv"
        )

    else:
        url = (
            f"{KAIKO_BASE_URL}/data/trades.latest/exchanges/"
            f"{exchange_code}/spot/{instrument}/trades"
        )

    data = request_kaiko_data(url, params)

    filename_base = safe_filename(
        f"{data_type}_{exchange_code}_{instrument}_{start_time}_{end_time}"
    )

    json_path, csv_path = save_json_and_csv(data, filename_base)

    result = {
        "message": "Download completed successfully.",
        "data_type": data_type,
        "exchange": exchange_code,
        "instrument": instrument,
        "start_time": start_time,
        "end_time": end_time,
        "interval": interval,
        "json_file": str(json_path),
        "csv_file": str(csv_path) if csv_path else "No CSV created because no tabular data was returned."
    }

    return result


# -----------------------------
# OpenAI agent logic
# -----------------------------

tools = [
    {
        "type": "function",
        "name": "download_kaiko_data",
        "description": "Download Kaiko crypto market data to the filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "data_type": {
                    "type": "string",
                    "enum": ["trades", "ohlcv"],
                    "description": "Use trades for tick-level trade data. Use ohlcv for summary/candlestick data."
                },
                "asset": {
                    "type": "string",
                    "description": "The crypto asset, such as Bitcoin, BTC, Ethereum, or ETH."
                },
                "quote_asset": {
                    "type": "string",
                    "description": "Quote currency, usually USD."
                },
                "exchange": {
                    "type": "string",
                    "description": "Exchange name or code, such as Coinbase or cbse."
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time in ISO 8601 UTC format, such as 2026-03-01T00:00:00.000Z."
                },
                "end_time": {
                    "type": "string",
                    "description": "End time in ISO 8601 UTC format, such as 2026-03-31T23:59:59.999Z."
                },
                "interval": {
                    "type": ["string", "null"],
                    "description": "Required only for OHLCV data, such as 1m, 5m, 1h, or 1d. Use null for trades."
                }
            },
            "required": [
                "data_type",
                "asset",
                "quote_asset",
                "exchange",
                "start_time",
                "end_time",
                "interval"
            ],
            "additionalProperties": False
        }
    }
]


def answer_question(user_question):
    """
    Sends the user request to the model.
    The model decides the correct function arguments.
    Then the script runs the download function.
    """

    system_message = """
You are a Kaiko Market Data download assistant.

Your job:
- Convert the user's natural-language request into a call to download_kaiko_data.
- Only support Coinbase spot BTC-USD and ETH-USD for this homework.
- Use exchange 'Coinbase' if the user does not specify an exchange.
- Use quote_asset 'usd' if the user asks for spot rates or does not specify quote currency.
- Use data_type 'ohlcv' for requests asking for interval data, candle data, OHLCV, summary data, or aggregated data.
- Use data_type 'trades' for requests asking for tick data, trade data, or every trade.
- For OHLCV requests, infer interval from phrases like '1-minute interval' as '1m'.
- For trade/tick data, interval must be null.
- Convert all dates and times to ISO 8601 UTC format with milliseconds and Z.

Important safety rule:
- Tick-level trade requests must never exceed 10 minutes.
- If the user requests more than 10 minutes of tick data, do not call the tool. Explain that tick data is limited to 10 minutes.
- OHLCV requests can cover longer date ranges.

Examples:
User: I want 1-minute interval trade data for Bitcoin spot rates for all of March 2026
Tool call:
data_type='ohlcv'
asset='Bitcoin'
quote_asset='usd'
exchange='Coinbase'
start_time='2026-03-01T00:00:00.000Z'
end_time='2026-03-31T23:59:59.999Z'
interval='1m'

User: I want tick data for Ethereum spot rates for March 19, 2026 from 2:00 PM UTC to 2:09:59 PM UTC
Tool call:
data_type='trades'
asset='Ethereum'
quote_asset='usd'
exchange='Coinbase'
start_time='2026-03-19T14:00:00.000Z'
end_time='2026-03-19T14:09:59.999Z'
interval=null
"""

    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        tools=tools
    )

    function_call = None

    for item in response.output:
        if item.type == "function_call":
            function_call = item
            break

    if function_call is None:
        return response.output_text

    arguments = json.loads(function_call.arguments)

    result = download_kaiko_data(**arguments)

    final_answer = (
        "Download completed successfully.\n\n"
        f"Data type: {result['data_type']}\n"
        f"Exchange: {result['exchange']}\n"
        f"Instrument: {result['instrument']}\n"
        f"Start time: {result['start_time']}\n"
        f"End time: {result['end_time']}\n"
        f"Interval: {result['interval']}\n"
        f"JSON file: {result['json_file']}\n"
        f"CSV file: {result['csv_file']}"
    )

    return final_answer


# -----------------------------
# Command-line entry point
# -----------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Download Kaiko market data from a natural-language request."
    )

    parser.add_argument(
        "question",
        type=str,
        help="Natural-language data request."
    )

    args = parser.parse_args()

    answer = answer_question(args.question)
    print(answer)


if __name__ == "__main__":
    main()