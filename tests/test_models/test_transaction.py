import pytest
from datetime import datetime
from models.transaction import Transaction, TransactionType


def test_transaction_creation():
    """Test basic transaction creation."""
    transaction = Transaction(
        amount=100.0,
        type=TransactionType.INCOME,
        category="Salary",
        description="Monthly salary",
    )

    assert transaction.amount == 100.0
    assert transaction.type == TransactionType.INCOME
    assert transaction.category == "Salary"
    assert transaction.description == "Monthly salary"
    assert isinstance(transaction.date, datetime)


def test_negative_amount_raises_error():
    """Test that negative amounts raise ValueError."""
    with pytest.raises(ValueError, match="Amount must be positive"):
        Transaction(
            amount=-100.0,
            type=TransactionType.EXPENSE,
            category="Food",
            description="Groceries",
        )


def test_transaction_without_description():
    """Test transaction creation without optional description."""
    transaction = Transaction(
        amount=50.0, type=TransactionType.EXPENSE, category="Food", description=None
    )

    assert transaction.amount == 50.0
    assert transaction.description is None
