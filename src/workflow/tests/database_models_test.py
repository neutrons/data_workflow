from workflow.database.report.models import (
    DataRun,
    InstrumentManager,
    DataRunManager,
    WorkflowSummary,
)

import unittest.mock as mock
import unittest


class TestModelsInstrumentManager(unittest.TestCase):
    @mock.patch("django.db.models.Manager.get_queryset")
    def test_sql_dump(self, managerQuerySetMock):
        itemMock = mock.Mock()
        itemMock.id = 2
        itemMock.name = "mock_name"

        managerQuerySetMock.return_value = [itemMock]
        instrumentManager = InstrumentManager()

        self.assertEqual(
            "INSERT INTO report_instrument(id, name) VALUES ("
            + str(itemMock.id)  # noqa: W503
            + ", '"  # noqa: W503
            + itemMock.name  # noqa: W503
            + "');\nSELECT pg_catalog.setval('report_instrument_id_seq', "  # noqa: W503
            + str(itemMock.id)  # noqa: W503
            + ", true);\n",  # noqa: W503
            instrumentManager.sql_dump(),
        )


class TestModelsDataRunManager(unittest.TestCase):
    @mock.patch("django.db.models.Manager.get_queryset")
    def test_filter_with_both_ids(self, managerQuerySetMock):
        filterMock = mock.MagicMock()
        managerQuerySetMock.return_value = filterMock
        filterMock.filter = mock.MagicMock()

        dataRunManager = DataRunManager()
        self.assertIsNone(dataRunManager.get_last_run(instrument_id=1, ipts_id=1))
        filterMock.filter.assert_called_with(instrument_id=1, ipts_id=1)

    @mock.patch("django.db.models.Manager.get_queryset")
    def test_filter_with_one_id(self, managerQuerySetMock):
        filterMock = mock.MagicMock()
        managerQuerySetMock.return_value = filterMock
        filterMock.filter = mock.MagicMock()

        dataRunManager = DataRunManager()
        self.assertIsNone(dataRunManager.get_last_run(instrument_id=1))
        filterMock.filter.assert_called_with(instrument_id=1)

    @mock.patch("django.db.models.Manager.get_queryset")
    def test_last_run_len_greaterthan_0(self, managerQuerySetMock):
        filterMock = mock.MagicMock()
        managerQuerySetMock.return_value = filterMock
        filterMock.filter = mock.MagicMock()
        filterMock.filter.return_value = mock.MagicMock()
        filterMock.filter.return_value.__len__.return_value = 1

        dataRunManager = DataRunManager()
        self.assertIsNotNone(dataRunManager.get_last_run(instrument_id=1))
        filterMock.filter.assert_called_with(instrument_id=1)

    @mock.patch("workflow.database.report.models.InstrumentStatus.objects")
    def test_last_cached_run(self, instrumentStatusObjectsMock):
        mockStatus = mock.MagicMock()
        mockStatus.last_run_id = 1
        instrumentStatusObjectsMock.get.return_value = mockStatus
        dataRunManager = DataRunManager()
        self.assertEqual(dataRunManager.get_last_cached_run(instrument_id=1), 1)

    @mock.patch("workflow.database.report.models.DataRun.objects")
    @mock.patch("workflow.database.report.models.InstrumentStatus.save")
    @mock.patch("workflow.database.report.models.InstrumentStatus")
    @mock.patch("workflow.database.report.models.InstrumentStatus.objects")
    def test_last_cached_run_exception(
        self,
        instrumentStatusObjectsMock,
        instrumentStatusMock,
        instrumentStatusSaveMock,
        datarunObjectsMock,
    ):
        mockStatus = mock.MagicMock()
        mockStatus.last_run_id = 1
        instrumentStatusInstanceMock = mock.MagicMock()
        instrumentStatusMock.return_value = instrumentStatusInstanceMock
        instrumentStatusInstanceMock.save = instrumentStatusSaveMock

        instrumentStatusObjectsMock.save = instrumentStatusSaveMock
        instrumentStatusMock.objects = instrumentStatusObjectsMock
        instrumentStatusObjectsMock.get.side_effect = Exception("Boom!")

        datarunObjectsMock.get_last_run.return_value = 1

        dataRunManager = DataRunManager()
        dataRunManager.get_last_cached_run(instrument_id=1)
        datarunObjectsMock.get_last_run.assert_called()
        instrumentStatusSaveMock.assert_called()


