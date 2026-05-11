"""
Django management command to backfill run_title field for existing DataRun records
"""

import logging

from django.core.management.base import BaseCommand

from reporting.dasmon.models import Parameter
from reporting.report.models import DataRun, Instrument

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill run_title field for existing DataRun records from StatusCache"

    def add_arguments(self, parser):
        parser.add_argument(
            "--instrument",
            type=str,
            help="Only process runs for this instrument (optional)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of runs to process (optional)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )

    def handle(self, *args, **options):
        instrument_name = options.get("instrument")
        limit = options.get("limit")
        dry_run = options.get("dry_run", False)

        # Build query for DataRun records without run_title
        query = DataRun.objects.filter(run_title__isnull=True)

        if instrument_name:
            try:
                instrument = Instrument.objects.get(name=instrument_name.lower())
                query = query.filter(instrument_id=instrument)
                self.stdout.write(f"Filtering for instrument: {instrument_name}")
            except Instrument.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Instrument '{instrument_name}' not found"))
                return

        if limit:
            query = query[:limit]
            self.stdout.write(f"Limiting to {limit} runs")

        total_runs = query.count()
        self.stdout.write(f"Found {total_runs} runs without run_title")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        updated_count = 0
        not_found_count = 0

        try:
            # Get the run_title parameter
            run_title_param = Parameter.objects.get(name="run_title")
        except Parameter.DoesNotExist:
            self.stdout.write(self.style.ERROR("Parameter 'run_title' not found in database"))
            return

        for data_run in query:
            try:
                # Look up run_title from StatusCache
                # We need to find the status cache entry that matches this instrument and run
                # StatusCache stores the latest value per parameter per instrument
                # We need to query StatusVariable (historical data) to find run_title at the time of this run

                # For simplicity, we'll look for any run_title in StatusVariable for this instrument
                # around the time this DataRun was created
                # Look for run_title status variables for this instrument near the run creation time
                # within a 24-hour window
                from datetime import timedelta

                from reporting.dasmon.models import StatusVariable

                time_window_start = data_run.created_on - timedelta(hours=1)
                time_window_end = data_run.created_on + timedelta(hours=1)

                status_vars = StatusVariable.objects.filter(
                    instrument_id=data_run.instrument_id,
                    key_id=run_title_param,
                    timestamp__gte=time_window_start,
                    timestamp__lte=time_window_end,
                ).order_by("timestamp")

                # Also need to find run_number to match
                try:
                    run_number_param = Parameter.objects.get(name="run_number")

                    # Find run_number status variables in the same time window
                    run_number_vars = StatusVariable.objects.filter(
                        instrument_id=data_run.instrument_id,
                        key_id=run_number_param,
                        timestamp__gte=time_window_start,
                        timestamp__lte=time_window_end,
                    ).order_by("timestamp")

                    # Match run_title with run_number
                    run_title = None
                    for run_num_var in run_number_vars:
                        try:
                            if int(run_num_var.value) == data_run.run_number:
                                # Find the closest run_title in time
                                for title_var in status_vars:
                                    if (
                                        abs((title_var.timestamp - run_num_var.timestamp).total_seconds()) < 300
                                    ):  # within 5 minutes
                                        run_title = title_var.value
                                        break
                                if run_title:
                                    break
                        except ValueError:
                            continue

                    if run_title:
                        if not dry_run:
                            data_run.run_title = run_title
                            data_run.save()

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"{'[DRY RUN] Would update' if dry_run else 'Updated'} "
                                f"{data_run.instrument_id} run {data_run.run_number}: {run_title[:50]}"
                            )
                        )
                        updated_count += 1
                    else:
                        not_found_count += 1
                        if options.get("verbosity", 1) > 1:
                            self.stdout.write(
                                f"No run_title found for {data_run.instrument_id} run {data_run.run_number}"
                            )

                except Parameter.DoesNotExist:
                    not_found_count += 1
                    if options.get("verbosity", 1) > 1:
                        self.stdout.write("No run_number parameter found")

            except Exception as e:
                logger.exception(f"Error processing run {data_run.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"Error processing {data_run.instrument_id} run {data_run.run_number}: {e}")
                )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Total runs processed: {total_runs}")
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
        self.stdout.write(f"Not found: {not_found_count}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No actual changes were made"))
