"""
Core Accounting Views

ViewSets for:
- Chart of Accounts management
- Journal Entry CRUD + post/void workflow
- Transaction listing with filters
- Bank Account management
- Bank Reconciliation engine
- Financial Reports (Trial Balance, P&L, Balance Sheet, Cash Flow)
"""

from datetime import date

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.models import TokenUser

from users.models import User
from .helpers_accounting import (
    seed_default_accounts,
    generate_trial_balance,
    generate_income_statement,
    generate_balance_sheet,
    generate_cash_flow_statement,
    auto_reconcile_transactions,
)
from .models_accounting import (
    Account, JournalEntry, JournalEntryLine,
    Transaction, BankAccount, BankStatement, ReconciliationSession,
)
from .permissions import IsOwnerAdminManagerOrReadonly, IsOwnerOrAdmin
from .serializers_accounting import (
    AccountSerializer, AccountTreeSerializer,
    JournalEntrySerializer, JournalEntryListSerializer,
    PostJournalEntrySerializer, VoidJournalEntrySerializer,
    TransactionSerializer,
    BankAccountSerializer, BankStatementSerializer,
    ReconciliationSessionSerializer,
    DateRangeInputSerializer, AsOfDateInputSerializer,
)


class AccountingBaseViewSet(viewsets.ModelViewSet):
    """Base viewset with business-scoping logic for accounting views."""

    def get_business(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        business = getattr(user, 'business', None)
        return business

    def get_queryset(self):
        business = self.get_business()
        if business is None:
            return self.queryset.none()
        return self.queryset.filter(business=business)

    def get_user(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        return user


# ─────────────────────────────────────────────────────────────────────
# CHART OF ACCOUNTS
# ─────────────────────────────────────────────────────────────────────

class AccountViewSet(AccountingBaseViewSet):
    """
    Manage the Chart of Accounts for a business.

    Endpoints:
    - GET /accounts/ — list all accounts (flat)
    - GET /accounts/tree/ — hierarchical tree view
    - GET /accounts/{id}/ — account detail with balance
    - POST /accounts/ — create new account
    - POST /accounts/seed_defaults/ — create default Nigerian SME chart of accounts
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """Return the chart of accounts as a nested tree."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        root_accounts = Account.objects.filter(
            business=business, parent=None, is_active=True
        ).order_by('code')

        serializer = AccountTreeSerializer(root_accounts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='seed-defaults')
    def seed_defaults(self, request):
        """Seed the default Nigerian SME chart of accounts."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        count = seed_default_accounts(business)
        return JsonResponse({
            "message": f"Created {count} default accounts.",
            "total_accounts": Account.objects.filter(business=business).count(),
        })

    @action(detail=True, methods=['get'], url_path='ledger')
    def ledger(self, request, pk=None):
        """Get all journal entry lines for a specific account (account ledger)."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        try:
            account = Account.objects.get(business=business, pk=pk)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found."}, status=404)

        lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__status=JournalEntry.Status.POSTED,
        ).select_related('journal_entry').order_by('journal_entry__date')

        ledger_entries = []
        running_balance = 0
        for line in lines:
            if account.account_type in ['ASSET', 'EXPENSE']:
                running_balance += float(line.debit_amount) - float(line.credit_amount)
            else:
                running_balance += float(line.credit_amount) - float(line.debit_amount)

            ledger_entries.append({
                'date': line.journal_entry.date,
                'reference': line.journal_entry.reference_number,
                'description': line.description or line.journal_entry.description,
                'debit': str(line.debit_amount),
                'credit': str(line.credit_amount),
                'running_balance': f"{running_balance:.2f}",
            })

        return JsonResponse({
            'account': AccountSerializer(account).data,
            'ledger': ledger_entries,
        })


# ─────────────────────────────────────────────────────────────────────
# JOURNAL ENTRIES
# ─────────────────────────────────────────────────────────────────────

