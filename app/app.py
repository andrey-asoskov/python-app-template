import os
import json
import logging
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

metrics = PrometheusMetrics(app)
metrics.info("app_info", "The App", version="0.1.0")

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

db_password = ''
if os.path.isfile(basepath + '/../data/mysql-user-password'):
  with open(basepath + '/../data/mysql-user-password', 'r', encoding="utf-8") as file_object:
    db_password = file_object.read()
elif os.path.isfile('/run/secrets/mysql-user-password'):
  with open('/run/secrets/mysql-user-password', 'r', encoding="utf-8") as file_object:
    db_password = file_object.read()
else:
  app.logger.error('Cannot read secrets - db user password')

db_host = os.environ.get('DB_HOST') or ''
db_port = os.environ.get('DB_PORT') or '3306'
db_name = os.environ.get('DB_NAME') or ''

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + db_user + ':' + db_password + '@' + db_host + ':' + db_port + '/' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.logger.info('DB Config: ' + 'mysql+pymysql://' + db_user + ':' + 'XXX' + '@' + db_host + ':' + db_port + '/' + db_name)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# pylint: disable=too-few-public-methods
class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), unique=True, index=True)
  role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

  def __repr__(self):
      return f'<User {self.username}>'


# pylint: disable=too-few-public-methods
class Role(db.Model):
  __tablename__ = 'roles'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), unique=True)
  users = db.relationship('User', backref='role')

  def __repr__(self):
      return f'<Role {self.name}>'


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


@app.route('/', methods=['GET', 'POST'])
def index():
  try:
    users = User.query.all()
  except:
    app.logger.error("Something is wrong with DB connection")
    message = 'Something is wrong with DB connection'
    abort(400, {'message': message})
  else:
    res = {'results': []}
    for user in users:
        res['results'].append({
          'user_id': user.id,
          'username': user.username,
          'user_role': Role.query.filter_by(id=user.role_id).first().name
        })

    return return_ok(res)


@app.route('/health', methods=['GET'])
def get_health():
  try:
    db.session.execute('SELECT 1')
  except:
    app.logger.error("Something is wrong with DB connection")
    message = 'Something is wrong with DB connection'
    abort(400, {'message': message})
  else:
    message = 'health is ok'
    data = {'message': message}
    return return_ok(data)


@app.route('/create', methods=['GET'])
def get_create():
  try:
    db.drop_all()
    db.create_all()

    admin_role = Role(name='Admin')
    mod_role = Role(name='Moderator')
    user_role = Role(name='User')

    user_john = User(username='john', role=admin_role)
    user_susan = User(username='susan', role=user_role)
    user_david = User(username='david', role=user_role)

    db.session.add(admin_role)
    db.session.add(mod_role)
    db.session.add(user_role)
    db.session.add(user_john)
    db.session.add(user_susan)
    db.session.add(user_david)
    db.session.commit()
  except:
    app.logger.error("Something is wrong with DB connection")
    message = 'Something is wrong with DB connection'
    abort(400, {'message': message})
  else:
    message = 'Data is created'
    data = {'message': message}
    return return_ok(data)


@app.route("/crash", methods=['GET'])
def get_crash():
  try:
    db.session.close()
  except:
    app.logger.error('Failed to close DB connection')
    message = 'Failed to close DB connection'
    abort(400, {'message': message})
  else:
    message = 'Successfull shutdown'
    data = {'message': message}
    return return_ok(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
