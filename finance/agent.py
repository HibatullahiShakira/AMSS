import os
from langchain_ollama import ChatOllama
from langchain.tools import tool
from decimal import Decimal
from django.db.models import Sum

def get_business_agent(business):
    """
    Initializes and returns a LangChain agent bounded to a specific business tenant.
    """
    
    @tool
    def get_total_revenue(query: str) -> str:
        """Returns the total YTD revenue for the business."""
        from finance.models import Income
        total = Income.objects.filter(business=business).aggregate(t=Sum('amount'))['t'] or 0
        return f"Total Revenue is ₦{total:,.2f}"

    @tool
    def get_total_expenses(query: str) -> str:
        """Returns the total YTD expenses for the business."""
        from finance.models import Expense
        total = Expense.objects.filter(business=business).aggregate(t=Sum('amount'))['t'] or 0
        return f"Total Expenses are ₦{total:,.2f}"

    @tool
    def get_outstanding_invoices(query: str) -> str:
        """Returns a summary of unpaid or overdue invoices."""
        from billing.models import Invoice
        unpaid = Invoice.objects.filter(business=business, status__in=['SENT', 'PARTIALLY_PAID'])
        if not unpaid.exists():
            return "There are no outstanding invoices."
        
        result = "Outstanding Invoices:\n"
        for inv in unpaid[:5]:
            result += f"- {inv.invoice_number} to {inv.customer.name}: ₦{inv.balance_due:,.2f} due on {inv.due_date}\n"
        return result

    @tool
    def run_cashflow_simulation(query: str) -> str:
        """Runs a Monte Carlo Cash Flow at Risk (CFaR) simulation using current Nigerian macroeconomic parameters (Inflation, FX, Interest)."""
        from finance.helpers_uncertainty import cash_flow_at_risk
        try:
            results = cash_flow_at_risk(business, horizon_months=12, num_simulations=1000)
            risk = results['probability_negative'] * 100
            p5 = results['percentiles']['p5']
            p50 = results['percentiles']['p50_median']
            
            return (f"Monte Carlo Simulation complete.\n"
                    f"- Expected Cashflow (Median): ₦{p50:,.2f}\n"
                    f"- Pessimistic Cashflow (5th Percentile): ₦{p5:,.2f}\n"
                    f"- Probability of cash depletion (Burnout Risk): {risk:.1f}%")
        except Exception as e:
            return f"Error running simulation: {str(e)}"
            
    @tool
    def run_stress_test(query: str) -> str:
        """Runs macroeconomic stress tests (e.g., Inflation Spike, Revenue Collapse)."""
        from finance.helpers_uncertainty import stress_test_business
        try:
            results = stress_test_business(business)
            output = "Stress Test Results:\n"
            for res in results['stress_results']:
                output += f"- Scenario: {res['scenario']}\n  Impact: {res['impact_percentage']}%\n  Severity: {res['severity']}\n"
            return output
        except Exception as e:
            return f"Error running stress test: {str(e)}"

    tools = [
        get_total_revenue,
        get_total_expenses,
        get_outstanding_invoices,
        run_cashflow_simulation,
        run_stress_test
    ]

    from langgraph.prebuilt import create_react_agent

    # Initialize Local Open Source LLM (Ollama)
    llm = ChatOllama(model="llama3.2", temperature=0)

    # Create the modern LangGraph React Agent
    agent = create_react_agent(llm, tools)

    return agent
