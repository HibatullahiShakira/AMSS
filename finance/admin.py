"""
Finance Admin — Register all models for Django admin interface.

Provides admin panels for all four modules:
1. Core Accounting (Accounts, Journal Entries, Transactions, Bank)
2. Loan & Liability (Liabilities, Payment Schedules, Creditors)
3. Uncertainty Engine (Macro Snapshots, Scenario Forecasts)
4. Asset Tracker (Assets, Maintenance, Disposals, Depreciation)
"""

from django.contrib import admin

from .models import (
    Income, Expense, Asset, Liability, PaymentSchedule,
    PaymentInstallment, Creditor, Collateral,
    Customer, Supplier, AccountsReceivable, AccountsPayable,
    CashFlowForecast,
)
from .models_accounting import (
    Account, JournalEntry, JournalEntryLine,
    Transaction, BankAccount, BankStatement, ReconciliationSession,
)
from .models_uncertainty import MacroSnapshot, ScenarioForecast, MacroDataLog
from .models_asset import AssetMaintenanceLog, AssetDisposal, DepreciationSchedule


# ─── Existing Models ───

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'source', 'currency', 'date', 'business')
    list_filter = ('source', 'currency', 'business')
    search_fields = ('description',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'expense_category', 'currency', 'date', 'business')
    list_filter = ('expense_category', 'currency', 'business')
    search_fields = ('description',)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'asset_types', 'valuation_method', 'useful_life', 'business')
    list_filter = ('asset_types', 'valuation_method', 'is_appreciating', 'business')
    search_fields = ('name', 'description')


@admin.register(Liability)
class LiabilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'liability_type', 'due_date', 'paid_amount', 'business')
    list_filter = ('liability_type', 'business')
    search_fields = ('name', 'description')


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ('liability', 'payment_frequency', 'start_date', 'end_date', 'business')
    list_filter = ('payment_frequency',)


@admin.register(PaymentInstallment)
class PaymentInstallmentAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'date', 'principal', 'interest', 'monthly_payment', 'remaining_principal')


@admin.register(Creditor)
class CreditorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone_number', 'email', 'business')
    search_fields = ('name',)


@admin.register(Collateral)
class CollateralAdmin(admin.ModelAdmin):
    list_display = ('liability', 'description', 'value', 'business')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_info', 'business', 'created_at')
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_info', 'business', 'created_at')
    search_fields = ('name',)


@admin.register(AccountsReceivable)
class AccountsReceivableAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount_due', 'due_date', 'status', 'business')
    list_filter = ('status',)


@admin.register(AccountsPayable)
class AccountsPayableAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'amount_due', 'due_date', 'status', 'business')
    list_filter = ('status',)


@admin.register(CashFlowForecast)
class CashFlowForecastAdmin(admin.ModelAdmin):
    list_display = ('date', 'predicted_inflow', 'predicted_outflow', 'net_cash_flow', 'business')


# ─── Module 1: Core Accounting ───

class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2
    fields = ('account', 'debit_amount', 'credit_amount', 'description')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'is_active', 'is_system_account', 'business')
    list_filter = ('account_type', 'is_active', 'business')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'date', 'description', 'status', 'entry_type', 'business')
    list_filter = ('status', 'entry_type', 'business')
    search_fields = ('reference_number', 'description')
    inlines = [JournalEntryLineInline]
    readonly_fields = ('reference_number', 'created_at', 'updated_at')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_type', 'amount', 'currency', 'date',
        'payment_method', 'is_reconciled', 'business'
    )
    list_filter = ('transaction_type', 'payment_method', 'is_reconciled', 'business')
    search_fields = ('description', 'counterparty', 'external_reference')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_number', 'account_name', 'current_balance', 'is_active', 'business')
    list_filter = ('bank_name', 'is_active', 'business')


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = (
        'bank_account', 'transaction_date', 'description',
        'debit_amount', 'credit_amount', 'is_reconciled'
    )
    list_filter = ('is_reconciled', 'bank_account')


@admin.register(ReconciliationSession)
class ReconciliationSessionAdmin(admin.ModelAdmin):
    list_display = (
        'bank_account', 'statement_start_date', 'statement_end_date',
        'status', 'matched_count', 'unmatched_count', 'business'
    )
    list_filter = ('status',)


# ─── Module 3: Uncertainty Engine ───

@admin.register(MacroSnapshot)
class MacroSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        'effective_date', 'cbn_monetary_policy_rate', 'inflation_rate',
        'fx_rate_usd_ngn', 'source', 'is_current'
    )
    list_filter = ('source', 'is_current')
    ordering = ('-effective_date',)
    fieldsets = (
        ('Core Rates', {
            'fields': (
                'cbn_monetary_policy_rate', 'inflation_rate',
                'inflation_rate_monthly',
            ),
        }),
        ('Exchange Rates', {
            'fields': ('fx_rate_usd_ngn', 'fx_rate_usd_ngn_parallel'),
        }),
        ('Interest Rates', {
            'fields': (
                'prime_lending_rate', 'savings_deposit_rate',
                'treasury_bill_rate',
            ),
        }),
        ('Energy Costs', {
            'fields': ('diesel_price_per_litre', 'petrol_price_per_litre'),
        }),
        ('Growth', {
            'fields': ('gdp_growth_rate',),
        }),
        ('Metadata', {
            'fields': ('effective_date', 'source', 'notes', 'is_current'),
        }),
    )


@admin.register(ScenarioForecast)
class ScenarioForecastAdmin(admin.ModelAdmin):
    list_display = (
        'business', 'forecast_type', 'base_case',
        'optimistic_case', 'pessimistic_case', 'generated_at'
    )
    list_filter = ('forecast_type', 'business')


@admin.register(MacroDataLog)
class MacroDataLogAdmin(admin.ModelAdmin):
    list_display = ('source', 'status', 'indicators_fetched', 'fetched_at')
    list_filter = ('source', 'status')
    readonly_fields = ('response_data',)


# ─── Module 4: Asset Tracker ───

@admin.register(AssetMaintenanceLog)
class AssetMaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('asset', 'date', 'maintenance_type', 'cost', 'performed_by', 'business')
    list_filter = ('maintenance_type', 'business')
    search_fields = ('asset__name', 'description')


@admin.register(AssetDisposal)
class AssetDisposalAdmin(admin.ModelAdmin):
    list_display = ('asset', 'date', 'method', 'proceeds', 'gain_or_loss', 'business')
    list_filter = ('method', 'business')


@admin.register(DepreciationSchedule)
class DepreciationScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'asset', 'period_number', 'opening_book_value',
        'depreciation_amount', 'closing_book_value', 'is_posted'
    )
    list_filter = ('is_posted', 'business')
