import pytest
from unittest import mock
from django.test import TestCase

from reporting.report.models import Instrument
from reporting.report.models import DataRun
from reporting.report.models import RunStatus
from reporting.report.models import IPTS
from reporting.report.models import StatusQueue
from reporting.report.models import Task
from reporting.report.models import WorkflowSummary
from reporting.report.models import StatusQueueMessageCount

import json


class ViewUtilTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ipts = IPTS.objects.create(expt_name="test_exp")
        ipts.save()
        sq = StatusQueue(name="test", is_workflow_input=True)
        sq.save()
        for run_number in range(10):
            # make a missing run
            if run_number == 5:
                continue
            run = DataRun.objects.create(
                run_number=run_number,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"tmp/test_{run_number}.nxs",
            )
            run.save()
            rs = RunStatus.objects.create(
                run_id=run,
                queue_id=sq,
                message_id=f"msg: test_run_{run_number}",
            )
            rs.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=False,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            )

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="test_exp").delete()
        StatusQueue.objects.all().delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def test_generate_key(self):
        from reporting.report.view_util import generate_key

        # case: LIVE_PLOT_SECRET_KEY not in settings
        inst = "test_instrument"
        run_id = 1
        rst = generate_key(inst, run_id)
        self.assertEqual(rst, None)
        # case: LIVE_PLOT_SECRET_KEY is empty string
        with self.settings(LIVE_PLOT_SECRET_KEY=""):
            rst = generate_key(inst, run_id)
            self.assertEqual(rst, None)
        # case: LIVE_PLOT_SECRET_KEY is valid
        with self.settings(LIVE_PLOT_SECRET_KEY="test_key"):
            rst = generate_key(inst, run_id)
            refval = "d556af22f61bf04e6eb79d88f5c9031230b29b33"
            self.assertEqual(rst, refval)

    def test_append_key(self):
        from reporting.report.view_util import append_key

        # case: client_key is None
        input_url = "www.test.xyz"
        inst = "test_instrument"
        run_id = 1
        rst = append_key(input_url, inst, run_id)
        self.assertEqual(rst, input_url)
        # case: client_key is not None
        with self.settings(LIVE_PLOT_SECRET_KEY="test_key"):
            rst = append_key(input_url, inst, run_id)
            refval = f"{input_url}?key=d556af22f61bf04e6eb79d88f5c9031230b29b33"
            self.assertEqual(rst, refval)

    @mock.patch(("reporting.dasmon.view_util.fill_template_values"), return_value="passed")
    def test_fill_template_values(self, mockDasmonTemplateFiller):
        from reporting.report.view_util import fill_template_values

        # - prep
        request = {"test_key": "test_val"}
        # make flake8 happy
        _ = mockDasmonTemplateFiller(request, test="test")
        # - test
        # case: no instrument specified
        rst = fill_template_values(request, test_arg1="test_arg1")
        self.assertEqual(rst["test_arg1"], "test_arg1")
        # case: correct usage
        rst = fill_template_values(
            request,
            instrument="Test_Instrument",
            test_arg="test_arg",
        )
        self.assertEqual(rst, "passed")

    def test_needs_reduction(self):
        from reporting.report.view_util import needs_reduction

        inst = Instrument.objects.get(name="test_instrument")
        run_id = DataRun.objects.get(run_number=1, instrument_id=inst)
        request = {"test", "test"}
        # case: no valid entry in queue
        rst = needs_reduction(request, run_id)
        self.assertFalse(rst)
        # case: queue says ready, and no task found
        sq_DataReady = StatusQueue(name="REDUCTION.DATA_READY", is_workflow_input=True)
        sq_DataReady.save()
        rst = needs_reduction(request, run_id)
        self.assertTrue(rst)
        # case: queue says ready, but task list is not empty
        Task.objects.create(
            instrument_id=inst,
            input_queue_id=sq_DataReady,
        ).save()
        rst = needs_reduction(request, run_id)
        self.assertFalse(rst)

    @mock.patch("reporting.reporting_app.view_util.send_activemq_message")
    @mock.patch("reporting.report.catalog.get_run_info")
    def test_send_processing_request(self, mockGetRunInfo, mockMsgSender):
        from reporting.report.view_util import send_processing_request

        # - prep
        mockGetRunInfo = mock.MagicMock()
        mockGetRunInfo.return_value = {
            "data_files": [f"/tmp/test_{i}.nxs.h5" for i in range(4)],
            "proposal": [f"pp_{i}" for i in range(4)],
        }
        #
        mockMsgSender = mock.MagicMock()
        mockMsgSender.return_value = "tester"
        inst = Instrument.objects.get(name="test_instrument")
        run_id = DataRun.objects.get(run_number=1, instrument_id=inst)
        # - test
        # NOTE: no side effect to check against, so running without errors
        #       is the test here.
        send_processing_request(inst, run_id)

    @mock.patch("reporting.report.view_util.send_processing_request")
    def test_processing_request(self, mockSendProcessRequest):
        from reporting.report.view_util import processing_request

        #
        mockSendProcessRequest = mock.MagicMock()
        mockSendProcessRequest.return_value = "test"
        #
        request = mock.MagicMock()
        request.user = mock.MagicMock()
        request.user.return_value = "test_user"
        # NOTE: no artifact to check against, running without error is the check
        #       here
        processing_request(
            request,
            instrument="test_instrument",
            run_id=1,
            destination=None,
        )

    def test_retrieve_rates(self):
        from reporting.report.view_util import retrieve_rates

        inst = Instrument.objects.get(name="test_instrument")
        run_id = DataRun.objects.get(run_number=1, instrument_id=inst)
        #
        runs, errors = retrieve_rates(inst, run_id)
        # NOTE: we are checking the default ones
        self.assertGreater(len(runs), 1)
        self.assertGreater(len(errors), 1)

    def test_run_rate(self):
        from reporting.report.view_util import run_rate

        inst = Instrument.objects.get(name="test_instrument")
        runs = run_rate(inst)
        # NOTE: we are checking the default ones
        self.assertGreater(len(runs), 1)

    def test_error_rate(self):
        from reporting.report.view_util import error_rate

        inst = Instrument.objects.get(name="test_instrument")
        errors = error_rate(inst)
        # NOTE: we are checking the default ones
        self.assertGreater(len(errors), 1)

    def test_get_current_status(self):
        from reporting.report.view_util import get_current_status

        inst = Instrument.objects.get(name="test_instrument")
        rst = get_current_status(inst)
        self.assertTrue("run_rate" in rst.keys())
        self.assertTrue("error_rate" in rst.keys())
        self.assertEqual(rst["last_expt"], "TEST_EXP")

    def test_is_acquisition_complete(self):
        from reporting.report.view_util import is_acquisition_complete

        inst = Instrument.objects.get(name="test_instrument")
        run_id = DataRun.objects.get(run_number=1, instrument_id=inst)
        rst = is_acquisition_complete(run_id)
        self.assertFalse(rst)

    def test_get_post_processing_status(self):
        from reporting.report.view_util import get_post_processing_status

        rst = get_post_processing_status()
        self.assertEqual(rst["catalog"], 0)
        self.assertEqual(rst["reduction"], 0)

    def test_get_run_status_text(self):
        from reporting.report.view_util import get_run_status_text

        inst = Instrument.objects.get(name="test_instrument")
        run_id = DataRun.objects.get(run_number=1, instrument_id=inst)
        # show element id
        rst = get_run_status_text(run_id, use_element_id=True)
        self.assertTrue("run_id_" in rst)
        # no show element id, green status
        rst = get_run_status_text(run_id)
        self.assertTrue("acquiring" in rst)
        # no show element, red status
        ipts = IPTS.objects.get(expt_name="test_exp")
        run = DataRun.objects.create(
            run_number=65535,
            ipts_id=ipts,
            instrument_id=inst,
            file="/tmp/test_65535.nxs",
        )
        run.save()
        workflowSummary = WorkflowSummary.objects.create(
            run_id=run,
            complete=False,
        )
        workflowSummary.save()

        rst = get_run_status_text(run)
        self.assertTrue("acquiring" in rst)
        dataReady = StatusQueue(name="POSTPROCESS.DATA_READY", is_workflow_input=True)
        dataReady.save()
        RunStatus.objects.create(run_id=run, queue_id=dataReady).save()
        rst = get_run_status_text(run)
        self.assertTrue("red" in rst)
        self.assertTrue("incomplete" in rst)

        workflowSummary.complete = True
        workflowSummary.save()
        rst = get_run_status_text(run)
        self.assertTrue("green" in rst)
        self.assertTrue("complete" in rst)

    def test_get_run_list_dict(self):
        from reporting.report.view_util import get_run_list_dict

        inst = Instrument.objects.get(name="test_instrument")
        runs = DataRun.objects.filter(instrument_id=inst)
        rst = get_run_list_dict(runs)
        # note: run_5 is skipped on purpose
        self.assertEqual(len(rst), 9)

    def test_extract_ascii_from_div(self):
        from reporting.report.view_util import extract_ascii_from_div

        # case: null input
        html_data = "<div>test</div>"
        rst = extract_ascii_from_div(html_data)
        self.assertEqual(rst, None)
        # case: valid input
        # NOTE: the actual html page has a lot of other meta info
        #       inserted in the newPlot func, which might break this func
        #       during production (so far it hasn't happend yet)
        html_data = r"""Plotly.newPlot([{"name": "sp-1", "type": "scatter", "visible": true,
            "x": [1.098439161783472, 1.0993178366492713, 1.100197214393798],
            "y": [32.900697887235374, 33.88348428512092, 34.96296658992418]}],
            {"margin": {"b": 40, "l": 40, "r": 0, "t": 0},
            "xaxis": {"title": {"text": "d-spacing (A)"}},
            "yaxis": {"title": {"text": "Counts per microAmp.hour"}}},
            {"responsive": true})</script>""".replace(
            "\n", ""
        )
        rst = extract_ascii_from_div(html_data, trace_id=1)
        refval = "1.09844 32.9007 0 0\n1.09932 33.8835 0 0\n1.1002 34.963 0 0\n"
        self.assertEqual(rst, refval)

    @mock.patch("reporting.report.view_util.get_plot_data_from_server")
    def test_get_plot_template_dict(self, mockGetDataFromServer):
        from reporting.report.view_util import get_plot_template_dict

        inst = Instrument.objects.get(name="test_instrument")
        run_id = 1
        run = DataRun.objects.get(run_number=run_id, instrument_id=inst)
        #
        mockGetDataFromServer = mock.MagicMock()
        mockGetDataFromServer.return_value = "test_html"
        rst = get_plot_template_dict(run, inst, run_id)
        self.assertTrue("html_data" in rst.keys())

    @mock.patch("requests.get")
    def test_get_plot_data_from_server(self, mockRequestsGet):
        from reporting.report.view_util import get_plot_data_from_server

        # mock external dependencies
        getresponse_return = mock.MagicMock()
        getresponse_return.status_code = 200
        getresponse_return.text = "test"
        mockRequestsGet.return_value = getresponse_return
        # test
        inst = Instrument.objects.get(name="test_instrument")
        run = DataRun.objects.get(run_number=1, instrument_id=inst)
        rst = get_plot_data_from_server(inst.name, run)
        self.assertEqual(rst, "test")

    def test_extract_d3_data_from_json(self):
        from reporting.report.view_util import extract_d3_data_from_json

        # null case
        plot_data, x_label, y_label = extract_d3_data_from_json(None)
        self.assertEqual(plot_data, None)
        self.assertEqual(x_label, "Q [1/\u00c5]")
        self.assertEqual(y_label, "Absolute reflectivity")
        # main_output in data_dict['main_output']
        json_data = json.dumps(
            {
                "main_output": {
                    "x": [1, 2, 3],
                    "y": [1, 2, 3],
                    "e": [0, 0, 0],
                    "x_label": "x_label",
                    "y_label": "y_label",
                }
            }
        )
        plot_data, x_label, y_label = extract_d3_data_from_json(json_data)
        self.assertEqual(len(plot_data), 3)
        self.assertEqual(x_label, "x_label")
        self.assertEqual(y_label, "y_label")
        # data in data_dict['main_output']
        json_data = json.dumps(
            {
                "main_output": {
                    "data": {
                        "1": [
                            [1, 2, 3],  # x
                            [1, 2, 3],  # y
                            [0, 0, 0],  # e
                            [0, 0, 0],  # dx [optional]
                        ]
                    },
                    "axes": {
                        "xlabel": "xlabel",
                        "ylabel": "ylabel",
                    },
                }
            }
        )
        plot_data, x_label, y_label = extract_d3_data_from_json(json_data)
        self.assertEqual(len(plot_data), 3)
        self.assertEqual(x_label, "xlabel")
        self.assertEqual(y_label, "ylabel")

    def test_find_skipped_runs(self):
        from reporting.report.view_util import find_skipped_runs

        inst = Instrument.objects.get(name="test_instrument")
        missing_runs = find_skipped_runs(inst)
        self.assertEqual(missing_runs[0], 5)

    def test_get_status_queue_message_count(self):
        from reporting.report.view_util import reduction_queue_sizes

        sq1 = StatusQueue(name="TEST_QUEUE", is_workflow_input=True)
        sq1.save()
        sq2 = StatusQueue(name="TEST_QUEUE2", is_workflow_input=True)
        sq2.save()

        StatusQueueMessageCount(queue=sq1, message_count=10).save()
        StatusQueueMessageCount(queue=sq1, message_count=11).save()
        StatusQueueMessageCount(queue=sq1, message_count=12).save()
        StatusQueueMessageCount(queue=sq2, message_count=42).save()

        queue_size_list = reduction_queue_sizes()
        self.assertEqual(len(queue_size_list), 2)
        assert queue_size_list[0]["queue"] == "TEST_QUEUE"
        assert queue_size_list[0]["message_count"] == 12
        assert queue_size_list[1]["queue"] == "TEST_QUEUE2"
        assert queue_size_list[1]["message_count"] == 42


if __name__ == "__main__":
    pytest.main([__file__])
