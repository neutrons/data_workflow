# pylint: disable=too-many-locals, too-many-statements, bare-except, invalid-name
"""
    Perform DB transactions
"""
from django.db import transaction
import django
import six
import sys
import os
import json
import logging
import traceback
# The workflow modules must be on the python path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workflow.database.settings")
if django.VERSION[1] >= 7:
    django.setup()
    from workflow.database.report.models import DataRun, RunStatus, StatusQueue, WorkflowSummary
    from workflow.database.report.models import IPTS, Instrument, Error, Information, Task
else:
    # The report database module must be on the python path for Django to find it
    sys.path.append(os.path.dirname(__file__))

    # Import your models for use in your script
    from report.models import DataRun, RunStatus, StatusQueue, WorkflowSummary
    from report.models import IPTS, Instrument, Error, Information, Task


@transaction.atomic
def add_status_entry(headers, data):
    """
        Populate the reporting database with the contents
        of a status message of the following format:

        @param headers: ActiveMQ message header dictionary
        @param data: JSON encoded message content

        headers: {'expires': '0', 'timestamp': '1344613053723',
                  'destination': '/queue/POSTPROCESS.DATA_READY',
                  'persistent': 'true',
                  'priority': '5',
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}

        The data is a dictionary in a JSON format.

        data: {"instrument": tokens[2],
               "ipts": tokens[3],
               "run_number": run_number,
               "data_file": message}
    """
    # Find the DB entry for this queue
    destination = headers["destination"].replace('/queue/', '')
    status_id = StatusQueue.objects.filter(name__startswith=destination)
    if len(status_id) == 0:
        status_id = StatusQueue(name=destination)
        status_id.save()
    else:
        status_id = status_id[0]

    # Process the data
    data_dict = json.loads(data)

    # Look for instrument
    instrument = data_dict["instrument"].lower()
    try:
        instrument_id = Instrument.objects.get(name=instrument)
    except Instrument.DoesNotExist:
        instrument_id = Instrument(name=instrument)
        instrument_id.save()

    # Look for IPTS ID
    ipts = data_dict["ipts"].upper()
    try:
        ipts_id = IPTS.objects.get(expt_name=ipts)
    except IPTS.DoesNotExist:
        ipts_id = IPTS(expt_name=ipts)
        ipts_id.save()

    # Add instrument to IPTS if not already in there
    try:
        if IPTS.objects.filter(id=ipts_id.id, instruments__in=[instrument_id]).count() == 0:
            ipts_id.instruments.add(instrument_id)
            ipts_id.save()
    except:
        traceback.print_exc()
        logging.error(sys.exc_value)

    # Check whether we already have an entry for this run
    run_number = int(data_dict["run_number"])
    try:
        run_id = DataRun.objects.get(run_number=run_number, instrument_id=instrument_id)
        # Update the file location and IPTS as needed
        run_id.ipts_id = ipts_id
        if "data_file" in data_dict and len(data_dict["data_file"]) > 0:
            run_id.file = data_dict["data_file"]
        run_id.save()
    except DataRun.DoesNotExist:
        logging.info("Creating entry for run %s-%d", instrument, run_number)
        run_id = DataRun.create_and_save(run_number=run_number,
                                         instrument_id=instrument_id,
                                         ipts_id=ipts_id,
                                         file=data_dict["data_file"])

    # Add a workflow summary for this new run
    try:
        summary_id = WorkflowSummary.objects.get(run_id=run_id)
    except WorkflowSummary.DoesNotExist:
        summary_id = WorkflowSummary(run_id=run_id)
        summary_id.save()

    # Create a run status object in the DB
    run_status = RunStatus(run_id=run_id,
                           queue_id=status_id,
                           message_id=headers["message-id"])
    run_status.save()

    # Create an information entry as necessary
    # Truncate to max length of DB character field
    if "information" in data_dict:
        data = data_dict["information"]
        mesg = (data[:198] + '..') if len(data) > 200 else data
        info = Information(run_status_id=run_status,
                           description=mesg)
        info.save()

    # Create error entry as necessary
    if "error" in data_dict:
        data = data_dict["error"]
        mesg = (data[:198] + '..') if len(data) > 200 else data
        error = Error(run_status_id=run_status,
                      description=mesg)
        error.save()

    # Update the workflow summary
    summary_id = WorkflowSummary.objects.get_summary(run_id)
    if "is_complete" in data_dict:
        summary_id.complete = True
        summary_id.save()
    else:
        summary_id.update()


