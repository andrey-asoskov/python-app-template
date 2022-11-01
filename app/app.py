import time
import os
import ipaddress
import json
import logging
import sqlite3
from flask import Flask, request, send_file
from flask import abort, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import mysql.connector
from mysql.connector import errorcode
import dns.resolver

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
prefix = 'v1'

metrics = PrometheusMetrics(app)
metrics.info("app_info", "The App", version="0.1.0")

db_config = {
    'host': os.environ.get('DB_HOST') or '',
    'port': os.environ.get('DB_PORT') or '',
    'database': os.environ.get('DB_NAME') or '',
    # 'user': os.environ.get('DB_USER') or '',
    # 'password': os.environ.get('DB_PASSWORD') or '',
    'get_warnings': True,
    'raise_on_warnings': False
}

basepath = os.path.dirname(__file__)

db_user = ''
if os.path.isfile(basepath + '/../data/mysql-user-name'):
  with open(basepath + '/../data/mysql-user-name', 'r', encoding="utf-8") as file_object:
    db_user = file_object.read()
elif os.path.isfile('/run/secrets/mysql-user-name'):
  with open('/run/secrets/mysql-user-name', 'r', encoding="utf-8") as file_object:
    db_user = file_object.read()
else:
  app.logger.error('Cannot read secrets - db user name')
db_config['user'] = db_user

db_password = ''
if os.path.isfile(basepath + '/../data/mysql-user-password'):
  with open(basepath + '/../data/mysql-user-password', 'r', encoding="utf-8") as file_object:
    db_password = file_object.read()
elif os.path.isfile('/run/secrets/mysql-user-password'):
  with open('/run/secrets/mysql-user-password', 'r', encoding="utf-8") as file_object:
    db_password = file_object.read()
else:
  app.logger.error('Cannot read secrets - db user password')

db_config['password'] = db_password

db_config_secure = dict(db_config)
db_config_secure['password'] = 'XXX'
app.logger.info('DB Config: %s ', json.dumps(db_config_secure))


if os.environ.get('APP_ENV', 'PROD') == "PROD":
  try:
    cnx_g = mysql.connector.connect(**db_config)
    cursor_g = cnx_g.cursor(buffered=True)
    show_status_g = ("SHOW STATUS;")
    cursor_g.execute(show_status_g)
  except mysql.connector.Error as err_g:
    if err_g.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      app.logger.error("Something is wrong with your user name or password")
    elif err_g.errno == errorcode.ER_BAD_DB_ERROR:
      app.logger.error("Database does not exist")
    else:
      app.logger.error(f'Something went wrong: {format(err_g)}')
  else:
    app.logger.info('Connected to MySQL Database')
else:
  cnx_g = sqlite3.connect("queries.sqlite3")
  cur = cnx_g.cursor()
  cur.execute("""
              DROP TABLE IF EXISTS  queries;
              """
              )
  cur.execute("""
              CREATE TABLE queries
              (id INTEGER PRIMARY KEY NOT NULL,
              created_at int(10) NOT NULL,
              client_ip char(15),
              domain char(255),
              addresses char(255));
              """
              )
  app.logger.info('Connected to sqlite3 Database')


def return_ok(data):
  response = jsonify(data)
  response.content_type = 'application/json'
  response.status_code = 200

  app.logger.info('Sent response - Content-Type: %s, Status-code: %s, Data: %s ',
                  response.content_type, response.status_code, json.dumps(data))

  return response


@app.before_request
def save_request():
  request_data = request.get_json(silent=True)
  app.logger.info('Received request - Client: %s, Path: %s, Method: %s, Content-Type: %s, Data: %s',
                  request.remote_addr, request.path, request.method, request.content_type, json.dumps(request_data))


@app.errorhandler(400)
def bad_request(error):
  if 'message' in error.description:
    data = {'message': error.description['message']}
  else:
    data = {"message": "Error"}

  response = jsonify(data)
  response.content_type = 'application/json'
  response.status_code = 400

  app.logger.error('Sent response - Content-Type: %s, Status-code: %s, Data: %s ',
                   response.content_type, response.status_code, json.dumps(data))

  return response


@app.errorhandler(404)
def resource_not_found(error):
  if 'message' in error.description:
    data = {'message': error.description['message']}
  else:
    data = {"message": "Error"}

  response = jsonify(data)
  response.content_type = 'application/json'
  response.status_code = 404

  app.logger.error('Sent response - Content-Type: %s, Status-code: %s, Data: %s ',
                   response.content_type, response.status_code, json.dumps(data))

  return response


@app.errorhandler(500)
def server_error(error):
  if 'message' in error.description:
    data = {'message': error.description['message']}
  else:
    data = {"message": "Error"}

  response = jsonify(data)
  response.content_type = 'application/json'
  response.status_code = 500

  app.logger.error('Sent response - Content-Type: %s, Status-code: %s, Data: %s ',
                   response.content_type, response.status_code, json.dumps(data))

  return response


