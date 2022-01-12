import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from report.models import Instrument, IPTS, DataRun, StatusQueue
from dasmon.models import ActiveInstrument
from report.forms import ProcessingForm


def test_validate_integer_list():
    from report.forms import validate_integer_list

    # case: "1,2,3"
    value_list = validate_integer_list("1,2,3")
    assert value_list == [1, 2, 3]
    # case: "1-3"
    value_list = validate_integer_list("1-3")
    assert value_list == [1, 2, 3]
    # case: "1-3,5,6"
    value_list = validate_integer_list("1-3,5,6")
    assert value_list == [1, 2, 3, 5, 6]
    # case: "1-3,5-7"
    value_list = validate_integer_list("1-3,5-7")
    assert value_list == [1, 2, 3, 5, 6, 7]
    # case: "error"
    with pytest.raises(ValidationError):
        validate_integer_list("error")
    # case: "-2"
    with pytest.raises(ValidationError):
        validate_integer_list("-2")


class ProcessingFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # add IPTS
        ipts = IPTS.objects.create(expt_name="TEST_IPTS")
        ipts.save()
        # add instrument
        for i in range(3):
            inst = Instrument.objects.create(name=f"test_instrument_{i}")
            inst.save()
            ActiveInstrument.objects.create(
                instrument_id=inst,
                is_alive=True,
                is_adara=True,
                has_pvsd=True,
                has_pvstreamer=True,
            ).save()
            # add instrument to the many-to-many field for IPTS
            ipts.instruments.add(inst)
            # add data run
            for rn in range(4):
                DataRun.objects.create(
                    run_number=rn,
                    ipts_id=ipts,
                    instrument_id=inst,
                ).save()
        # add status queue
        for i in ("POSTPROCESS", "REDUCTIO", "TEST"):
            for ending in ("REQUEST", "DATA_READY", "NOT_NEEDED", "TEST"):
                StatusQueue.objects.create(
                    name=f"{i}.{ending}",
                    is_workflow_input=True,
                ).save()

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.all().delete()
        StatusQueue.objects.all().delete()
        IPTS.objects.all().delete()
        DataRun.objects.all().delete()

    def test_init(self):
        form = ProcessingForm(
            {
                "instrument": "test_instrument_0",
                "experiment": "TEST_IPTS",
                "run_list": "1,2,3",
                "create_as_needed": True,
                "task": "POSTPROCESS.REQUEST",
            }
        )
        self.assertTrue(form.is_valid())
        for me in ("instrument", "experiment", "run_list", "create_as_needed", "task"):
            self.assertTrue(me in form.fields)

    def test_instrument_list_proper(self):
        form = ProcessingForm(
            {
                "instrument": "test_instrument_0",
                "experiment": "TEST_IPTS",
                "run_list": "1,2,3",
                "create_as_needed": True,
                "task": "POSTPROCESS.REQUEST",
            }
        )
        self.assertTrue(form.is_valid())
        Instruments = form.fields["instrument"].choices
        self.assertEqual(len(Instruments), 3)

    def test_task_list_proper(self):
        form = ProcessingForm(
            {
                "instrument": "test_instrument_0",
                "experiment": "TEST_IPTS",
                "run_list": "1,2,3",
                "create_as_needed": True,
                "task": "POSTPROCESS.REQUEST",
            }
        )
        self.assertTrue(form.is_valid())
        Tasks = form.fields["task"].choices
        self.assertEqual(len(Tasks), 3 * (4 - 1))  # TEST is not a valid ending

    def test_set_initial_proper(self):
        form = ProcessingForm(
            {
                "instrument": "test_instrument_0",
                "experiment": "TEST_IPTS",
                "run_list": "1,2,3",
                "create_as_needed": True,
                "task": "POSTPROCESS.REQUEST",
            }
        )
        self.assertTrue(form.is_valid())
        # case: empty initial -> restore to defaults
        form.set_initial({})
        self.assertTrue(form.is_valid())
        # NOTE: this might be a bug from django end as it does not clear the
        #       existing instrument list properly
        self.assertEqual(len(form.initial["instrument"]), 2)
        self.assertEqual(form.initial["task"], "POSTPROCESS.DATA_READY")
        # case: non-empty initial
        initial = {
            "instrument": "test_instrument_1",
            "experiment": "TEST_IPTS",
            "run_list": "1,2,3",
            "create_as_needed": True,
            "task": "REDUCTION.REQUEST",
        }
        form.set_initial(initial)
        self.assertEqual(form.initial["instrument"], "test_instrument_1")
        self.assertEqual(form.initial["experiment"], "TEST_IPTS")
        self.assertEqual(form.initial["run_list"], "1,2,3")
        self.assertEqual(form.initial["create_as_needed"], True)
        self.assertEqual(form.initial["task"], "REDUCTION.REQUEST")

    def test_create_file_path(self):
        # case: is adara
        inst = Instrument.objects.get(name="test_instrument_0")
        ipts = "test_ipts"
        run = 1
        file_path = ProcessingForm._create_file_path(inst, ipts, run)
        refval = "/SNS/TEST_INSTRUMENT_0/test_ipts/nexus/TEST_INSTRUMENT_0_1.nxs.h5"
        self.assertEqual(file_path, refval)
        # case: no adara
        inst = Instrument.objects.create(name="test_instrument_x")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_adara=False,
        ).save()
        file_path = ProcessingForm._create_file_path(inst, ipts, run)
        refval = (
            "/SNS/TEST_INSTRUMENT_X/test_ipts/0/1/NeXus/TEST_INSTRUMENT_X_1_event.nxs"
        )
        self.assertEqual(file_path, refval)

    def test_recover_processed_run(self):
        form = ProcessingForm(
            {
                "instrument": "test_instrument_0",
                "experiment": "TEST_IPTS",
                "run_list": "1,2,3",
                "create_as_needed": True,
                "task": "POSTPROCESS.REQUEST",
            }
        )
        self.assertTrue(form.is_valid())
        #
        inst = Instrument.objects.get(name="test_instrument_0")
        rst = form._recover_processed_run(inst)
        #
        self.assertEqual(rst["task"], "POSTPROCESS.REQUEST")
        self.assertEqual(str(rst["instrument"]), "test_instrument_0")
        self.assertEqual(len(rst["runs"]), 3)
        self.assertTrue(rst["is_complete"])

    def test_process(self):
        data = {
            "instrument": "test_instrument_0",
            "experiment": "TEST_IPTS",
            "run_list": "1,2,3",
            "create_as_needed": True,
            "task": "POSTPROCESS.REQUEST",
        }
        # case: all valid
        form = ProcessingForm(data)
        if not form.is_valid():
            print("error is:")
            print(form.errors)
        rst = form.process()
        self.assertTrue("Found instrument" in rst["report"])
        self.assertTrue("Found experiment" in rst["report"])
        self.assertEqual(rst["task"], "POSTPROCESS.REQUEST")
        self.assertEqual(len(rst["runs"]), 3)
        # case: create new run
        data = {
            "instrument": "test_instrument_0",
            "experiment": "TEST_IPTS",
            "run_list": "1,2,3,4",
            "create_as_needed": True,
            "task": "POSTPROCESS.REQUEST",
        }
        form = ProcessingForm(data)
        self.assertTrue(form.is_valid())
        rst = form.process()
        self.assertTrue("The following runs will be created: [4]" in rst["report"])
        self.assertEqual(len(rst["runs"]), 4)


if __name__ == "__main__":
    pytest.main([__file__])
