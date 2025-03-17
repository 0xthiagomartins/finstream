# FinStream

## Overview
FinStream is a simple and interactive personal finance dashboard built with Streamlit. It helps users manage their budget, set financial goals, track net worth, and visualize financial progress.

![image](./assets/budget_demo.png)
![image](./assets/first_million_demo.png)
![image](./assets/net_worth_demo.png)
![image](./assets/market_cap_of_demo.png)

## Features
- **Budget Tracker**: Log income and expenses, visualize spending trends.
- **Goals & First Million**: Set financial targets and estimate time to reach your first million.
- **Assets vs Liabilities**: Track net worth by managing assets and debts.

## Project Structure
```
finstream/
├── src/                    # Source code
│   ├── app.py             # Main Streamlit application
│   ├── models/            # Data models
│   ├── utils/             # Helper functions
│   └── config/            # Configuration files
├── tests/                 # Test files
│   ├── conftest.py
│   ├── test_models/
│   └── test_utils/
├── .streamlit/
│   └── config.toml
├── sprints/              # Sprint planning and documentation
│   ├── sprint1/
│   └── sprint2/
├── docs/                 # Documentation
├── requirements.txt      # Project dependencies
├── README.md
└── ROADMAP.md
```

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/0xthiagomartins/finstream.git
   cd finstream
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```bash
   streamlit run src/app.py
   ```

## Dependencies
- Python 3.x
- Streamlit
- Pandas
- Matplotlib / Plotly
