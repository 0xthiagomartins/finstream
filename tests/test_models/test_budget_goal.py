import pytest
from models.budget_goal import BudgetGoal


def test_valid_budget_goal():
    """Test creating a valid budget goal."""
    allocations = {
        "Investment": 30.0,
        "Travel": 10.0,
        "Education": 40.0,
    }

    goal = BudgetGoal(allocations)
    assert goal.allocations == allocations


def test_excessive_allocation():
    """Test that total allocation over 100% raises error."""
    with pytest.raises(ValueError, match="Total allocation cannot exceed 100%"):
        BudgetGoal(
            {
                "Investment": 50.0,
                "Travel": 30.0,
                "Education": 40.0,  # Total 120%
            }
        )


def test_negative_allocation():
    """Test that negative allocation raises error."""
    with pytest.raises(ValueError, match="Allocation for Travel cannot be negative"):
        BudgetGoal(
            {
                "Investment": 30.0,
                "Travel": -10.0,
                "Education": 40.0,
            }
        )