class JournalEntryViewSet(AccountingBaseViewSet):
    """
    Manage journal entries with a Draft → Posted → Void workflow.

    Endpoints:
    - GET /journal-entries/ — list all journal entries
    - POST /journal-entries/ — create a new draft journal entry
    - POST /journal-entries/{id}/post/ — post a draft entry
    - POST /journal-entries/{id}/void/ — void a posted entry
    """
    queryset = JournalEntry.objects.all()
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return JournalEntryListSerializer
        return JournalEntrySerializer

    @action(detail=True, methods=['post'], url_path='post')
    def post_entry(self, request, pk=None):
        """Post a draft journal entry — makes it affect account balances."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        try:
            entry = JournalEntry.objects.get(business=business, pk=pk)
        except JournalEntry.DoesNotExist:
            return JsonResponse({"error": "Journal entry not found."}, status=404)

        if entry.status != JournalEntry.Status.DRAFT:
            return JsonResponse(
                {"error": f"Cannot post. Current status: {entry.status}"},
                status=400,
            )

        if not entry.is_balanced:
            return JsonResponse(
                {"error": "Cannot post. Journal entry does not balance."},
                status=400,
            )

        user = self.get_user()
        entry.status = JournalEntry.Status.POSTED
        entry.posted_by = user
        entry.posted_at = timezone.now()
        entry.save()

        return JsonResponse({
            "message": "Journal entry posted successfully.",
            "entry": JournalEntrySerializer(entry).data,
        })

    @action(detail=True, methods=['post'], url_path='void')
    def void_entry(self, request, pk=None):
        """Void a posted journal entry — reverses its effect on account balances."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        try:
            entry = JournalEntry.objects.get(business=business, pk=pk)
        except JournalEntry.DoesNotExist:
            return JsonResponse({"error": "Journal entry not found."}, status=404)

        if entry.status != JournalEntry.Status.POSTED:
            return JsonResponse(
                {"error": f"Cannot void. Current status: {entry.status}"},
                status=400,
            )

        serializer = VoidJournalEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_user()
        entry.status = JournalEntry.Status.VOID
        entry.voided_by = user
        entry.voided_at = timezone.now()
        entry.void_reason = serializer.validated_data['reason']
        entry.save()

        return JsonResponse({
            "message": "Journal entry voided successfully.",
            "entry": JournalEntrySerializer(entry).data,
        })


# ─────────────────────────────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────

class TransactionViewSet(AccountingBaseViewSet):
    """
    List and filter financial transactions.
    Transactions are typically auto-created via journal entries.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter by date range
        start = self.request.query_params.get('start_date')
        end = self.request.query_params.get('end_date')
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)

        # Filter by type
        txn_type = self.request.query_params.get('type')
        if txn_type:
            qs = qs.filter(transaction_type=txn_type)

        # Filter by reconciliation status
        reconciled = self.request.query_params.get('reconciled')
        if reconciled is not None:
            qs = qs.filter(is_reconciled=reconciled.lower() == 'true')

        return qs

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Get a summary of transaction totals by type."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        from django.db.models import Count
        summary = Transaction.objects.filter(
            business=business
        ).values('transaction_type').annotate(
            count=Count('id'),
            total=Sum('amount'),
        ).order_by('transaction_type')

        return JsonResponse({"summary": list(summary)})


# ─────────────────────────────────────────────────────────────────────
# BANK ACCOUNTS
# ─────────────────────────────────────────────────────────────────────

class BankAccountViewSet(AccountingBaseViewSet):
    """Manage business bank accounts."""
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=False, methods=['get'], url_path='balance-summary')
    def balance_summary(self, request):
        """Get total balance across all bank accounts."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        accounts = BankAccount.objects.filter(business=business, is_active=True)
        total = accounts.aggregate(total=Sum('current_balance'))['total'] or 0

        return JsonResponse({
            "total_bank_balance": total,
            "account_count": accounts.count(),
            "accounts": list(accounts.values(
                'id', 'bank_name', 'account_number', 'current_balance', 'currency'
            )),
        })


# ─────────────────────────────────────────────────────────────────────
# BANK STATEMENTS
# ─────────────────────────────────────────────────────────────────────

