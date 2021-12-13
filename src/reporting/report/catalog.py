# pylint: disable=bare-except, invalid-name, too-many-nested-blocks, too-many-locals, too-many-branches, line-too-long
"""
    Optional utilities to communicate with ONcat.
    ONcat is an online data catalog used internally at ORNL.

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2018 Oak Ridge National Laboratory
"""
import sys
import logging
try:
    import pyoncat
except:
    logging.error("No ONCat")
import datetime
from django.conf import settings


def decode_time(timestamp):
    """
        Decode timestamp and return a datetime object
        :param timestamp: timestamp to decode
    """
    try:
        tz_location = timestamp.rfind('+')
        if tz_location < 0:
            tz_location = timestamp.rfind('-')
        if tz_location > 0:
            date_time_str = timestamp[:tz_location]
            # Get rid of fractions of a second
            sec_location = date_time_str.rfind('.')
            if sec_location > 0:
                date_time_str = date_time_str[:sec_location]
            return datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S")
    except:
        logging.error("Could not parse timestamp '%s': %s", timestamp, sys.exc_info()[1])
        return None


def get_run_info(instrument, ipts, run_number):
    """
        Legacy issue:
        Until the facility information is stored in the DB so that we can
        retrieve the facility from it, we'll have to use the application
        configuration.
        :param str instrument: instrument short name
        :param str ipts: experiment name
        :param str run_number: run number
        :param str facility: facility name (SNS or HFIR)
    """
    facility = 'SNS'
    if hasattr(settings, 'FACILITY_INFO'):
        facility = settings.FACILITY_INFO.get(instrument, 'SNS')
    return _get_run_info(instrument, ipts, run_number, facility)


def _get_run_info(instrument, ipts, run_number, facility='SNS'):
    """
        Get ONCat info for the specified run
        Notes: At the moment we do not catalog reduced data
        :param str instrument: instrument short name
        :param str ipts: experiment name
        :param str run_number: run number
        :param str facility: facility name (SNS or HFIR)
    """
    run_info = {}
    try:
        oncat = pyoncat.ONCat(
            settings.CATALOG_URL,
            # Here we're using the machine-to-machine "Client Credentials" flow,
            # which requires a client ID and secret, but no *user* credentials.
            flow=pyoncat.CLIENT_CREDENTIALS_FLOW,
            client_id=settings.CATALOG_ID,
            client_secret=settings.CATALOG_SECRET,
        )
        oncat.login()

        datafiles = oncat.Datafile.list(
            facility=facility,
            instrument=instrument.upper(),

            # Specifying the exact IPTS that contains the runs you need is optional,
            # but you should provide one if that information is available -- this will
            # mean ONCat can respond quicker because it has to look in fewer places.
            experiment=ipts,

            # We are only interested in the location of "raw" .nxs.h5 files.
            projection=['experiment', 'location',
                        'metadata.entry.title',
                        'metadata.entry.duration',
                        'metadata.entry.total_counts',
                        'metadata.entry.proton_charge',
                        'metadata.entry.start_time',
                        'metadata.entry.end_time',
                        ],
            tags=['type/raw'],
            # exts = ['.nxs.h5'],

            # Specify the list of ranges of run numbers we want.
            ranges_q='indexed.run_number:%s' % str(run_number)
        )

        run_info['data_files'] = []
        for datafile in datafiles:
            run_info['data_files'].append(datafile.location)
            if datafile.location.endswith('.nxs.h5'):
                run_info['title'] = datafile.metadata.get('entry', {}).get('title', None)
                run_info['proposal'] = datafile.experiment
                run_info['duration'] = datafile.metadata.get('entry', {}).get('duration', None)
                run_info['totalCounts'] = datafile.metadata.get('entry', {}).get('total_counts', None)
                run_info['protonCharge'] = datafile.metadata.get('entry', {}).get('proton_charge', None)
                run_info['startTime'] = decode_time(datafile.metadata.get('entry', {}).get('start_time', None))
                run_info['endTime'] = decode_time(datafile.metadata.get('entry', {}).get('end_time', None))
    except:
        logging.error("Communication with ONCat server failed: %s", sys.exc_info()[1])

    return run_info
