import streamlit as st
import pandas as pd
from scipy.optimize import newton, brentq


# --- Standard IRR Logic ---
@st.cache_data
def calculate_irr(cash_flows):
    """Calculates the periodic Internal Rate of Return (IRR)."""

    def npv(rate):
        if rate <= -0.9999:
            return float('inf')
        return sum(amount / ((1.0 + rate) ** t) for t, amount in enumerate(cash_flows))

    guesses = [0.01, 0.05, 0.1, 0.2, 0.001, 0.5]
    for guess in guesses:
        try:
            rate = newton(npv, guess, tol=1e-7, maxiter=1000)
            if abs(npv(rate)) < 1e-4:
                return rate
        except (RuntimeError, OverflowError, ValueError):
            continue

    try:
        return brentq(npv, -0.9999, 100.0, xtol=1e-7)
    except ValueError:
        pass

    return None


# --- Session State & Formatting Callbacks ---
if "asset_input" not in st.session_state:
    st.session_state.asset_input = "0"
if "loan_input" not in st.session_state:
    st.session_state.loan_input = "0"
if "doc_input" not in st.session_state:
    st.session_state.doc_input = "0"


def format_asset():
    raw_val = st.session_state.asset_input.replace(',', '')
    try:
        st.session_state.asset_input = f"{float(raw_val):,.0f}"
    except ValueError:
        st.session_state.asset_input = "0"


def format_loan():
    raw_val = st.session_state.loan_input.replace(',', '')
    try:
        st.session_state.loan_input = f"{float(raw_val):,.0f}"
    except ValueError:
        st.session_state.loan_input = "0"


def format_doc():
    raw_val = st.session_state.doc_input.replace(',', '')
    try:
        st.session_state.doc_input = f"{float(raw_val):,.0f}"
    except ValueError:
        st.session_state.doc_input = "0"


# --- UI Layout Setup ---
st.set_page_config(page_title="IRR Calculator", layout="wide")

# --- Custom CSS for Input Boxes ---
st.markdown(
    """
    <style>
    /* Force text inside input boxes to be white */
    div[data-baseweb="input"] input {
        color: white !important;
        -webkit-text-fill-color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header with Title (Left) and Logo (Right) ---
header_left, header_right = st.columns([4, 1])

with header_left:
    st.title("IRR Calculator")

with header_right:
    # Ensure 'company_logo.png' is in the same folder as this script
    try:
        st.image("company_logo.png", width=150)
    except FileNotFoundError:
        st.write("*(Logo placeholder)*")

st.markdown("---")

# --- Create 3 parallel columns for the main app ---
col1, col2, col3 = st.columns(3)

# --- Column 1: Inputs ---
with col1:
    st.subheader("1. Parameters & Rates")

    st.text_input("Total Value of Assets (KES)", key="asset_input", on_change=format_asset)
    st.text_input("Loan Amount (KES)", key="loan_input", on_change=format_loan)
    st.text_input("Documentation Charge (KES)", key="doc_input", on_change=format_doc)

    total_asset_value = float(st.session_state.asset_input.replace(',', ''))
    loan_amount = float(st.session_state.loan_input.replace(',', ''))
    doc_charge = float(st.session_state.doc_input.replace(',', ''))

    num_units = st.number_input("Number of Units", min_value=1, value=1, step=1)
    repayment_months = st.number_input("Repayment Length (Months)", min_value=1, value=12, step=1)
    finance_rate_pct = st.number_input("Finance Rate (%)", min_value=0.0, max_value=100.0, value=16.0, step=0.1)
    commitment_rate_pct = st.number_input("Commitment Rate (%)", min_value=0.0, max_value=20.0, value=2.0, step=0.1)

# --- Background Math ---
finance_rate = finance_rate_pct / 100.0
commitment_rate = commitment_rate_pct / 100.0
repayment_years = repayment_months / 12.0

commitment_cost = loan_amount * commitment_rate * repayment_years
bank_charge = repayment_years * 6000
option_money = num_units * 10000
transfer_charge = num_units * 10000
other_charges = commitment_cost + bank_charge + doc_charge + option_money + transfer_charge

# --- Column 2: Fees Breakdown ---
with col2:
    st.subheader("2. Fees & Repayment Logic")

    # Updated Asset Value Box (Uses Primary Blue #415367)
    st.markdown(
        f"""
        <div style="background-color: #a72753; padding: 15px; border-radius: 5px; color: white;">
            <strong>Asset Value:</strong> KES {total_asset_value:,.2f} for {num_units} unit(s)
        </div>
        <br>
        """,
        unsafe_allow_html=True
    )

    st.write(f"- **Commitment Cost:** KES {commitment_cost:,.2f}")
    st.write(f"- **Bank Charge:** KES {bank_charge:,.2f}")
    st.write(f"- **Documentation Charge:** KES {doc_charge:,.2f}")
    st.write(f"- **Option Money:** KES {option_money:,.2f}")
    st.write(f"- **Transfer Charge:** KES {transfer_charge:,.2f}")

    # Total Charges Box (Uses Secondary Crimson #a72753)
    st.markdown(
        f"""
        <br>
        <div style="background-color: #a72753; padding: 15px; border-radius: 5px; color: white; text-align: center;">
            <strong>Total Other Charges: KES {other_charges:,.2f}</strong>
        </div>
        <br>
        """,
        unsafe_allow_html=True
    )

    pays_cash_upfront = st.toggle("Pay Other Charges upfront in cash?", value=True)

# --- Column 3: Final Metrics ---
with col3:
    st.subheader("3. Final Loan Metrics")

    if loan_amount > 0:
        fc = loan_amount * finance_rate * repayment_years

        if pays_cash_upfront:
            finance_cost = fc
            initial_cash_flow = -(loan_amount - other_charges)
        else:
            finance_cost = fc + other_charges
            initial_cash_flow = -loan_amount

        total_to_be_repaid = loan_amount + finance_cost
        emi_amount = total_to_be_repaid / repayment_months

        cash_flows = [initial_cash_flow] + [emi_amount] * repayment_months
        monthly_irr = calculate_irr(cash_flows)

        st.markdown(f"#### **Finance Cost:** KES {finance_cost:,.2f}")
        st.markdown(f"#### **Total to be Repaid:** KES {total_to_be_repaid:,.2f}")
        st.markdown(f"#### **Monthly EMI:** KES {emi_amount:,.2f}")

        if monthly_irr is not None:
            annual_irr = monthly_irr * 12
            # Annualized IRR Box (Uses Secondary Crimson #a72753)
            st.markdown(
                f"""
                <br>
                <div style="background-color: #a72753; padding: 15px; border-radius: 5px; color: white; text-align: center;">
                    <h3 style="margin:0; color: white;">Annualized IRR: {annual_irr * 100:.6f}%</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Invalid IRR Error Box (Uses Secondary Crimson #a72753)
            st.markdown(
                """
                <br>
                <div style="background-color: #a72753; padding: 15px; border-radius: 5px; color: white;">
                    Could not calculate a valid IRR for these inputs.
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        # Zero Loan Warning Box (Uses Secondary Crimson #a72753 instead of gray/yellow)
        st.markdown(
            """
            <div style="background-color: #a72753; padding: 15px; border-radius: 5px; color: white;">
                Please enter a Loan Amount greater than 0 to view final metrics.
            </div>
            """,
            unsafe_allow_html=True
        )