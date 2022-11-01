import os

os.environ["DB_HOST"] = ''
os.environ["DB_PORT"] = ''
os.environ["DB_NAME"] = ''

import unittest
import warnings
import sys

sys.path.append("..")
from app.app import app


class AppTest_DB_notavailable(unittest.TestCase):
  def setUp(self):
    warnings.simplefilter("ignore")
    self.ctx = app.app_context()
    self.ctx.push()
    self.client = app.test_client()

  def tearDown(self):
    self.ctx.pop()

  def test_health(self):
    response = self.client.get("/health")

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Database is not connected')

  def test_crash(self):
    response = self.client.get("/crash")

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Database is not connected')

  def test_lookup(self):
    response = self.client.get(
        "/v1/tools/lookup", headers={'Content-Type': 'application/json'}, data='{"domain": "apple.com"}')

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Database is not connected')

  def test_history(self):
    response = self.client.get(
        "/v1/history", headers={'Content-Type': 'application/json'})

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Database is not connected')


if __name__ == "__main__":
  unittest.main(verbosity=2)
