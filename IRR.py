import streamlit as st
import pandas as pd
from scipy.optimize import newton, brentq

# --- Standard IRR Logic ---
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

# --- UI Layout Setup ---
st.set_page_config(page_title="IRR Calculator", layout="wide")
st.title("IRR Calculator")
st.markdown("---")

# --- Inputs ---
st.markdown("### 1. Core Loan Parameters")
total_asset_value = st.number_input("Total Value of Assets (KES)", min_value=0.0, value=8000000.0, step=100000.0)
loan_amount = st.number_input("Loan Amount (KES)", min_value=0.0, value=5000000.0, step=100000.0)
doc_charge = st.number_input("Documentation Charge (KES)", min_value=0.0, value=17000.0, step=1000.0)
num_units = st.number_input("Number of Units", min_value=1, value=2, step=1)
repayment_months = st.number_input("Repayment Length (Months)", min_value=1, value=24, step=1)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("### 2. Rates")
finance_rate_pct = st.slider("Finance Rate (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.1)
commitment_rate_pct = st.slider("Commitment Rate (%)", min_value=0.0, max_value=20.0, value=2.0, step=0.1)

finance_rate = finance_rate_pct / 100.0
commitment_rate = commitment_rate_pct / 100.0
repayment_years = repayment_months / 12.0

st.markdown("---")
st.markdown("### 3. Fees & Repayment Logic")

commitment_cost = loan_amount * commitment_rate * repayment_years
bank_charge = repayment_years * 6000
option_money = repayment_years * 10000
transfer_charge = repayment_years * 10000
other_charges = commitment_cost + bank_charge + doc_charge + option_money + transfer_charge

st.info(f"**Total Asset Value:** KES {total_asset_value:,.2f} for {num_units} unit(s)")

st.markdown("#### Itemized 'Other Charges' Breakdown")
st.write(f"- **Commitment Cost:** KES {commitment_cost:,.2f}")
st.write(f"- **Bank Charge:** KES {bank_charge:,.2f}")
st.write(f"- **Documentation Charge:** KES {doc_charge:,.2f}")
st.write(f"- **Option Money:** KES {option_money:,.2f}")
st.write(f"- **Transfer Charge:** KES {transfer_charge:,.2f}")
st.success(f"**Total Other Charges: KES {other_charges:,.2f}**")

st.markdown("#### Payment Structure")
pays_cash_upfront = st.toggle("Pay Other Charges upfront in cash?", value=True)

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

st.markdown("---")
st.markdown("### Final Loan Metrics")

st.markdown(f"#### **Finance Cost:** KES {finance_cost:,.2f}")
st.markdown(f"#### **Total to be Repaid:** KES {total_to_be_repaid:,.2f}")
st.markdown(f"#### **Monthly EMI:** KES {emi_amount:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

if monthly_irr is not None:
    annual_irr = monthly_irr * 12
    st.error(f"## Annualized IRR: {annual_irr * 100:.6f}%")
else:
    st.error("Could not calculate a valid IRR for these inputs.")