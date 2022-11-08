import os

os.environ["DB_HOST"] = '127.0.0.1'
os.environ["DB_PORT"] = '3306'
os.environ["DB_NAME"] = 'db1'

import unittest
import warnings
import sys

sys.path.append("..")
from app.app import app

warnings.simplefilter("ignore", ResourceWarning)


class AppTest_DB_available(unittest.TestCase):
  def setUp(self):
    self.ctx = app.app_context()
    self.ctx.push()
    self.client = app.test_client()

  def tearDown(self):
    self.ctx.pop()

  # pylint: disable=too-many-statements
  def test_all(self):
    # test create
    response = self.client.get("/create")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Data is created')

    # test root
    response = self.client.get("/")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['results'], list))

    # test_health(self):
    response = self.client.get("/health")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'health is ok')

    # test_metrics(self):
    response = self.client.get("/metrics")

    self.assertEqual(response.status_code, 200)
    self.assertRegex(response.text, 'python_gc_objects_collected_total')

    # test_crash
    response = self.client.get("/crash")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Successfull shutdown')


if __name__ == "__main__":
  unittest.main()
