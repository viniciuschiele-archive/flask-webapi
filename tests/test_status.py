from flask_webapi import status
from unittest import TestCase


class TestStatus(TestCase):
    def test_is_informational(self):
        self.assertFalse(status.is_informational(99))
        self.assertFalse(status.is_informational(200))

        for i in range(100, 199):
            self.assertTrue(status.is_informational(i))

    def test_is_success(self):
        self.assertFalse(status.is_success(199))
        self.assertFalse(status.is_success(300))

        for i in range(200, 299):
            self.assertTrue(status.is_success(i))

    def test_is_redirect(self):
        self.assertFalse(status.is_redirect(299))
        self.assertFalse(status.is_redirect(400))

        for i in range(300, 399):
            self.assertTrue(status.is_redirect(i))

    def test_is_client_error(self):
        self.assertFalse(status.is_client_error(399))
        self.assertFalse(status.is_client_error(500))

        for i in range(400, 499):
            self.assertTrue(status.is_client_error(i))

    def test_is_server_error(self):
        self.assertFalse(status.is_server_error(499))
        self.assertFalse(status.is_server_error(600))

        for i in range(500, 599):
            self.assertTrue(status.is_server_error(i))
