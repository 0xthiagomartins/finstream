import streamlit as st
import pandas as pd
from typing import Dict


def render_asset_liability_card(
    category: str,
    items: Dict[str, float],
    on_update: callable,
    on_add: callable,
    is_asset: bool = True,
):
    """Render an asset/liability card for a specific category."""
    with st.container(border=True):
        # Card header with category and total amount
        total_amount = sum(items.values())

        header_col1, header_col2 = st.columns([2, 1])
        with header_col1:
            st.subheader(category)
        with header_col2:
            st.subheader(f"${total_amount:,.2f}")

        # Items table with enhanced styling
        if items:
            df = pd.DataFrame(
                [{"Item": name, "Amount": amount} for name, amount in items.items()]
            )
            edited_df = st.data_editor(
                df,
                column_config={
                    "Amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f",
                        required=True,
                        min_value=0,
                    ),
                    "Item": st.column_config.TextColumn(
                        "Item",
                        required=True,
                    ),
                },
                hide_index=True,
                num_rows="dynamic",
                key=f"{category}_{'asset' if is_asset else 'liability'}_table",
                on_change=lambda: on_update(category, edited_df),
            )
