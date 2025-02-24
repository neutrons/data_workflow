import psycopg.errors as pge
import psycopg
import argparse
import os
import unittest


class TestSetInstrumentPVs(unittest.TestCase):
    @classmethod
    def setUp(cls):
        options = cls.getSettings()
        cls.conn = cls.get_db_conn(options)
        cls.ids = cls.insert_test_data()

    @classmethod
    def get_db_conn(cls, options):
        conn = psycopg.connect(
            dbname=options.database,
            user=options.user,
            password=options.password,
            host=options.host,
            port=options.port,
        )
        return conn

    @classmethod
    def getSettings(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument("--user", dest="user", default=os.getenv("DATABASE_USER", "workflow"))
        parser.add_argument("--password", dest="password", default=os.getenv("DATABASE_PASS", "workflow"))
        parser.add_argument("--host", dest="host", default=os.getenv("DATABASE_HOST", "localhost"))
        parser.add_argument("--port", dest="port", default=os.getenv("DATABASE_PORT", "5432"))
        parser.add_argument("--database-name", dest="database", default=os.getenv("DATABASE_NAME", "workflow"))
        options = parser.parse_args(args="")
        return options

    @classmethod
    def insert_test_data(cls):
        instrument = "inst1"
        pvs = ["pv1", "pv2", "pv3"]
        clean_pv_ids = []
        cursor = cls.conn.cursor()
        cursor.execute("INSERT INTO report_instrument (name) VALUES (%s);", (instrument,))
        cursor.execute("SELECT id FROM report_instrument where name = %s;", (instrument,))
        inst_id = cursor.fetchone()[0]
        for pv in pvs:
            cursor.execute("INSERT INTO pvmon_pvname (name, monitored) VALUES (%s, %s);", (pv, "t"))
        cursor.execute("SELECT id FROM pvmon_pvname where name = ANY(%s);", (pvs,))
        pv_ids = cursor.fetchall()
        for each in pv_ids:
            cursor.execute(
                "INSERT INTO pvmon_pv (instrument_id, name_id, value, status, update_time) VALUES (%s, %s, 0.0, 0, 0);",
                (inst_id, each[0]),
            )
            clean_pv_ids.append((inst_id, each[0]))

        return clean_pv_ids

    @classmethod
    def tearDown(cls):
        cls.conn.rollback()

    def test_monitor_some(self):
        test_instrument = "inst1"
        test_pvs = ["pv1", "pv2"]
        expected_values = [self.ids[0], self.ids[1]]

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT setInstrumentPVs('{}'::character varying, ARRAY[{}])".format(
                test_instrument, ",".join(f"'{pv}'" for pv in test_pvs)
            )
        )
        cursor.execute("SELECT instrument_id, pv_name_id FROM pvmon_monitoredvariable;")
        result = cursor.fetchall()
        self.assertListEqual(expected_values, result)

    def test_monitor_all(self):
        test_instrument = "inst1"
        test_pvs = ["pv1", "pv2", "pv3"]
        expected_values = self.ids

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT setInstrumentPVs('{}'::character varying, ARRAY[{}])".format(
                test_instrument, ",".join(f"'{pv}'" for pv in test_pvs)
            )
        )
        cursor.execute("SELECT instrument_id, pv_name_id FROM pvmon_monitoredvariable;")
        result = cursor.fetchall()
        self.assertListEqual(expected_values, result)

    def test_monitor_none(self):
        test_instrument = "inst1"
        expected_values = [(self.ids[0][0], None)]

        cursor = self.conn.cursor()

        cursor.execute("SELECT setInstrumentPVs('{}'::character varying, ARRAY[]::text[])".format(test_instrument))
        cursor.execute("SELECT instrument_id, pv_name_id FROM pvmon_monitoredvariable;")
        result = cursor.fetchall()
        self.assertListEqual(expected_values, result)

    def test_monitor_pv_does_not_exist(self):
        test_instrument = "inst1"
        test_pvs = ["pv1", "pv3", "pv5"]
        expected_values = [self.ids[0], self.ids[2]]

        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT setInstrumentPVs('{}'::character varying, ARRAY[{}])".format(
                test_instrument, ",".join(f"'{pv}'" for pv in test_pvs)
            )
        )
        cursor.execute("SELECT instrument_id, pv_name_id FROM pvmon_monitoredvariable;")
        result = cursor.fetchall()
        self.assertListEqual(expected_values, result)

    def test_monitor_instrument_does_not_exist(self):
        test_instrument = "inst2"
        test_pvs = ["pv1", "pv2"]

        cursor = self.conn.cursor()
        with self.assertRaises(pge.RaiseException):
            cursor.execute(
                "SELECT setInstrumentPVs('{}'::character varying, ARRAY[{}])".format(
                    test_instrument, ",".join(f"'{pv}'" for pv in test_pvs)
                )
            )
