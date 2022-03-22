import pytest
from unittest import TestCase
import workflow

_ = [workflow]


class StateUtilitiesTest(TestCase):
    def test_decode_message(self):
        from workflow.state_utilities import decode_message

        msg = "/SNS/EQSANS/IPTS-1234/nexus/EQSANS_5678.nxs.h5"
        data = decode_message(msg)
        self.assertEqual(data["instrument"], "eqsans")
        self.assertEqual(data["facility"], "SNS")
        self.assertEqual(data["ipts"], "ipts-1234")
        self.assertEqual(data["run_number"], 5678)
        self.assertEqual(data["data_file"], msg)

    def test_logged_action(self):
        # NOTE: logged_action is a decorator and should be tested with integration
        #       test.
        pass


if __name__ == "__main__":
    pytest.main()
