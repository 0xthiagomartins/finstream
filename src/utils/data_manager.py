import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, List
import streamlit as st
from datetime import datetime
import json
from models.budget_goal import BudgetGoal

DATA_DIR = Path("data")
ASSETS_FILE = DATA_DIR / "assets.csv"
LIABILITIES_FILE = DATA_DIR / "liabilities.csv"
BUDGET_GOALS_FILE = DATA_DIR / "budget_goals.csv"
EXPENSES_FILE = DATA_DIR / "expenses.csv"
FIRST_MILLION_FILE = DATA_DIR / "first_million.csv"


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def save_to_csv(data: Dict[str, Dict[str, float]], is_asset: bool = True):
    """Save assets or liabilities to CSV."""
    ensure_data_dir()
    file_path = ASSETS_FILE if is_asset else LIABILITIES_FILE

    rows = []
    for category, items in data.items():
        for item, amount in items.items():
            rows.append({"Category": category, "Item": item, "Amount": amount})

    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False)


def save_budget_goals(goals: Dict):
    """Save budget goals to CSV."""
    ensure_data_dir()

    # Convert BudgetGoal object to dictionary
    if hasattr(goals, "allocations"):
        goals_dict = goals.allocations
    else:
        goals_dict = goals

    # Create DataFrame with allocations
    rows = []
    for category, percentage in goals_dict.items():
        rows.append({"Category": category, "Percentage": percentage})

    df = pd.DataFrame(rows)
    df.to_csv(BUDGET_GOALS_FILE, index=False)


def save_expenses(expenses: Dict[str, Dict[str, float]]):
    """Save expenses to CSV."""
    ensure_data_dir()

    # Convert nested dict to DataFrame with consistent column names
    rows = []
    for category, items in expenses.items():
        for description, amount in items.items():
            rows.append(
                {"Category": category, "Description": description, "Amount": amount}
            )

    df = pd.DataFrame(rows)

    # Ensure we have all required columns
    if not df.empty:
        required_columns = ["Category", "Description", "Amount"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

    df.to_csv(EXPENSES_FILE, index=False)


def save_first_million_config(config: Dict):
    """Save first million configuration to CSV."""
    ensure_data_dir()
    df = pd.DataFrame([config])
    df.to_csv(FIRST_MILLION_FILE, index=False)


def load_from_csv(is_asset: bool = True) -> Dict[str, Dict[str, float]]:
    """Load assets or liabilities from CSV."""
    file_path = ASSETS_FILE if is_asset else LIABILITIES_FILE

    if not file_path.exists():
        return {}

    try:
        df = pd.read_csv(file_path)

        result = {}
        for _, row in df.iterrows():
            category = row["Category"]
            if category not in result:
                result[category] = {}
            result[category][row["Item"]] = row["Amount"]

        return result
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return {}


def load_budget_goals() -> Dict:
    """Load budget goals from CSV."""
    if not BUDGET_GOALS_FILE.exists():
        return {}

    try:
        df = pd.read_csv(BUDGET_GOALS_FILE)
        if df.empty:
            return {}

        # Convert DataFrame back to allocations dictionary
        allocations = {row["Category"]: row["Percentage"] for _, row in df.iterrows()}

        # Create and return BudgetGoal object
        try:
            return BudgetGoal(allocations)
        except ValueError:
            return None

    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return {}


def load_expenses() -> Dict[str, Dict[str, float]]:
    """Load expenses from CSV."""
    if not EXPENSES_FILE.exists():
        return {}

    try:
        df = pd.read_csv(EXPENSES_FILE)

        # Convert DataFrame back to nested dict
        result = {}

        # Check if we have the new format (Category, Description, Amount)
        if (
            "Category" in df.columns
            and "Description" in df.columns
            and "Amount" in df.columns
        ):
            for _, row in df.iterrows():
                category = row["Category"]
                if category not in result:
                    result[category] = {}
                result[category][row["Description"]] = row["Amount"]

        # Check if we have the old format (category, description, amount)
        elif (
            "category" in df.columns
            and "description" in df.columns
            and "amount" in df.columns
        ):
            for _, row in df.iterrows():
                category = row["category"]
                if category not in result:
                    result[category] = {}
                result[category][row["description"]] = row["amount"]

        return result
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return {}


def load_first_million_config() -> Dict:
    """Load first million configuration from CSV."""
    if not FIRST_MILLION_FILE.exists():
        return {}

    try:
        df = pd.read_csv(FIRST_MILLION_FILE)
        return df.iloc[0].to_dict() if not df.empty else {}
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return {}


def save_current_state():
    """Save all current session state to CSV files."""
    # Net Worth data
    if "assets" in st.session_state:
        save_to_csv(st.session_state.assets, True)
    if "liabilities" in st.session_state:
        save_to_csv(st.session_state.liabilities, False)

    # Budget data
    if "budget_goals" in st.session_state:
        save_budget_goals(st.session_state.budget_goals)
    if "expenses" in st.session_state:
        save_expenses(st.session_state.expenses)

    # First Million data
    if "first_million_config" in st.session_state:
        save_first_million_config(st.session_state.first_million_config)


def load_saved_state():
    """Load all saved state from CSV files."""
    # Net Worth data
    st.session_state.assets = load_from_csv(True)
    st.session_state.liabilities = load_from_csv(False)

    # Budget data
    st.session_state.budget_goals = load_budget_goals()
    st.session_state.expenses = load_expenses()

    # First Million data
    st.session_state.first_million_config = load_first_million_config()


def save_budget_state(
    budget_goals: Dict[str, float],
    expenses: Dict[str, Dict[str, float]],
    monthly_salary: float,
):
    """Save budget-related state (goals and expenses together)."""
    ensure_data_dir()

    # Save budget goals
    if budget_goals:
        rows = []
        for category, percentage in budget_goals.items():
            rows.append({"Category": category, "Percentage": percentage})
        df = pd.DataFrame(rows)
        df.to_csv(BUDGET_GOALS_FILE, index=False)

    # Save expenses
    if expenses:
        rows = []
        for category, items in expenses.items():
            for description, amount in items.items():
                rows.append(
                    {"Category": category, "Description": description, "Amount": amount}
                )
        df = pd.DataFrame(rows)
        df.to_csv(EXPENSES_FILE, index=False)

    # Save monthly salary along with budget goals
    with open(DATA_DIR / "budget_config.json", "w") as f:
        json.dump({"monthly_salary": monthly_salary}, f)


def load_budget_state():
    """Load complete budget state (goals and expenses)."""
    try:
        # Load budget goals
        goals = None
        if BUDGET_GOALS_FILE.exists():
            df = pd.read_csv(BUDGET_GOALS_FILE)
            if not df.empty:
                allocations = {
                    row["Category"]: row["Percentage"] for _, row in df.iterrows()
                }
                try:
                    goals = BudgetGoal(allocations)
                except ValueError as e:
                    st.error(f"Error loading budget goals: {str(e)}")
                    goals = None

        # Load expenses
        expenses = load_expenses()

        # Load monthly salary
        monthly_salary = 0.0
        config_file = DATA_DIR / "budget_config.json"
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                monthly_salary = config.get("monthly_salary", 0.0)

        # Update session state
        st.session_state.budget_goal = goals
        st.session_state.budget_goals = goals.allocations if goals else {}
        st.session_state.expenses = expenses
        st.session_state.monthly_salary = monthly_salary

    except Exception as e:
        st.error(f"Error loading budget state: {str(e)}")
