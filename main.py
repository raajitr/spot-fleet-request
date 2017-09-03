from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
import bcrypt
import gc
from functools import wraps
from spot_instances import SpotInstantiate
import instances_defs
import os

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

app.config['MONGO_DBNAME'] = 'aws_config'
app.config['MONGO_URI'] = 'mongodb://raajit:alchemist1@ds119524.mlab.com:19524/aws_config'

mongo = PyMongo(app)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        flash('You need to login first')
        return redirect(url_for('index'))
    return wrap

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard/')
@login_required
def dashboard():
    if 'access_key_id' not in session:
        return redirect(url_for('config'))

    fleet_request_ids = SpotInstantiate(session['access_key_id'], session['secret_key']).describe_request()

    if 'error' in fleet_request_ids:
        flash(fleet_request_ids['error'])
        fleet_request_ids = []

    return render_template("dashboard.html",
                            types_of_instances = instances_defs.types_of_instances,
                            fleet_request_ids = fleet_request_ids)

@app.route('/config/', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'POST':
        session['arn'] = request.form['arn']
        session['access_key_id'] = request.form['accesskeyid']
        session['secret_key'] = request.form['secretkey']

        is_authenticated = SpotInstantiate(session['access_key_id'], session['secret_key']).authenticate()

        if is_authenticated:
            return redirect(url_for('dashboard'))
        flash('Invalid Credentials')

    return render_template("config_page.html")

@app.route('/launch_fleet/', methods=['POST'])
def launch_fleet():
    fleet_request = {
        'instance_type': request.form['instance_type'],
        'fleet_size': int(request.form['fleet_size']),
        'price': request.form['price'],
        'request_expiration_time': request.form['request_expiration_time'],
        'arn': session['arn'],
        'ami_id': request.form['ami_id']
    }
    request_status = SpotInstantiate(session['access_key_id'], session['secret_key'])._request_spot_fleet(fleet_request)

    if 'error' in request_status:
        flash(request_status['error'])

    return redirect(url_for('dashboard'))

@app.route('/cancel_request/<request_id>', methods=['POST'])
def cancel_request(request_id):

    request_status = SpotInstantiate(session['access_key_id'], session['secret_key']).cancel_request(request_id)

    if request_status:
        flash(request_status)

    return redirect(url_for('dashboard'))

# Login/ Logout/ Sign Up
@app.route('/register/', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf8'), bcrypt.gensalt())

            users.insert({'name': request.form['name'],
                          'username': request.form['username'],
                          'password': hashpass})

            session['logged_in'] = True
            session['username'] = request.form['username']
            return redirect(url_for('config'))
        # else
        flash('That username already exists')
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('config'))

    if request.method == 'POST':
        users = mongo.db.users
        attempted_user = users.find_one({'username': request.form['username']})

        if attempted_user:
            is_password_matched = bcrypt.hashpw(request.form['password'].encode('utf-8'),
                                  attempted_user['password'].encode('utf-8')) == attempted_user['password'].encode('utf-8')

            if is_password_matched:
                session['username'] = request.form['username']
                session['logged_in'] = True
                return redirect(url_for('config'))
    return render_template("login.html")

@app.route('/logout/')
@login_required
def logout():
    session.clear()
    gc.collect() # garbage collector
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return '404'

@app.errorhandler(400)
def bad_request(e):
    return e

if __name__ == "__main__":
    app.secret_key = os.environ["SECRET_KEY"]
    app.run()
