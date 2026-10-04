from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Existing views
from .views import (
    IncomeViewSet, ExpenseViewSet, AssetViewSet, AssetProjectSimulation,
    LiabilityViewSet, PaymentScheduleViewSet, CollateralViewSet,
    CashFlowProjectionViewSet, CashFlowOptimizationViewSet,
    CreditorViewSet, CustomerViewSet, SupplierViewSet, EmployeeViewSet
)

# Module 1: Core Accounting views
from .views_accounting import (
    AccountViewSet, JournalEntryViewSet, TransactionViewSet,
    BankAccountViewSet, BankStatementViewSet, BankReconciliationViewSet,
    FinancialReportViewSet,
)

# Module 3: Uncertainty Engine views
from .views_uncertainty import MacroSnapshotViewSet, UncertaintyEngineViewSet

# Module 6: Expense & Reminder Engine
from .views_expense import (
    ExpenseCategoryViewSet, RecurringExpenseViewSet, ReminderViewSet, ExpenseIntelligenceViewSet
)

# Module 8: Nigerian Tax Engine
from .views_tax import (
    TaxConfigurationView, TaxTransactionViewSet, TaxReturnViewSet,
    TaxFilingDeadlineViewSet, TaxCalculatorViewSet
)

# Module 9: Analytics & Reporting
from .views_analytics import ReportingViewSet
from .views_data import DataManagementViewSet, DocumentParseViewSet

router = DefaultRouter()

# ─── Existing routes ───
router.register(r'incomes', IncomeViewSet, basename='income')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'assets', AssetViewSet, basename='assets')
router.register(r'asset_project_simulation', AssetProjectSimulation, basename='asset_project_simulation')
router.register(r'liabilities', LiabilityViewSet, basename='liabilities')
router.register(r'project_schedule', PaymentScheduleViewSet, basename='project_schedule')
router.register(r'collateral', CollateralViewSet, basename='collateral')
router.register(r'cash_projections', CashFlowProjectionViewSet, basename='cash_projections')
router.register(r'cash_flow', CashFlowOptimizationViewSet, basename='cash_flow')
router.register(r'creditors', CreditorViewSet, basename='creditors')
router.register(r'customers', CustomerViewSet, basename='customers')
router.register(r'suppliers', SupplierViewSet, basename='suppliers')
router.register(r'employees', EmployeeViewSet, basename='employees')

# ─── Module 1: Core Accounting ───
router.register(r'accounts', AccountViewSet, basename='accounts')
router.register(r'journal-entries', JournalEntryViewSet, basename='journal-entries')
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-accounts')
router.register(r'bank-statements', BankStatementViewSet, basename='bank-statements')
router.register(r'reconciliation', BankReconciliationViewSet, basename='reconciliation')
router.register(r'reports', FinancialReportViewSet, basename='reports')

# ─── Module 3: Uncertainty Engine ───
router.register(r'macro', MacroSnapshotViewSet, basename='macro')
router.register(r'uncertainty', UncertaintyEngineViewSet, basename='uncertainty')

# ─── Module 6: Expense & Reminder Engine ───
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-categories')
router.register(r'recurring-expenses', RecurringExpenseViewSet, basename='recurring-expenses')
router.register(r'reminders', ReminderViewSet, basename='reminders')
router.register(r'expense-intelligence', ExpenseIntelligenceViewSet, basename='expense-intelligence')

# ─── Module 8: Nigerian Tax Engine ───
router.register(r'tax-transactions', TaxTransactionViewSet, basename='tax-transactions')
router.register(r'tax-returns', TaxReturnViewSet, basename='tax-returns')
router.register(r'tax-deadlines', TaxFilingDeadlineViewSet, basename='tax-deadlines')
router.register(r'tax-calculator', TaxCalculatorViewSet, basename='tax-calculator')

# ─── Module 9: Analytics & Reporting ───
from .views_analytics import ReportingViewSet
router.register(r'analytics', ReportingViewSet, basename='analytics')

# ─── Module 5: Business Agent ───
from .views_agent import AgentViewSet
router.register(r'agent', AgentViewSet, basename='agent')

# ─── Data Management & Imports ───
router.register(r'data', DataManagementViewSet, basename='data')
router.register(r'document', DocumentParseViewSet, basename='document')

from django.urls import path

urlpatterns = [
    path('', include(router.urls)),
    path('tax-config/', TaxConfigurationView.as_view(), name='tax-config'),
]
