from dataclasses import dataclass
from typing import Dict


@dataclass
class BudgetGoal:
    """Represents target allocations for different spending categories."""

    allocations: Dict[str, float]  # category -> percentage (0-100)

    def __post_init__(self):
        # Convert all values to float and validate percentages
        self.allocations = {k: float(v) for k, v in self.allocations.items()}

        total = sum(self.allocations.values())
        if total > 100:
            raise ValueError("Total allocation cannot exceed 100%")
        for category, percentage in self.allocations.items():
            if percentage < 0:
                raise ValueError(f"Allocation for {category} cannot be negative")