class BankStatementViewSet(viewsets.ModelViewSet):
    """Upload and manage bank statement lines."""
    queryset = BankStatement.objects.all()
    serializer_class = BankStatementSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        bank_account_id = self.request.query_params.get('bank_account')
        if bank_account_id:
            return self.queryset.filter(bank_account_id=bank_account_id)
        return self.queryset.none()


# ─────────────────────────────────────────────────────────────────────
# BANK RECONCILIATION
# ─────────────────────────────────────────────────────────────────────

class BankReconciliationViewSet(AccountingBaseViewSet):
    """
    Bank reconciliation workflow.

    - POST /reconciliation/ — start a new reconciliation session
    - POST /reconciliation/{id}/auto-match/ — run auto-matching algorithm
    - POST /reconciliation/{id}/complete/ — mark session as complete
    """
    queryset = ReconciliationSession.objects.all()
    serializer_class = ReconciliationSessionSerializer
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=True, methods=['post'], url_path='auto-match')
    def auto_match(self, request, pk=None):
        """Run the automated reconciliation matching algorithm."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        try:
            session = ReconciliationSession.objects.get(
                business=business, pk=pk
            )
        except ReconciliationSession.DoesNotExist:
            return JsonResponse(
                {"error": "Reconciliation session not found."}, status=404
            )

        if session.status != ReconciliationSession.Status.IN_PROGRESS:
            return JsonResponse(
                {"error": "Session is not in progress."}, status=400
            )

        results = auto_reconcile_transactions(session)

        return JsonResponse({
            "message": "Auto-matching completed.",
            "matched": results['matched'],
            "unmatched": results['unmatched'],
        })

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Mark a reconciliation session as completed."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        try:
            session = ReconciliationSession.objects.get(
                business=business, pk=pk
            )
        except ReconciliationSession.DoesNotExist:
            return JsonResponse(
                {"error": "Reconciliation session not found."}, status=404
            )

        session.status = ReconciliationSession.Status.COMPLETED
        session.completed_at = timezone.now()
        session.save()

        return JsonResponse({
            "message": "Reconciliation session completed.",
            "session": ReconciliationSessionSerializer(session).data,
        })


# ─────────────────────────────────────────────────────────────────────
# FINANCIAL REPORTS
# ─────────────────────────────────────────────────────────────────────

class FinancialReportViewSet(viewsets.ViewSet):
    """
    Generate standard financial reports.

    - GET /reports/trial-balance/?as_of_date=YYYY-MM-DD
    - GET /reports/income-statement/?start_date=...&end_date=...
    - GET /reports/balance-sheet/?as_of_date=YYYY-MM-DD
    - GET /reports/cash-flow/?start_date=...&end_date=...
    """
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_business(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        return getattr(user, 'business', None)

    @action(detail=False, methods=['get'], url_path='trial-balance')
    def trial_balance(self, request):
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        as_of = request.query_params.get('as_of_date')
        as_of_date = date.fromisoformat(as_of) if as_of else None

        report = generate_trial_balance(business, as_of_date)
        return JsonResponse(report)

    @action(detail=False, methods=['get'], url_path='income-statement')
    def income_statement(self, request):
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        serializer = DateRangeInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = generate_income_statement(
            business,
            serializer.validated_data['start_date'],
            serializer.validated_data['end_date'],
        )
        return JsonResponse(report)

    @action(detail=False, methods=['get'], url_path='balance-sheet')
    def balance_sheet(self, request):
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        as_of = request.query_params.get('as_of_date')
        as_of_date = date.fromisoformat(as_of) if as_of else None

        report = generate_balance_sheet(business, as_of_date)
        return JsonResponse(report)

    @action(detail=False, methods=['get'], url_path='cash-flow')
    def cash_flow_statement(self, request):
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        serializer = DateRangeInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = generate_cash_flow_statement(
            business,
            serializer.validated_data['start_date'],
            serializer.validated_data['end_date'],
        )
        return JsonResponse(report)
