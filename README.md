# Advanced Crypto Investigation Suite

## Table of Contents

- [Advanced Crypto Investigation Suite](#advanced-crypto-investigation-suite)
  - [Table of Contents](#table-of-contents)
  - [1. Overview](#1-overview)
  - [2. Features](#2-features)
  - [3. Directory Structure](#3-directory-structure)
  - [4. Requirements](#4-requirements)
  - [5. Installation](#5-installation)
  - [6. Usage](#6-usage)
    - [1) Interactive Streamlit App](#1-interactive-streamlit-app)
    - [How to use:](#how-to-use)
    - [2) Command-Line Tool](#2-command-line-tool)
      - [Example Commands](#example-commands)

---

## 1. Overview

This repository contains two complementary Python scripts designed to perform advanced blockchain transaction analysis:

- **`crypto_tracker_v7.py`**: A user-friendly **Streamlit** application that helps visualize Ethereum transactions, detect interactions with known mixers or exchanges, and produce risk metrics and interactive transaction flow graphs.
- **`crypto_tracker_v3.py`**: A command-line tool (CLI) supporting both **Bitcoin** and **Ethereum**. It builds a transaction graph by recursively analyzing inputs/outputs of each transaction to a specified depth and visualizes it using **pyvis**.

Both scripts enable you to:

- Fetch transaction data from public APIs (Etherscan for Ethereum, BlockCypher for Bitcoin).
- Identify suspicious addresses, mixers, or exchange interactions.
- Generate interactive network graphs to visualize the flow of funds.

---

## 2. Features

- **Streamlit Dashboard** for real-time web-based exploration:
  - Interactive charts (timeline, pie charts, etc.).
  - Automatic detection of mixer addresses and exchanges.
  - Integrated transaction flow graph with **pyvis**/**NetworkX**.

- **CLI Tool** for:
  - Recursive transaction exploration up to an adjustable depth.
  - Support for both Bitcoin and Ethereum.
  - Generated HTML-based interactive graph outputs.

- **Risk Analysis**:
  - Flags transactions with known mixer addresses (e.g., Tornado Cash, Blender.io, ChipMixer).
  - Monitors hot wallet addresses of major exchanges (Binance, Coinbase, Kraken, etc.).

---

## 3. Directory Structure

```plaintext
.
├── crypto_tracker_v7.py  # The Streamlit-based app
├── crypto_tracker_v3.py        # The CLI-based analyzer
├── requirements.txt                # Dependencies file (optional)
├── README.md                       # This README documentation
└── ...
```
---

## 4. Requirements

- **Python 3.7+** (recommended)
- **Python Packages** (exact versions may vary):
  - `streamlit`
  - `requests`
  - `pandas`
  - `plotly`
  - `networkx`
  - `pyvis`
  - `argparse` (usually comes with Python by default)
  - `importlib-resources` (for Python < 3.9 if used in the CLI)

**Example `pip` installation:**
```bash
pip install streamlit requests pandas plotly networkx pyvis
```
For Ethereum-specific functionality, you need a valid Etherscan API key.
For Bitcoin-specific functionality (in the CLI script), BlockCypher is used (no API key required for basic calls, but you may need an API token for higher-rate usage).

---

## 5. Installation

- **Clone the repository:**
  
```bash
git clone https://github.com/arknet-cyber/eth-crypto-tracker.git
cd eth-crypto-tracker
```

- **Install required Python packages**

```bash
pip install -r requirements.txt
```
 or individually:

```bash
pip install streamlit requests pandas plotly networkx pyvis
```
---
(Optional) Configure your environment variables or create a .env file if you want to store your Etherscan API key securely. The Streamlit app also allows you to input your API key directly in the sidebar.

---

## 6. Usage

Below are detailed instructions on how to run each script in this repository.

---

### 1) Interactive Streamlit App

**File:** `crypto_tracker_v7.py`

- **Purpose**: Analyze and visualize Ethereum addresses in a web-based dashboard.

- **How to run**:

```bash
  streamlit run crypto_tracker_v7.py
```

### How to use:

1. After running the command, a local URL will appear in your terminal (e.g., `http://localhost:8501`).
2. Open your browser and navigate to that URL.
3. Enter the Ethereum address and your Etherscan API key in the sidebar.
4. Click the **"Analyze Transactions"** button to generate:
   - **Transaction metrics and summaries**  
   - **Timeline and distribution charts**  
   - **An interactive transaction graph**
5. Explore flagged interactions with mixers or exchanges in the corresponding tables.

### 2) Command-Line Tool

**File:** `crypto_tracker_v3.py`

- **Purpose**: Perform a recursive analysis of addresses (Bitcoin or Ethereum) via CLI, build a transaction graph, and generate an **HTML** output for interactive visualization.

- **Basic Syntax**:

```bash
  python crypto_tracker_v3.py <address> --crypto <btc|eth> --depth <int> [--api-key <KEY>]
```

**Key Arguments**:

- `address`: The blockchain address you want to analyze.  
- `--crypto`: Choose between `btc` (default) or `eth`.  
- `--depth`: How many levels deep into the transaction history to recurse.  
- `--api-key`: Required only when `--crypto eth` (Etherscan key).

> **Note**: The script saves an HTML file named `transaction_graph.html` in the current directory.

#### Example Commands

1. **Analyze a BTC address with default depth of 2**:

```bash
   python crypto_tracker_v3.py 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
```

1. **Analyze an ETH address with depth 3 using an Etherscan API key**:

```bash
python crypto_tracker_v3.py 0x1234567890abcdef1234567890abcdef12345678 --crypto eth --depth 3 --api-key YOUR_KEY_HERE
```

The CLI will create a file named transaction_graph.html containing an interactive visualization of the transaction flow.