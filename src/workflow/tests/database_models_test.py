from workflow.database.report.models import InstrumentManager, DataRunManager

import unittest.mock as mock
import unittest


class TestModelsInstrumentManager(unittest.TestCase):

    @mock.patch('django.db.models.Manager.get_queryset')
    def test_sql_dump(self, managerQuerySetMock):
        itemMock = mock.Mock()
        itemMock.id = 2
        itemMock.name = 'mock_name'

        managerQuerySetMock.return_value = [itemMock]
        instrumentManager = InstrumentManager()

        self.assertEqual('INSERT INTO report_instrument(id, name) VALUES ('
        + str(itemMock.id)
        + ', \''
        + itemMock.name
        +'\');\nSELECT pg_catalog.setval(\'report_instrument_id_seq\', '
        + str(itemMock.id) 
        +', true);\n',
        instrumentManager.sql_dump())

class TestModelsDataRunManager(unittest.TestCase):

    @mock.patch('django.db.models.Manager.get_queryset')
    def test_filter_with_both_ids(self, managerQuerySetMock):
        filterMock = mock.MagicMock()
        managerQuerySetMock.return_value = filterMock
        filterMock.filter = mock.MagicMock()

        dataRunManager = DataRunManager()
        self.assertIsNone(dataRunManager.get_last_run(instrument_id=1, ipts_id=1))
        filterMock.filter.assert_called_with(instrument_id=1, ipts_id=1)

    @mock.patch('django.db.models.Manager.get_queryset')
    def test_filter_with_one_id(self, managerQuerySetMock):
        filterMock = mock.MagicMock()
        managerQuerySetMock.return_value = filterMock
        filterMock.filter = mock.MagicMock()

        dataRunManager = DataRunManager()
        self.assertIsNone(dataRunManager.get_last_run(instrument_id=1))
        filterMock.filter.assert_called_with(instrument_id=1)

    @mock.patch('django.db.models.Manager.get_queryset')
    def test_last_run_len_greaterthan_0(self, managerQuerySetMock):
        filterMock = mock.MagicMock()
        managerQuerySetMock.return_value = filterMock
        filterMock.filter = mock.MagicMock()
        filterMock.filter.return_value = mock.MagicMock()
        filterMock.filter.return_value.__len__.return_value=1

        dataRunManager = DataRunManager()
        self.assertIsNotNone(dataRunManager.get_last_run(instrument_id=1))
        filterMock.filter.assert_called_with(instrument_id=1)

    @mock.patch('workflow.database.report.models.InstrumentStatus.objects')
    def test_last_cached_run(self, instrumentStatusObjectsMock):
        mockStatus = mock.MagicMock()
        mockStatus.last_run_id = 1
        instrumentStatusObjectsMock.get.return_value = mockStatus
        dataRunManager = DataRunManager()
        self.assertEqual(dataRunManager.get_last_cached_run(instrument_id=1), 1)

    @mock.patch('workflow.database.report.models.DataRun.objects')
    @mock.patch('workflow.database.report.models.InstrumentStatus.save')
    @mock.patch('workflow.database.report.models.InstrumentStatus')
    @mock.patch('workflow.database.report.models.InstrumentStatus.objects')
    def test_last_cached_run_exception(self, instrumentStatusObjectsMock, instrumentStatusMock, instrumentStatusSaveMock, datarunObjectsMock):
        mockStatus = mock.MagicMock()
        mockStatus.last_run_id = 1
        instrumentStatusInstanceMock = mock.MagicMock()
        instrumentStatusMock.return_value = instrumentStatusInstanceMock
        instrumentStatusInstanceMock.save = instrumentStatusSaveMock

        instrumentStatusObjectsMock.save = instrumentStatusSaveMock
        instrumentStatusMock.objects = instrumentStatusObjectsMock
        instrumentStatusObjectsMock.get.side_effect = Exception('Boom!')

        datarunObjectsMock.get_last_run.return_value = 1
        
        dataRunManager = DataRunManager()
        dataRunManager.get_last_cached_run(instrument_id=1)
        datarunObjectsMock.get_last_run.assert_called()
        instrumentStatusSaveMock.assert_called()


