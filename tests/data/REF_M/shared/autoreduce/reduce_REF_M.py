#!/usr/bin/env python
"""Templated autoreduction script for REF_M"""
# standard imports
import argparse
from collections import namedtuple
import logging
import os
import re
import sys
import warnings

# third-party imports
from mr_reduction.mr_reduction import ReductionProcess
from mr_reduction.web_report import upload_html_report

warnings.simplefilter("ignore")
CONDA_ENV = "mr_reduction"


class ContextFilter(logging.Filter):
    """Simple log filter to take out non-Mantid logs from .err file"""

    def filter(self, record):
        filtered_logs = ["Optimal parameters not found"]
        msg = record.getMessage()
        if record.levelname == "WARNING":
            return 0
        for item in filtered_logs:
            if item in msg:
                return 0
        return 1


logger = logging.getLogger()
f = ContextFilter()
logger.addFilter(f)


def _as_bool(value):
    r"""Cast a string to bool"""
    if isinstance(value, str):
        if value.lower() == "false":
            return False
    return bool(value)


def reduction_user_options():
    r"""Collects all values defined by the user in https://monitor.sns.gov/reduction/ref_m/"""
    # Options common to all samples:
    kwargs_common = dict(
        plot_2d=_as_bool(True),
        const_q_binning=_as_bool(False),
        q_step=float(-0.02),
        use_sangle=_as_bool(True),
        update_peak_range=_as_bool(True),
        publish=False,  # uploading to livedata server to be done later by `upload_html_report()`
    )

    # Options for Sample 1
    kwargs_sample_1 = dict(
        use_roi=True,
        force_peak_roi=_as_bool(True),
        peak_roi=[int(149), int(159)],
        use_roi_bck=False,
        force_bck_roi=_as_bool(True),
        bck_roi=[int(28), int(80)],
        use_tight_bck=False,
        bck_offset=int(),
    )

    # Options for Sample 2
    kwargs_sample_2 = dict(
        use_roi=True,
        force_peak_roi=_as_bool(True),
        peak_roi=[int(160), int(180)],
        use_roi_bck=False,
        force_bck_roi=_as_bool(True),
        bck_roi=[int(30), int(70)],
        use_tight_bck=_as_bool(False),
        bck_offset=int(),
    )

    # Options for Sample 3
    kwargs_sample_3 = dict(
        use_roi=True,
        force_peak_roi=_as_bool(True),
        peak_roi=[int(160), int(180)],
        use_roi_bck=False,
        force_bck_roi=_as_bool(True),
        bck_roi=[int(30), int(70)],
        use_tight_bck=_as_bool(False),
        bck_offset=int(),
    )

    # Do we have more than one sample in this run?
    sample_count = int(1)
    ReductionOptions = namedtuple("ReductionOptions", "common, sample_count, sample1, sample2, sample3")
    return ReductionOptions(kwargs_common, sample_count, kwargs_sample_1, kwargs_sample_2, kwargs_sample_3)


def reduce_events_file(event_file_path, outdir):
    event_file = os.path.split(event_file_path)[-1]  # file name
    reports = list()  # autoreduction reports for each sample in the run, in HTML format
    opts = reduction_user_options()
    assert opts.sample_count <= 3, "Sample count must be <= 3"
    kwargs_samples = [opts.sample1, opts.sample2, opts.sample3]
    sample_numbers = (
        [
            None,
        ]
        if opts.sample_count == 1
        else range(1, opts.sample_count + 1)
    )  # numbers start at 1, not 0
    for i, sample_number in enumerate(sample_numbers):
        d = dict(data_run=event_file, output_dir=outdir, sample_number=sample_number)
        kwargs = {**d, **opts.common, **kwargs_samples[i]}  # merge all partial dicts
        reports.append(ReductionProcess(**kwargs).reduce())
    return reports


def parse_command_arguments():
    parser = argparse.ArgumentParser(description="Autoreduction script for REF_M")
    parser.add_argument("events_file", type=str, help="Path to the Nexus events file.")
    parser.add_argument("outdir", type=str, help="Output directory path.")
    parser.add_argument(
        "--report_file",
        type=str,
        help="Save the HTML report to file. If only the file name is given,"
        "the file is saved in the output directory",
    )
    parser.add_argument("--no_publish", action="store_true", help="Do not upload HTML report to the livedata server.")
    return parser.parse_args()


def main():
    r"""Autoreduce a single events file and upload the HTML report to the livedata server"""
    args = parse_command_arguments()
    reports = reduce_events_file(args.events_file, args.outdir)

    # If saving the report to file, find if we should save to the output directory
    file_path = args.report_file
    if file_path and os.path.basename(file_path) == file_path:
        file_path = os.path.join(args.outdir, file_path)
    run_number = re.search(r"REF_M_\d+", args.events_file).group(0)
    upload_html_report(reports, publish=(not args.no_publish), run_number=run_number, report_file=file_path)

    # Check if the auto-reduce data has been saved to the canonical IPTS-XXXXX/shared/autoreduce directory
    try:
        ipts = re.search(r"IPTS-\d+", args.events_file).group(0)  # extract 'IPTS-31954' from the events file
        ipts_number = ipts.split("-")[1]
        cmd = f"/SNS/software/nses/bin/confirm-data -s Yes BL-4A {ipts_number} 1 Auto"
        print(cmd)
        os.system(cmd)
    except:
        print("Could not set data availability")
        print(sys.exc_info()[1])


if __name__ == "__main__":
    main()
