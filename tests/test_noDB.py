import os

os.environ["DB_HOST"] = ''
os.environ["DB_PORT"] = '5555'
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

  def test_health1(self):
    response = self.client.get("/health")

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Something is wrong with DB connection')

  def test_createt(self):
    response = self.client.get("/create")

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Something is wrong with DB connection')

  def test_root(self):
    response = self.client.get("/")

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Something is wrong with DB connection')

  def test_health2(self):
    response = self.client.get("/health")

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Something is wrong with DB connection')

  def test_crash(self):
    response = self.client.get("/crash")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Successfull shutdown')


if __name__ == "__main__":
  unittest.main(verbosity=2)
