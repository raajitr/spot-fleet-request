import bcrypt
import gc
from functools import wraps
import os

from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo

import instances_defs
from spot_instances import SpotInstantiate

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

# MongoDB hosted by mLabs
app.config['MONGO_DBNAME'] = os.environ['MONGO_DBNAME']
app.config['MONGO_URI'] = os.environ['MONGO_URI']

mongo = PyMongo(app)

# decorator to be used for redirecting to login page if not logged in
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        flash('You need to login first')
        return redirect(url_for('index'))
    return wrap

# index route
@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard/')
@login_required
def dashboard():
    if 'access_key_id' not in session:
        flash('You need to add AWS Credentials first')
        return redirect(url_for('config'))

    # get request ids using the User's config credentials
    fleet_request_ids = SpotInstantiate(session['access_key_id'], session['secret_key']).describe_request()

    if 'error' in fleet_request_ids:
        flash(fleet_request_ids['error'])
        fleet_request_ids = []

    return render_template("dashboard.html",
                            types_of_instances = instances_defs.types_of_instances,
                            fleet_request_ids = fleet_request_ids)

# Config
@app.route('/config/', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'POST':
        session['arn'] = request.form['arn']
        session['access_key_id'] = request.form['accesskeyid']
        session['secret_key'] = request.form['secretkey']

        # authenticate's the AWS credentials
        is_authenticated = SpotInstantiate(session['access_key_id'], session['secret_key']).authenticate()

        if is_authenticated:
            return redirect(url_for('dashboard'))
        flash('Invalid Credentials')

    return render_template("config_page.html")

# Launch Fleet Post Request
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
    # request spot fleet
    request_status = SpotInstantiate(session['access_key_id'], session['secret_key'])._request_spot_fleet(fleet_request)

    if 'error' in request_status:
        flash(request_status['error'])

    return redirect(url_for('dashboard'))

# Cancel Fleet Request
@app.route('/cancel_request/<request_id>', methods=['POST'])
def cancel_request(request_id):
    # Cancels request as per the request id
    request_status = SpotInstantiate(session['access_key_id'], session['secret_key']).cancel_request(request_id)

    if request_status:
        flash(request_status)

    return redirect(url_for('dashboard'))

# Login/ Logout/ Sign Up
@app.route('/register/', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # Connecting to users collection stored in database
        users = mongo.db.users
        # get user's query filtered by name
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf8'), bcrypt.gensalt())

            users.insert({'name': request.form['name'],
                          'username': request.form['username'],
                          'password': hashpass})

            session['logged_in'] = True
            session['username'] = request.form['username']
            return redirect(url_for('config'))
        # if above doesn't checks out then the username already exists
        flash('That username already exists')
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('config'))

    if request.method == 'POST':
        users = mongo.db.users
        attempted_user = users.find_one({'username': request.form['username']})
        try:
            if attempted_user:
                is_password_matched = bcrypt.hashpw(request.form['password'].encode('utf-8'),
                                    attempted_user['password'].encode('utf-8')) == attempted_user['password'].encode('utf-8')
        except Exception as e:
            flash(e)
            return redirect(url_for('login'))
            if is_password_matched:
                session['username'] = request.form['username'].encode('utf-8')
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

if __name__ == "__main__":
    app.run(debug=True)
