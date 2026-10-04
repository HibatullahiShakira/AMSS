"""
Asset Tracker — Enhanced Business Logic

Implements:
- Depreciation schedule generation (Straight-Line, Reducing Balance)
- Asset-Liability mismatch detection (Negative Equity, Drag, Ghost assets)
- Asset disposal with gain/loss computation
- Asset register report
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, F, Q

from .models import Asset, Liability
from .models_asset import AssetMaintenanceLog, AssetDisposal, DepreciationSchedule
from .helpers_uncertainty import get_macro_parameters


def generate_depreciation_schedule(asset):
    """
    Generate a full depreciation schedule over the asset's useful life.

    Supports:
    - Straight-Line: (cost - residual) / useful life
    - Reducing Balance (Declining-Balance): rate * book value each period
    - Double-Declining-Balance: 2/useful_life * book value

    Returns list of period entries and saves them to the database.
    """
    cost = Decimal(str(asset.amount))
    residual = Decimal(str(asset.residual_value))
    useful_life = int(asset.useful_life)
    method = asset.valuation_method

    if useful_life <= 0:
        return []

    # Clear existing schedule
    DepreciationSchedule.objects.filter(asset=asset).delete()

    schedules = []
    opening_value = cost
    accumulated = Decimal('0.00')
    start_year = int(asset.date_acquired)

    for period in range(1, useful_life + 1):
        if method == 'Straight-Line':
            annual_dep = (cost - residual) / useful_life

        elif method == 'Declining-Balance':
            rate = Decimal('1') - (residual / cost) ** (Decimal('1') / useful_life)
            annual_dep = opening_value * rate

        elif method == 'Double-Declining-Balance':
            rate = Decimal('2') / useful_life
            annual_dep = opening_value * rate

        elif method == 'Sum-of-the-Years-Digits':
            total_years = sum(range(1, useful_life + 1))
            remaining_years = useful_life - period + 1
            annual_dep = (cost - residual) * Decimal(str(remaining_years)) / total_years

        elif method == 'Units-of-Production':
            # Simplified — treat as straight-line if no production data
            annual_dep = (cost - residual) / useful_life

        else:
            annual_dep = (cost - residual) / useful_life

        # Don't depreciate below residual value
        if opening_value - annual_dep < residual:
            annual_dep = opening_value - residual

        if annual_dep < 0:
            annual_dep = Decimal('0.00')

        accumulated += annual_dep
        closing_value = cost - accumulated

        period_start = date(start_year + period - 1, 1, 1)
        period_end = date(start_year + period - 1, 12, 31)

        schedule_entry = DepreciationSchedule(
            asset=asset,
            business=asset.business,
            period_number=period,
            period_start_date=period_start,
            period_end_date=period_end,
            opening_book_value=opening_value,
            depreciation_amount=round(annual_dep, 2),
            accumulated_depreciation=round(accumulated, 2),
            closing_book_value=round(closing_value, 2),
        )
        schedules.append(schedule_entry)
        opening_value = closing_value

    DepreciationSchedule.objects.bulk_create(schedules)

    return [
        {
            'period': s.period_number,
            'period_start': str(s.period_start_date),
            'period_end': str(s.period_end_date),
            'opening_value': str(s.opening_book_value),
            'depreciation': str(s.depreciation_amount),
            'accumulated': str(s.accumulated_depreciation),
            'closing_value': str(s.closing_book_value),
        }
        for s in schedules
    ]


def compute_asset_book_value(asset):
    """
    Compute the current net book value of an asset based on
    its depreciation schedule.
    """
    current_year = date.today().year
    years_used = current_year - int(asset.date_acquired)

    if asset.is_appreciating:
        # For appreciating assets, apply appreciation
        rate = float(asset.appreciation_rate) / 100
        return float(asset.amount) * (1 + rate) ** years_used

    # For depreciating assets, get from schedule
    latest_schedule = DepreciationSchedule.objects.filter(
        asset=asset,
        period_end_date__lte=date.today(),
    ).order_by('-period_number').first()

    if latest_schedule:
        return float(latest_schedule.closing_book_value)

    # Fallback to simple straight-line
    annual_dep = (float(asset.amount) - float(asset.residual_value)) / max(asset.useful_life, 1)
    book_value = float(asset.amount) - (annual_dep * years_used)
    return max(book_value, float(asset.residual_value))


def detect_asset_liability_mismatches(business):
    """
    Detect asset-liability mismatches per the blueprint's algorithm:

    1. NEGATIVE EQUITY ASSET: financing balance > book value
    2. DRAG ASSET: annual cost > annual contribution
    3. GHOST ASSET: fully depreciated but loan not paid

    Returns a list of alerts for each detected mismatch.
    """
    assets = Asset.objects.filter(business=business)
    liabilities = Liability.objects.filter(business=business)
    macro = get_macro_parameters()

    alerts = []

    for asset in assets:
        book_value = compute_asset_book_value(asset)
        annual_maintenance = float(asset.annual_maintenance_cost)

        # Find linked liabilities (equipment finance, loans for this asset)
        linked_liabilities = liabilities.filter(
            Q(name__icontains=asset.name) |
            Q(description__icontains=asset.name)
        )

        for liability in linked_liabilities:
            outstanding = float(liability.get_outstanding_balance())

            # 1. NEGATIVE EQUITY ASSET: owe more than it's worth
            if outstanding > book_value and book_value > 0:
                shortfall = outstanding - book_value
                alerts.append({
                    'type': 'NEGATIVE_EQUITY',
                    'severity': 'CRITICAL',
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'liability_id': liability.id,
                    'liability_name': liability.name,
                    'book_value': round(book_value, 2),
                    'outstanding_balance': round(outstanding, 2),
                    'shortfall': round(shortfall, 2),
                    'message': (
                        f"Your {asset.name} (₦{book_value:,.0f} book value) "
                        f"has an outstanding loan of ₦{outstanding:,.0f}. "
                        f"You owe ₦{shortfall:,.0f} more than the asset is worth. "
                        f"Consider refinancing or disposal."
                    ),
                })

        # 2. DRAG ASSET: annual cost exceeds its value contribution
        if not asset.is_appreciating and asset.useful_life > 0:
            annual_dep = (float(asset.amount) - float(asset.residual_value)) / asset.useful_life
            total_annual_cost = annual_dep + annual_maintenance

            # Simple heuristic: if annual cost > 30% of asset value, it's a drag
            if book_value > 0 and total_annual_cost / book_value > 0.30:
                alerts.append({
                    'type': 'DRAG_ASSET',
                    'severity': 'WARNING',
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'book_value': round(book_value, 2),
                    'annual_depreciation': round(annual_dep, 2),
                    'annual_maintenance': annual_maintenance,
                    'total_annual_cost': round(total_annual_cost, 2),
                    'cost_to_value_ratio': round(total_annual_cost / book_value, 4),
                    'message': (
                        f"Your {asset.name} costs ₦{total_annual_cost:,.0f}/year to own "
                        f"(depreciation + maintenance) against a book value of "
                        f"₦{book_value:,.0f}. Review if this asset is still productive."
                    ),
                })

        # 3. GHOST ASSET: fully depreciated but still has linked debt
        if book_value <= float(asset.residual_value) * 1.05:
            for liability in linked_liabilities:
                outstanding = float(liability.get_outstanding_balance())
                if outstanding > 0:
                    alerts.append({
                        'type': 'GHOST_ASSET',
                        'severity': 'WARNING',
                        'asset_id': asset.id,
                        'asset_name': asset.name,
                        'liability_id': liability.id,
                        'liability_name': liability.name,
                        'book_value': round(book_value, 2),
                        'outstanding_balance': round(outstanding, 2),
                        'message': (
                            f"Your {asset.name} is fully depreciated "
                            f"(book value: ₦{book_value:,.0f}) but still has "
                            f"₦{outstanding:,.0f} outstanding on {liability.name}. "
                            f"You are paying for an asset that has no book value."
                        ),
                    })

    return {
        'alert_count': len(alerts),
        'critical_count': sum(1 for a in alerts if a['severity'] == 'CRITICAL'),
        'warning_count': sum(1 for a in alerts if a['severity'] == 'WARNING'),
        'alerts': alerts,
    }


def generate_asset_register_report(business):
    """
    Generate a full asset register report with current book values
    and depreciation status.
    """
    assets = Asset.objects.filter(business=business)

    register = []
    total_cost = Decimal('0.00')
    total_book_value = Decimal('0.00')
    total_accumulated_dep = Decimal('0.00')

    for asset in assets:
        book_value = Decimal(str(compute_asset_book_value(asset)))
        accumulated = Decimal(str(asset.amount)) - book_value
        years_used = date.today().year - int(asset.date_acquired)

        maintenance_total = AssetMaintenanceLog.objects.filter(
            asset=asset
        ).aggregate(total=Sum('cost'))['total'] or Decimal('0.00')

        entry = {
            'id': asset.id,
            'name': asset.name,
            'description': asset.description,
            'asset_type': asset.asset_types,
            'date_acquired': asset.date_acquired,
            'years_in_service': years_used,
            'original_cost': str(asset.amount),
            'residual_value': str(asset.residual_value),
            'useful_life_years': asset.useful_life,
            'remaining_life_years': max(asset.useful_life - years_used, 0),
            'valuation_method': asset.valuation_method,
            'is_appreciating': asset.is_appreciating,
            'current_book_value': str(round(book_value, 2)),
            'accumulated_depreciation': str(round(accumulated, 2)),
            'total_maintenance_cost': str(maintenance_total),
            'annual_maintenance_cost': str(asset.annual_maintenance_cost),
            'status': (
                'Fully Depreciated' if book_value <= asset.residual_value
                else 'Active'
            ),
        }

        register.append(entry)
        total_cost += asset.amount
        total_book_value += book_value
        total_accumulated_dep += accumulated

    return {
        'as_of_date': str(date.today()),
        'total_assets': len(register),
        'total_original_cost': str(total_cost),
        'total_book_value': str(round(total_book_value, 2)),
        'total_accumulated_depreciation': str(round(total_accumulated_dep, 2)),
        'assets': register,
    }
