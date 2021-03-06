#!/usr/bin/python
import unittest
import common
from autotest_lib.client.common_lib.test_utils import mock
from autotest_lib.client.bin import harness, harness_standalone, harness_ABAT


class harness_unittest(unittest.TestCase):
    def setUp(self):
        self.god = mock.mock_god()


    def tearDown(self):
        self.god.unstub_all()


    def test_select_none(self):
        job = object()
        self.god.stub_class(harness_standalone, "harness_standalone")

        harness_standalone.harness_standalone.expect_new(job)
        harness.select(None, job)
        self.god.check_playback()


    def test_select_standalone(self):
        job = object()
        self.god.stub_class(harness_standalone, "harness_standalone")

        harness_standalone.harness_standalone.expect_new(job)
        harness.select('standalone', job)
        self.god.check_playback()


    def test_select_ABAT(self):
        job = object()
        self.god.stub_class(harness_ABAT, "harness_ABAT")

        harness_ABAT.harness_ABAT.expect_new(job)
        harness.select('ABAT', job)
        self.god.check_playback()


if  __name__ == "__main__":
    unittest.main()