class TestModelsWorkflowSummary(unittest.TestCase):
    @mock.patch("django.db.models")
    @mock.patch("workflow.database.report.models.RunStatus.objects")
    def test_update_catalog(self, runStatusObjectsMock, djangoModelsMock):
        djangoModelsMock.ForeignKey = mock.MagicMock()
        workflowSummary = WorkflowSummary()
        workflowSummary.save = mock.MagicMock()
        workflowSummary.run_id = DataRun()

        def status_lookup(run_id, param_string):
            vals = {
                "CATALOG.COMPLETE": 1,
                "CATALOG.STARTED": 0,
                "REDUCTION.NOT_NEEDED": 0,
                "REDUCTION.DISABLED": 0,
                "REDUCTION.COMPLETE": 0,
                "REDUCTION.STARTED": 0,
                "REDUCTION_CATALOG.COMPLETE": 0,
                "REDUCTION_CATALOG.STARTED": 0,
            }

            lenMock = mock.MagicMock()
            lenMock.__len__.return_value = vals[param_string]
            return lenMock

        runStatusObjectsMock.status.side_effect = status_lookup
        workflowSummary.update()
        self.assertTrue(workflowSummary.cataloged)
        self.assertFalse(workflowSummary.catalog_started)

    @mock.patch("django.db.models")
    @mock.patch("workflow.database.report.models.RunStatus.objects")
    def test_update_reduction_need(self, runStatusObjectsMock, djangoModelsMock):
        djangoModelsMock.ForeignKey = mock.MagicMock()
        workflowSummary = WorkflowSummary()
        workflowSummary.save = mock.MagicMock()
        workflowSummary.run_id = DataRun()

        def status_lookup(run_id, param_string):
            vals = {
                "CATALOG.COMPLETE": 0,
                "CATALOG.STARTED": 0,
                "REDUCTION.NOT_NEEDED": 1,
                "REDUCTION.DISABLED": 1,
                "REDUCTION.COMPLETE": 0,
                "REDUCTION.STARTED": 0,
                "REDUCTION_CATALOG.COMPLETE": 0,
                "REDUCTION_CATALOG.STARTED": 0,
            }

            lenMock = mock.MagicMock()
            lenMock.__len__.return_value = vals[param_string]
            return lenMock

        runStatusObjectsMock.status.side_effect = status_lookup
        workflowSummary.update()
        self.assertFalse(workflowSummary.reduction_needed)

    @mock.patch("django.db.models")
    @mock.patch("workflow.database.report.models.RunStatus.objects")
    def test_update_reduction_status(self, runStatusObjectsMock, djangoModelsMock):
        djangoModelsMock.ForeignKey = mock.MagicMock()
        workflowSummary = WorkflowSummary()
        workflowSummary.save = mock.MagicMock()
        workflowSummary.run_id = DataRun()

        def status_lookup(run_id, param_string):
            vals = {
                "CATALOG.COMPLETE": 0,
                "CATALOG.STARTED": 0,
                "REDUCTION.NOT_NEEDED": 0,
                "REDUCTION.DISABLED": 0,
                "REDUCTION.COMPLETE": 1,
                "REDUCTION.STARTED": 1,
                "REDUCTION_CATALOG.COMPLETE": 0,
                "REDUCTION_CATALOG.STARTED": 0,
            }

            lenMock = mock.MagicMock()
            lenMock.__len__.return_value = vals[param_string]
            return lenMock

        runStatusObjectsMock.status.side_effect = status_lookup
        workflowSummary.update()
        self.assertTrue(workflowSummary.reduced)
        self.assertTrue(workflowSummary.reduction_started)

    @mock.patch("django.db.models")
    @mock.patch("workflow.database.report.models.RunStatus.objects")
    def test_update_reduction_catalog(self, runStatusObjectsMock, djangoModelsMock):
        djangoModelsMock.ForeignKey = mock.MagicMock()
        workflowSummary = WorkflowSummary()
        workflowSummary.save = mock.MagicMock()
        workflowSummary.run_id = DataRun()

        def status_lookup(run_id, param_string):
            vals = {
                "CATALOG.COMPLETE": 0,
                "CATALOG.STARTED": 0,
                "REDUCTION.NOT_NEEDED": 0,
                "REDUCTION.DISABLED": 0,
                "REDUCTION.COMPLETE": 0,
                "REDUCTION.STARTED": 0,
                "REDUCTION_CATALOG.COMPLETE": 1,
                "REDUCTION_CATALOG.STARTED": 1,
            }

            lenMock = mock.MagicMock()
            lenMock.__len__.return_value = vals[param_string]
            return lenMock

        runStatusObjectsMock.status.side_effect = status_lookup
        workflowSummary.update()
        self.assertTrue(workflowSummary.reduction_cataloged)
        self.assertTrue(workflowSummary.reduction_catalog_started)

    @mock.patch("django.db.models")
    @mock.patch("workflow.database.report.models.RunStatus.objects")
    def test_update_overall(self, runStatusObjectsMock, djangoModelsMock):
        djangoModelsMock.ForeignKey = mock.MagicMock()
        workflowSummary = WorkflowSummary()
        workflowSummary.save = mock.MagicMock()
        workflowSummary.run_id = DataRun()

        def status_lookup(run_id, param_string):
            vals = {
                "CATALOG.COMPLETE": 1,
                "CATALOG.STARTED": 0,
                "REDUCTION.NOT_NEEDED": 1,
                "REDUCTION.DISABLED": 0,
                "REDUCTION.COMPLETE": 0,
                "REDUCTION.STARTED": 0,
                "REDUCTION_CATALOG.COMPLETE": 1,
                "REDUCTION_CATALOG.STARTED": 1,
            }

            lenMock = mock.MagicMock()
            lenMock.__len__.return_value = vals[param_string]
            return lenMock

        runStatusObjectsMock.status.side_effect = status_lookup
        workflowSummary.update()
        self.assertTrue(workflowSummary.complete)
