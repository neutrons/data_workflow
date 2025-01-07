"""
Test helper functions for interacting with the database
"""


def get_status_queue_id(db_connection, queue_name):
    """
    Return the id for the statusqueue for the provided name

    :param psycopg.Connection db_connection: database connection
    :param int run_id: ID of the run in table datarun
    :param str queue_name: status queue
    :return: int, ID of the status queue in table statusqueue
    """
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM report_statusqueue where name = %s;", (queue_name,))
    queue_id = cursor.fetchone()

    if queue_id is None:
        cursor.execute(
            "INSERT INTO report_statusqueue (name, is_workflow_input) VALUES (%s, %s);", (queue_name, False)
        )
        cursor.execute("SELECT id FROM report_statusqueue where name = %s;", (queue_name,))
        queue_id = cursor.fetchone()
    cursor.close()

    return queue_id[0]


def check_run_status_exist(db_connection, run_id, queue_name):
    """
    Return if the run status was created for the given run_id and queue_name

    :param psycopg.Connection db_connection: database connection
    :param int run_id: ID of the run in table datarun
    :param str queue_name: status queue
    :return: bool
    """
    cursor = db_connection.cursor()
    queue_id = get_status_queue_id(db_connection, queue_name)
    cursor.execute("SELECT * FROM report_runstatus WHERE run_id_id = %s AND queue_id_id = %s", (run_id, queue_id))
    result = cursor.fetchone() is not None
    cursor.close()
    return result


def clear_previous_runstatus(db_connection, run_id):
    """
    Remove all previous run statuses for the given run_id

    :param psycopg.Connection db_connection: database connection
    :param tuple(int,) run_id: ID of the run in table datarun
    """
    cursor = db_connection.cursor()
    # delete run from tables report_information, report_error and report_runstatus
    cursor.execute(
        "DELETE FROM report_error WHERE run_status_id_id IN (SELECT id FROM report_runstatus "
        "WHERE run_id_id = %s);",
        (run_id,),
    )
    cursor.execute(
        "DELETE FROM report_information WHERE run_status_id_id IN (SELECT id FROM report_runstatus "
        "WHERE run_id_id = %s);",
        (run_id,),
    )
    cursor.execute("DELETE FROM report_runstatus WHERE run_id_id = %s;", (run_id,))
    db_connection.commit()
    cursor.close()


def add_instrument_data_run(conn, instrument, ipts, run_number, facility="SNS"):
    """
    Create the instrument, ipts and datarun if they don't already exist

    Returns the id for the created rundata

    :param psycopg.Connection conn: database connection
    :param str instrument: instrument
    :param str ipts: IPTS identifier, e.g. "IPTS-1234"
    :param int run_number: run number
    :param str facility: facility (SNS or HFIR)
    :return: int, ID of the run in table datarun
    """
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM report_instrument where name = %s;", (instrument,))
    inst_id = cursor.fetchone()

    if inst_id is None:
        cursor.execute("INSERT INTO report_instrument (name) VALUES (%s);", (instrument,))
        cursor.execute("SELECT id FROM report_instrument where name = %s;", (instrument,))
        inst_id = cursor.fetchone()
        conn.commit()

    cursor.execute("SELECT id FROM report_ipts WHERE expt_name = %s;", (ipts,))
    ipts_id = cursor.fetchone()
    if ipts_id is None:
        cursor.execute(
            "INSERT INTO report_ipts (expt_name, created_on) VALUES (%s, %s);",
            (ipts, "2020-05-20 13:02:52.281964;"),
        )
        cursor.execute("SELECT id FROM report_ipts WHERE expt_name = %s;", (ipts,))
        ipts_id = cursor.fetchone()
        conn.commit()

    cursor.execute(
        "SELECT id FROM report_datarun WHERE run_number = %s AND ipts_id_id = %s AND instrument_id_id = %s;",
        (run_number, ipts_id[0], inst_id[0]),
    )
    run_id = cursor.fetchone()
    if run_id is None:
        cursor.execute(
            "INSERT INTO report_datarun (run_number, ipts_id_id, instrument_id_id, file, created_on) "
            "VALUES (%s, %s, %s, %s, %s);",
            (
                run_number,
                ipts_id[0],
                inst_id[0],
                f"/{facility}/{instrument.upper()}/{ipts}/nexus/{instrument.upper()}_{run_number}.nxs.h5",
                "2020-05-20 13:02:52.281964;",
            ),
        )
        cursor.execute(
            "SELECT id FROM report_datarun WHERE run_number = %s AND ipts_id_id = %s AND instrument_id_id = %s;",
            (run_number, ipts_id[0], inst_id[0]),
        )
        run_id = cursor.fetchone()
        conn.commit()
    cursor.close()

    return run_id[0]


def check_error_msg_contains(conn, run_id, error_msg):
    """
    Return if there is an error record for the run that contains error_msg in description

    :param psycopg.Connection conn: database connection
    :param int run_id: ID of the run in table datarun
    :param str error_msg: error msg to check for
    :return: bool
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM report_error WHERE run_status_id_id IN (SELECT id FROM report_runstatus "
        "WHERE run_id_id = %s) AND description LIKE %s;",
        (run_id, f"%{error_msg}%"),  # surround err_msg by percentage signs for wildcard
    )
    result = cursor.fetchone() is not None
    cursor.close()
    return result