@app.route('/', methods=['GET'])
def get_root():
  if os.environ.get('KUBERNETES_SERVICE_PORT', False):
    IS_K8s = True
  else:
    IS_K8s = False

  data = {'version': '0.1.0',
          'date': int(time.time()),
          'kubernetes': IS_K8s
          }

  return return_ok(data)


@app.route('/health', methods=['GET'])
def get_health():
  if 'cnx_g' in globals():
    try:
      cursor = cnx_g.cursor(buffered=True)
      show_status = ("SELECT * FROM queries;")
      cursor.execute(show_status)
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        app.logger.error("Something is wrong with your user name or password")
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        app.logger.error("Database does not exist")
      else:
        app.logger.error(f'Something went wrong: {format(err)}')
      message = 'Failed to get the data'
      abort(400, {'message': message})
    else:
      message = 'health is ok'
      data = {'message': message}
      return return_ok(data)
  else:
    message = 'Database is not connected'
    abort(400, {'message': message})


@app.route("/crash", methods=['GET'])
def get_crash():
  if 'cnx_g' in globals():
    try:
      cursor = cnx_g.cursor()
      grace_shutdown = ("UNLOCK TABLES;")
      cursor.execute(grace_shutdown)
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        app.logger.error("Something is wrong with your user name or password")
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        app.logger.error("Database does not exist")
      else:
        app.logger.error(f'Something went wrong: {format(err)}')
      message = 'Failed to shutdown'
      abort(400, {'message': message})
    else:
      cnx_g.close()
      message = 'Successfull shutdown'
      data = {'message': message}
      return return_ok(data)
  else:
    message = 'Database is not connected'
    abort(400, {'message': message})


@app.route('/' + prefix + '/tools/lookup', methods=['GET'])
def get_lookup():
  request_data = request.get_json(silent=True)

  if 'domain' not in request_data:
    abort(400, {'message': "Domain name is not provided!"})

  try:
    resolved_domain = dns.resolver.resolve(request_data['domain'], 'A')
  except:
    abort(404, {'message': 'Failed to resolve: ' + request_data['domain']})

  domain_addresses = [r.to_text() for r in resolved_domain]
  resolved_at = int(time.time())

  # Writing down successful query
  if 'cnx_g' in globals():
    try:
      cursor = cnx_g.cursor(buffered=True)

      add_entry = ("INSERT INTO queries (created_at, client_ip, domain, addresses) "
                   "VALUES (%s, %s, %s, %s);")

      entry_data = (resolved_at, request.remote_addr,
                    request_data['domain'], ','.join(domain_addresses))

      cursor.execute(add_entry, entry_data)
      cnx_g.commit()
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        app.logger.error("Something is wrong with your user name or password")
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        app.logger.error("Database does not exist")
      else:
        app.logger.error(f'Something went wrong: {format(err)}')
      message = 'Failed to insert the data'
      abort(400, {'message': message})
    else:
      data = {'client_ip': request.remote_addr,
              'addresses': [r.to_text() for r in resolved_domain],
              'created_at': resolved_at,
              'domain': request_data['domain']
              }

      return return_ok(data)
  else:
    message = 'Database is not connected'
    abort(400, {'message': message})


@app.route('/' + prefix + '/tools/validate', methods=['POST'])
def post_validate():
  request_data = request.get_json(silent=True)

  if 'ip' not in request_data:
    abort(400, {'message': "IP is not provided!"})

  v6 = False

  try:
    ip = ipaddress.ip_address(request_data['ip'])
    if ip.version == 6:
      v6 = True
  except:
    abort(400, {'message': 'Not a valid IP address!'})

  if v6 is True:
    abort(400, {'message': 'Not a IPv4 address!'})

  data = {'status': True}

  return return_ok(data)


@app.route('/' + prefix + '/history', methods=['GET'])
def get_history():
  if 'cnx_g' in globals():
    try:
      # cnx = mysql.connector.connect(**db_config)
      cursor = cnx_g.cursor(buffered=True)
      select_last20 = (
          "SELECT created_at,client_ip, domain, addresses FROM queries ORDER BY ID DESC LIMIT 20")
      cursor.execute(select_last20)
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        app.logger.error("Something is wrong with your user name or password")
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        app.logger.error("Database does not exist")
      else:
        app.logger.error(f'Something went wrong: {format(err)}')
      message = 'Failed to get the data'
      abort(400, {'message': message})
    else:
      entries = []

      for (created_at, client_ip, domain, addresses) in cursor:
        entries.append({'created_at': int(created_at),
                        'client_ip': client_ip,
                        'domain': domain,
                        'addresses': [{'ip': i} for i in addresses.split(',')]
                        })
      return return_ok(entries)
  else:
    message = 'Database is not connected'
    abort(400, {'message': message})


@app.route("/api/schema.json")
def return_pdf():
  return send_file('./swagger.json')


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=4000)
