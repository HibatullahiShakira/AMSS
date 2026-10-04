"""
Management command to fetch Nigerian macro-economic data from the World Bank API.

Usage:
    python manage.py fetch_macro_data          # Fetch latest available data
    python manage.py fetch_macro_data --year 2024  # Fetch specific year

World Bank API indicators used:
- FP.CPI.TOTL.ZG: Inflation, consumer prices (annual %)
- FR.INR.DPST: Deposit interest rate (%)
- FR.INR.LEND: Lending interest rate (%)
- PA.NUS.FCRF: Official exchange rate (LCU per US$, period average)
- NY.GDP.MKTP.KD.ZG: GDP growth (annual %)
- FR.INR.RINR: Real interest rate (%)

The command fetches data and creates/updates a MacroSnapshot.
"""

import json
import urllib.request
import urllib.error
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from decimal import Decimal

from finance.models_uncertainty import MacroSnapshot, MacroDataLog


# World Bank API v2 indicators for Nigeria (country code: NGA)
WORLD_BANK_INDICATORS = {
    'FP.CPI.TOTL.ZG': 'inflation_rate',
    'FR.INR.DPST': 'savings_deposit_rate',
    'FR.INR.LEND': 'prime_lending_rate',
    'PA.NUS.FCRF': 'fx_rate_usd_ngn',
    'NY.GDP.MKTP.KD.ZG': 'gdp_growth_rate',
    'FR.INR.RINR': 'real_interest_rate',
}

WORLD_BANK_API_BASE = 'https://api.worldbank.org/v2/country/NGA/indicator'


def fetch_indicator(indicator_code, year=None):
    """
    Fetch a single indicator from the World Bank API.

    Returns the most recent available value.
    """
    date_param = f'{year}:{year}' if year else 'date=2020:2026'
    url = (
        f"{WORLD_BANK_API_BASE}/{indicator_code}"
        f"?format=json&per_page=10&date={date_param}"
    )

    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        if len(data) < 2 or data[1] is None:
            return None

        # Find the most recent non-null value
        for entry in data[1]:
            if entry.get('value') is not None:
                return {
                    'value': entry['value'],
                    'year': entry['date'],
                    'indicator': indicator_code,
                }

        return None

    except (urllib.error.URLError, json.JSONDecodeError, IndexError) as e:
        return {'error': str(e), 'indicator': indicator_code}


class Command(BaseCommand):
    help = 'Fetch Nigerian macro-economic data from the World Bank API and update MacroSnapshot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Specific year to fetch data for (default: most recent)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch and display data without saving to database',
        )

    def handle(self, *args, **options):
        year = options.get('year')
        dry_run = options.get('dry_run', False)

        self.stdout.write(
            self.style.NOTICE(
                f"\n{'='*60}\n"
                f"  AMSS Enterprise — Macro Data Fetcher\n"
                f"  Source: World Bank API\n"
                f"  Country: Nigeria (NGA)\n"
                f"  Year: {year or 'Most recent available'}\n"
                f"{'='*60}\n"
            )
        )

        fetched_data = {}
        errors = []
        indicators_fetched = 0

        for indicator_code, field_name in WORLD_BANK_INDICATORS.items():
            self.stdout.write(f"  Fetching {indicator_code} ({field_name})...")

            result = fetch_indicator(indicator_code, year)

            if result and 'error' not in result:
                fetched_data[field_name] = {
                    'value': result['value'],
                    'year': result['year'],
                }
                indicators_fetched += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    ✓ {field_name}: {result['value']:.2f} "
                        f"(Year: {result['year']})"
                    )
                )
            elif result and 'error' in result:
                errors.append(f"{field_name}: {result['error']}")
                self.stdout.write(
                    self.style.ERROR(f"    ✗ {field_name}: {result['error']}")
                )
            else:
                errors.append(f"{field_name}: No data available")
                self.stdout.write(
                    self.style.WARNING(f"    ⚠ {field_name}: No data available")
                )

        self.stdout.write(f"\n{'─'*60}")
        self.stdout.write(
            f"  Fetched: {indicators_fetched}/{len(WORLD_BANK_INDICATORS)} indicators"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("\n  DRY RUN — no data saved.\n"))
            # Log the attempt
            MacroDataLog.objects.create(
                source=MacroSnapshot.DataSource.WORLD_BANK,
                status=MacroDataLog.Status.SUCCESS if not errors else MacroDataLog.Status.PARTIAL,
                indicators_fetched=indicators_fetched,
                error_message='; '.join(errors) if errors else '',
                response_data=fetched_data,
            )
            return

        if indicators_fetched == 0:
            MacroDataLog.objects.create(
                source=MacroSnapshot.DataSource.WORLD_BANK,
                status=MacroDataLog.Status.FAILED,
                indicators_fetched=0,
                error_message='; '.join(errors),
            )
            raise CommandError(
                'No data was fetched. Check your internet connection '
                'and the World Bank API status.'
            )

        # Build the macro snapshot
        snapshot_data = {
            'effective_date': date.today(),
            'source': MacroSnapshot.DataSource.WORLD_BANK,
            'is_current': True,
            'notes': (
                f"Auto-fetched from World Bank API. "
                f"{indicators_fetched} indicators updated."
            ),
        }

        # Map fetched values to snapshot fields
        if 'inflation_rate' in fetched_data:
            snapshot_data['inflation_rate'] = Decimal(
                str(round(fetched_data['inflation_rate']['value'], 2))
            )
            # Estimate monthly from annual
            annual = fetched_data['inflation_rate']['value']
            monthly = ((1 + annual / 100) ** (1/12) - 1) * 100
            snapshot_data['inflation_rate_monthly'] = Decimal(
                str(round(monthly, 2))
            )

        if 'prime_lending_rate' in fetched_data:
            snapshot_data['prime_lending_rate'] = Decimal(
                str(round(fetched_data['prime_lending_rate']['value'], 2))
            )

        if 'savings_deposit_rate' in fetched_data:
            snapshot_data['savings_deposit_rate'] = Decimal(
                str(round(fetched_data['savings_deposit_rate']['value'], 2))
            )

        if 'fx_rate_usd_ngn' in fetched_data:
            snapshot_data['fx_rate_usd_ngn'] = Decimal(
                str(round(fetched_data['fx_rate_usd_ngn']['value'], 2))
            )

        if 'gdp_growth_rate' in fetched_data:
            snapshot_data['gdp_growth_rate'] = Decimal(
                str(round(fetched_data['gdp_growth_rate']['value'], 2))
            )

        # Create the snapshot
        snapshot = MacroSnapshot.objects.create(**snapshot_data)

        # Log success
        MacroDataLog.objects.create(
            source=MacroSnapshot.DataSource.WORLD_BANK,
            status=(
                MacroDataLog.Status.SUCCESS
                if not errors
                else MacroDataLog.Status.PARTIAL
            ),
            indicators_fetched=indicators_fetched,
            error_message='; '.join(errors) if errors else '',
            response_data=fetched_data,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n  ✓ MacroSnapshot created (ID: {snapshot.pk})\n"
                f"  ✓ Effective date: {snapshot.effective_date}\n"
                f"  ✓ MPR: {snapshot.cbn_monetary_policy_rate}%\n"
                f"  ✓ Inflation: {snapshot.inflation_rate}%\n"
                f"  ✓ FX Rate: ₦{snapshot.fx_rate_usd_ngn}/USD\n"
            )
        )
