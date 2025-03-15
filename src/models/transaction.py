from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass
class Transaction:
    amount: float
    type: TransactionType
    category: str
    description: Optional[str]
    date: datetime = datetime.now()

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount must be positive")