def add_workflow_status_entry(destination, message):
    """
        Add a database entry for an event generated by the workflow manager.
        This represents additional information regarding interventions by
        the workflow manager.
        @param destination: string representing the StatusQueue
        @param message: JSON encoded data dictionary
    """
    pass


def get_task(message_headers, message_data):
    """
        Find the DB entry for this queue
        @param headers: message headers
        @param message: JSON-encoded message content
    """
    if "destination" in message_headers:
        destination = message_headers["destination"].replace('/queue/', '')
        status_ids = StatusQueue.objects.filter(name__startswith=destination)
        if len(status_ids) > 0:
            status_id = status_ids[0]
    else:
        logging.error("transactions.get_task got badly formed message header")
        return None

    # Process the data
    try:
        data_dict = json.loads(message_data)
    except:
        logging.error("transactions.get_task expects JSON-encoded message: %s", sys.exc_value)
        return None

    # Look for instrument
    if "instrument" in data_dict:
        instrument = data_dict["instrument"].lower()
        try:
            instrument_id = Instrument.objects.get(name=instrument)
        except Instrument.DoesNotExist:
            logging.error("transactions.get_task could not find instrument entry")
            return None
    else:
        logging.error("transactions.get_task could not find instrument information")
        return None

    task_ids = Task.objects.filter(instrument_id=instrument_id, input_queue_id=status_id)
    if len(task_ids) == 1:
        return task_ids[0].json_encode()
    elif len(task_ids) > 1:
        logging.error("Sanity check problem: %s has more than one action for %s queue", instrument, destination)

    return None


def get_message_queues(only_workflow_inputs=True):
    """
        Get the list of message queues from the DB
        @param only_workflow_inputs: if True, only the queues that the workflow manager listens to will be returned
    """
    if only_workflow_inputs:
        queue_ids = StatusQueue.objects.filter(is_workflow_input=True)
    else:
        queue_ids = StatusQueue.objects.all()
    return [str(q) for q in queue_ids]


def _get_queue_ids(queue_list):
    queue_ids = []
    if isinstance(queue_list, list):
        for q in queue_list:
            q = str(q).strip().upper()
            # Find queue in DB
            try:
                q_id = StatusQueue.objects.get(name=q)
                queue_ids.append(q_id)
            except StatusQueue.DoesNotExist:
                logging.error("transactions.add_task could not find task queue %s" % q)
                return None
    elif queue_list is None:
        return []
    else:
        logging.error("transactions.add_task expects a list of queue names")
        return None
    return queue_ids


def add_task(instrument, input_queue, task_class='', task_queues=None, success_queues=None):
    """
        Add a task entry
    """
    # Find instrument
    try:
        instrument_id = Instrument.objects.get(name=instrument)
    except Instrument.DoesNotExist:
        logging.error("transactions.add_task could not find instrument entry")
        return

    # Find input queue
    try:
        input_id = StatusQueue.objects.get(name=input_queue.upper())
    except StatusQueue.DoesNotExist:
        logging.error("transactions.add_task could not find input queue")
        return

    # Find task queues
    if isinstance(task_queues, (six.string_types)):
        task_queues = [task_queues]
    task_queue_ids = _get_queue_ids(task_queues)
    if task_queue_ids is None:
        logging.error("transactions.add_task could not process task queues")
        return

    # Find success queues
    if isinstance(success_queues, (six.string_types)):
        success_queues = [success_queues]
    success_queue_ids = _get_queue_ids(success_queues)
    if success_queue_ids is None:
        logging.error("transactions.add_task could not process success queues")
        return

    # Sanity check
    if len(task_queue_ids) != len(success_queue_ids):
        logging.error("transactions.add_task expects the same number of tasks and success queues")
        return

    # Find whether it already exists
    try:
        task_id = Task.objects.get(instrument_id=instrument_id,
                                   input_queue_id=input_id)
    except Task.DoesNotExist:
        task_id = None

    if task_id is not None:
        task_id.task_class = str(task_class)
    else:
        task_id = Task(instrument_id=instrument_id,
                       input_queue_id=input_id,
                       task_class=str(task_class))
        task_id.save()

    task_id.task_queue_ids.clear()
    for q in task_queue_ids:
        task_id.task_queue_ids.add(q)

    task_id.success_queue_ids.clear()
    for q in success_queue_ids:
        task_id.success_queue_ids.add(q)
    task_id.save()


def sql_dump_tasks():
    """
        Dump the SQL necessary to insert the current task definitions
    """
    sql = ''
    sql += Instrument.objects.sql_dump()
    sql += '\n'
    sql += Task.objects.sql_dump()

    fd = open('task.sql', 'w')
    fd.write(sql)
    fd.close()

    print(sql)
