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
    response = self.client.get("/")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['version'], str))
    self.assertTrue(isinstance(response.json['date'], int))
    self.assertTrue(isinstance(response.json['kubernetes'], bool))

    # test_health(self):
    response = self.client.get("/health")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'health is ok')

    # test_metrics(self):
    response = self.client.get("/metrics")

    self.assertEqual(response.status_code, 200)
    self.assertRegex(response.text, 'python_gc_objects_collected_total')

    # test_lookup_good_one_address(self):
    response = self.client.get(
        "/v1/tools/lookup", headers={'Content-Type': 'application/json'}, data='{"domain": "apple.com"}')

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(list(response.json['addresses']), list))
    self.assertTrue(isinstance(response.json['client_ip'], str))
    self.assertTrue(isinstance(response.json['created_at'], int))
    self.assertTrue(isinstance(response.json['domain'], str))
    self.assertEqual(response.json['domain'], 'apple.com')

    # test_lookup_good_may_addresses(self):
    response = self.client.get(
        "/v1/tools/lookup", headers={'Content-Type': 'application/json'}, data='{"domain": "cnn.com"}')

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(list(response.json['addresses']), list))
    self.assertTrue(len(response.json['addresses']) > 1)
    self.assertTrue(isinstance(response.json['client_ip'], str))
    self.assertTrue(isinstance(response.json['created_at'], int))
    self.assertTrue(isinstance(response.json['domain'], str))
    self.assertEqual(response.json['domain'], 'cnn.com')

    # test_lookup_bad1(self):
    response = self.client.get(
        "/v1/tools/lookup", headers={'Content-Type': 'application/json'}, data='{"domain1": "apple.com"}')

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Domain name is not provided!')

    # test_lookup_bad2(self):
    response = self.client.get(
        "/v1/tools/lookup", headers={'Content-Type': 'application/json'}, data='{"domain": "444.44"}')

    self.assertEqual(response.status_code, 404)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'],
                     'Failed to resolve: ' + '444.44')

    # test_validate_good(self):
    response = self.client.post(
        "/v1/tools/validate", headers={'Content-Type': 'application/json'}, data='{"ip":"1.2.3.4"}')

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['status'], bool))
    self.assertEqual(response.json['status'], True)

    # test_validate_bad(self):
    response = self.client.post(
        "/v1/tools/validate", headers={'Content-Type': 'application/json'}, data='{"ip":"1.2.3.444"}')

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Not a valid IP address!')

    # test_validate_v6(self):
    response = self.client.post(
        "/v1/tools/validate", headers={'Content-Type': 'application/json'}, data='{"ip":"2001:db8::"}')

    self.assertEqual(response.status_code, 400)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Not a IPv4 address!')

    # test_history
    response = self.client.get(
        "/v1/history", headers={'Content-Type': 'application/json'})

    self.assertEqual(response.status_code, 200)

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(list(response.json), list))

    # test_crash
    response = self.client.get("/crash")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(isinstance(response.json['message'], str))
    self.assertEqual(response.json['message'], 'Successfull shutdown')


if __name__ == "__main__":
  unittest.main()
