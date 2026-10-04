"""
Core Accounting Serializers

Serializers for the double-entry accounting system:
Chart of Accounts, Journal Entries, Transactions, Bank Reconciliation.
"""

from decimal import Decimal

from rest_framework import serializers
from rest_framework_simplejwt.models import TokenUser

from users.models import User
from .models_accounting import (
    Account, JournalEntry, JournalEntryLine,
    Transaction, BankAccount, BankStatement, ReconciliationSession,
)


# ─────────────────────────────────────────────────────────────────────
# CHART OF ACCOUNTS
# ─────────────────────────────────────────────────────────────────────

class AccountSerializer(serializers.ModelSerializer):
    """Flat account serializer for list/detail views."""
    balance = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id', 'code', 'name', 'account_type', 'parent',
            'description', 'is_active', 'is_system_account',
            'currency', 'balance', 'children_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['is_system_account', 'created_at', 'updated_at']

    def get_children_count(self, obj):
        return obj.children.count()


class AccountTreeSerializer(serializers.ModelSerializer):
    """Recursive account serializer for tree/hierarchy view."""
    children = serializers.SerializerMethodField()
    balance = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )

    class Meta:
        model = Account
        fields = [
            'id', 'code', 'name', 'account_type', 'balance',
            'is_active', 'children',
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('code')
        return AccountTreeSerializer(children, many=True).data


# ─────────────────────────────────────────────────────────────────────
# JOURNAL ENTRIES
# ─────────────────────────────────────────────────────────────────────

class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = JournalEntryLine
        fields = [
            'id', 'account', 'account_code', 'account_name',
            'debit_amount', 'credit_amount', 'description',
        ]

    def validate(self, attrs):
        debit = attrs.get('debit_amount', Decimal('0.00'))
        credit = attrs.get('credit_amount', Decimal('0.00'))

        if debit > 0 and credit > 0:
            raise serializers.ValidationError(
                'A line cannot have both debit and credit amounts.'
            )
        if debit == 0 and credit == 0:
            raise serializers.ValidationError(
                'A line must have either a debit or credit amount.'
            )
        if debit < 0 or credit < 0:
            raise serializers.ValidationError('Amounts cannot be negative.')

        return attrs


class JournalEntrySerializer(serializers.ModelSerializer):
    """
    Full journal entry serializer with nested lines.
    Validates that debits == credits on create/update.
    """
    lines = JournalEntryLineSerializer(many=True)
    is_balanced = serializers.BooleanField(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True
    )

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'date', 'reference_number', 'description',
            'status', 'entry_type', 'source_module',
            'created_by', 'created_by_username',
            'posted_by', 'posted_at', 'voided_by', 'voided_at', 'void_reason',
            'is_balanced', 'total_amount', 'lines',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'reference_number', 'posted_by', 'posted_at',
            'voided_by', 'voided_at', 'created_at', 'updated_at',
        ]

    def validate_lines(self, lines_data):
        if len(lines_data) < 2:
            raise serializers.ValidationError(
                'A journal entry must have at least 2 lines.'
            )

        total_debit = sum(
            line.get('debit_amount', Decimal('0.00')) for line in lines_data
        )
        total_credit = sum(
            line.get('credit_amount', Decimal('0.00')) for line in lines_data
        )

        if total_debit != total_credit:
            raise serializers.ValidationError(
                f'Journal entry does not balance. '
                f'Debits: {total_debit}, Credits: {total_credit}'
            )

        return lines_data

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        request = self.context.get('request')
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        validated_data['created_by'] = user

        journal_entry = JournalEntry.objects.create(**validated_data)

        for line_data in lines_data:
            JournalEntryLine.objects.create(
                journal_entry=journal_entry, **line_data
            )

        return journal_entry

    def update(self, instance, validated_data):
        if instance.status == JournalEntry.Status.POSTED:
            raise serializers.ValidationError(
                'Cannot edit a posted journal entry. Void it and create a new one.'
            )

        lines_data = validated_data.pop('lines', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                JournalEntryLine.objects.create(
                    journal_entry=instance, **line_data
                )

        return instance


class JournalEntryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    total_amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )
    line_count = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'date', 'reference_number', 'description',
            'status', 'entry_type', 'total_amount', 'line_count',
            'created_at',
        ]

    def get_line_count(self, obj):
        return obj.lines.count()


class PostJournalEntrySerializer(serializers.Serializer):
    """Serializer for posting a draft journal entry."""
    confirm = serializers.BooleanField(
        default=True,
        help_text='Confirm posting this journal entry.'
    )


class VoidJournalEntrySerializer(serializers.Serializer):
    """Serializer for voiding a posted journal entry."""
    reason = serializers.CharField(
        max_length=500,
        help_text='Reason for voiding this journal entry.'
    )


# ─────────────────────────────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'journal_entry', 'transaction_type', 'amount',
            'currency', 'date', 'description', 'payment_method',
            'external_reference', 'is_reconciled', 'counterparty',
            'user', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        validated_data['user'] = user
        return super().create(validated_data)


# ─────────────────────────────────────────────────────────────────────
# BANK ACCOUNTS & RECONCILIATION
# ─────────────────────────────────────────────────────────────────────

class BankAccountSerializer(serializers.ModelSerializer):
    statement_count = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = [
            'id', 'account_name', 'bank_name', 'account_number',
            'sort_code', 'current_balance', 'currency', 'is_active',
            'linked_account', 'statement_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_statement_count(self, obj):
        return obj.statements.count()

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        return super().create(validated_data)


class BankStatementSerializer(serializers.ModelSerializer):
    matched_transaction_ref = serializers.CharField(
        source='matched_transaction.external_reference', read_only=True
    )

    class Meta:
        model = BankStatement
        fields = [
            'id', 'bank_account', 'transaction_date', 'value_date',
            'description', 'reference', 'debit_amount', 'credit_amount',
            'running_balance', 'is_reconciled',
            'matched_transaction', 'matched_transaction_ref',
            'created_at',
        ]
        read_only_fields = [
            'is_reconciled', 'matched_transaction', 'created_at',
        ]


class ReconciliationSessionSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(
        source='bank_account.bank_name', read_only=True
    )

    class Meta:
        model = ReconciliationSession
        fields = [
            'id', 'bank_account', 'bank_name',
            'statement_start_date', 'statement_end_date',
            'statement_closing_balance', 'status',
            'matched_count', 'unmatched_count', 'difference',
            'reconciled_by', 'started_at', 'completed_at',
        ]
        read_only_fields = [
            'matched_count', 'unmatched_count', 'difference',
            'reconciled_by', 'started_at', 'completed_at',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        validated_data['reconciled_by'] = user
        return super().create(validated_data)


# ─────────────────────────────────────────────────────────────────────
# FINANCIAL REPORT SERIALIZERS (read-only output)
# ─────────────────────────────────────────────────────────────────────

class TrialBalanceLineSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    account_type = serializers.CharField()
    debit_balance = serializers.DecimalField(max_digits=20, decimal_places=2)
    credit_balance = serializers.DecimalField(max_digits=20, decimal_places=2)


class TrialBalanceSerializer(serializers.Serializer):
    as_of_date = serializers.CharField()
    accounts = TrialBalanceLineSerializer(many=True)
    total_debits = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_credits = serializers.DecimalField(max_digits=20, decimal_places=2)
    is_balanced = serializers.BooleanField()


class DateRangeInputSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs):
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError(
                'start_date must be before end_date.'
            )
        return attrs


class AsOfDateInputSerializer(serializers.Serializer):
    as_of_date = serializers.DateField(required=False)
