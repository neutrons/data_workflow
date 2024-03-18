"""
    Utilities common to the whole web application.

    @copyright: 2014 Oak Ridge National Laboratory
"""

from django.conf import settings
import logging


def send_activemq_message(destination, data):
    """
    Send an AMQ message to the workflow manager.

    :param destination: queue to send the request to
    :param data: JSON data payload for the message
    """
    import stomp

    conn = stomp.Connection(host_and_ports=settings.BROKERS)
    conn.connect(settings.ICAT_USER, settings.ICAT_PASSCODE, wait=True)
    conn.send(destination, data, persistent="true")
    conn.disconnect()


def reduction_setup_url(instrument):
    """
    Check whether the reduction app is installed, and if so
    return a URL for the reduction setup if it's enabled
    for the given instrument

    :param instrument: instrument name
    """
    try:
        if "reporting.reduction" in settings.INSTALLED_APPS:
            import reporting.reduction.view_util

            return reporting.reduction.view_util.reduction_setup_url(instrument)
    except:  # noqa: E722
        logging.exception("Error getting reduction setup url:")
    return None
