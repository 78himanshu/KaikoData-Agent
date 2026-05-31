# KaikoData-Agent

An agentic market data downloader that converts natural-language trading data requests into Kaiko Market Data API downloads.

## Overview

KaikoData-Agent is a command-line AI agent designed for quantitative researchers and data engineers. The agent accepts natural-language requests such as asking for Bitcoin OHLCV data or Ethereum tick-level trade data, converts the request into structured API parameters, downloads the requested market data from Kaiko, and saves the results to the local filesystem.

The project extends a financial MCP/reference-data workflow into a practical data acquisition agent that can retrieve crypto market data through tool/function calling.

## What This Project Does

The agent:

1. Accepts a natural-language market data request
2. Identifies the requested asset, exchange, instrument, time range, interval, and data type
3. Chooses the correct Kaiko Market Data API endpoint
4. Downloads either OHLCV aggregation data or tick-level trade data
5. Saves the downloaded response as JSON
6. Converts the data into CSV for analysis
7. Prints the resolved request parameters and output file paths

## Supported Data Requests

The agent supports two Kaiko Market Data API endpoint families:

### OHLCV / Aggregated Trade Data

Used for interval-based market data such as:

```text
I want 1-minute interval trade data for Bitcoin spot rates for all of March 2026
```

### Tick-Level Trade Data

Used for raw trade/tick data such as:

```text
I want tick data for Ethereum spot rates for a 10-minute interval on March 19, 2026
```

## Features

- Agentic market data workflow
- OpenAI function calling
- Kaiko Market Data API integration
- Natural-language request parsing
- OHLCV data downloads
- Tick-level trade data downloads
- JSON and CSV output generation
- Filesystem-based data export
- CLI-first workflow for quant/data users
- Environment-based credential management

## Tech Stack

- Python
- OpenAI API
- Kaiko Market Data API
- Requests
- python-dotenv
- JSON
- CSV

## Project Structure

```text
KaikoData-Agent/
│
├── kaiko_data_agent.py
├── requirements.txt
├── pipeline_execution.png
├── README.md
└── .gitignore
```

Generated locally after running the agent:

```text
downloads/
├── ohlcv_cbse_btc-usd_2026-03-01t00_00_00_000z_2026-03-31t23_59_59_999z.json
└── ohlcv_cbse_btc-usd_2026-03-01t00_00_00_000z_2026-03-31t23_59_59_999z.csv
```

The `downloads/` folder is excluded from GitHub because it contains generated API outputs.

## Installation

Clone the repository:

```bash
git clone https://github.com/78himanshu/KaikoData-Agent.git
cd KaikoData-Agent
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file in the project root:

```text
OPENAI_API_KEY=your_openai_api_key_here
KAIKO_API_KEY=your_kaiko_api_key_here
```

The `.env` file is excluded from version control.

## Usage

Run the agent with a natural-language request:

```bash
python kaiko_data_agent.py "I want 1-minute interval trade data for Bitcoin spot rates for all of March 2026"
```

Example output:

```text
Download completed successfully.

Data type: ohlcv
Exchange: cbse
Instrument: btc-usd
Start time: 2026-03-01T00:00:00.000Z
End time: 2026-03-31T23:59:59.999Z
Interval: 1m
JSON file: downloads/ohlcv_cbse_btc-usd_2026-03-01t00_00_00_000z_2026-03-31t23_59_59_999z.json
CSV file: downloads/ohlcv_cbse_btc-usd_2026-03-01t00_00_00_000z_2026-03-31t23_59_59_999z.csv
```

## Agent Workflow

```text
Natural-Language Request
          │
          ▼
OpenAI Function-Calling Agent
          │
          ▼
Structured Market Data Parameters
          │
          ▼
Kaiko Market Data API
          │
          ▼
Downloaded JSON Response
          │
          ▼
CSV Conversion
          │
          ▼
Filesystem Output
```

## Why This Matters

Quantitative researchers and trading data engineers often need to retrieve specific market data slices quickly without manually constructing API URLs. KaikoData-Agent demonstrates how an AI agent can act as a natural-language interface to market data infrastructure.

This workflow is useful for:

- Quant research data acquisition
- Trading data discovery
- Market data engineering
- Natural-language API automation
- Agentic data workflows
- Crypto market analysis

## Future Improvements

- Add support for more Kaiko endpoints
- Add reference-data validation before download
- Add exchange and instrument disambiguation
- Add automatic pagination handling
- Add date range safeguards for large tick-data requests
- Add CLI flags for output format
- Add unit tests for request parsing and URL construction

## Author

Himanshu Paithane


