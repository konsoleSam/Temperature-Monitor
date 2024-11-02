#!Placeholder for linux shebang
import sys
import logging
import platform
import datetime
import secrets
import waitress
import socket
import os
import serial
import time
import threading
from flask import Flask,render_template,flash,redirect,url_for,request,session, jsonify#,Blueprint,send_file,send_from_directory,abort,make_response,jsonify# ,Markup
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup

app=Flask(__name__)

# check if app is compiled
FROZEN=getattr(sys, 'frozen', False)
if FROZEN:
    DIRECTORY=os.path.dirname(sys.executable)
else:
    DIRECTORY=os.path.dirname(__file__)

app.instance_path=os.path.join(DIRECTORY,"instance")
app.template_folder=os.path.join(DIRECTORY,"templates")
app.static_folder=os.path.join(DIRECTORY,"static")
if not os.path.exists(app.instance_path):
    os.mkdir(app.instance_path)

# Determine if the app is being run in debug mode
DEBUG=sys.gettrace()!=None
DEVELOPMENT=True
logger=logging.getLogger(__name__)
if DEBUG:
    logging.basicConfig(filename=os.path.join(app.instance_path,'app_debug.log'), level=logging.INFO)
else:
    logging.basicConfig(filename=os.path.join(app.instance_path,'app.log'), level=logging.INFO)
node=platform.node()
logger.info(node)
logger.info("DEBUG "+str(DEBUG))

logger.info("DIRECTORY "+DIRECTORY)

# Generate the secret key
# os.urandom(32).hex()
# secrets.token_hex(32)
app.config["SECRET_KEY"]=secrets.token_hex(32)

# serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# For postgresql, example://scott:tiger@localhost/project
if DEBUG:
    app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///debug_database.sqlite"
else:
    app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///database.sqlite"

app.config["SQLALCHEMY_BINDS"]={}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
app.config["REMEMBER_COOKIE_NAME"]="remember_token"
app.config["REMEMBER_COOKIE_DURATION"]=datetime.timedelta(days=365)
app.config["REMEMBER_COOKIE_DOMAIN"]=None
app.config["REMEMBER_COOKIE_PATH"]="/"
app.config["REMEMBER_COOKIE_SECURE"]=False
app.config["REMEMBER_COOKIE_HTTPONLY"]=True
app.config["REMEMBER_COOKIE_REFRESH_EACH_REQUEST"]=False
app.config["REMEMBER_COOKIE_SAMESITE"]=None
app.config["DEVICE_PORT"]="COM11"
app.config["DEVICE_LOCATION"]="High Bay"

database=SQLAlchemy()
database.init_app(app)

# SQL Alchemy data types: https://docs.sqlalchemy.org/en/20/core/type_basics.html
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/
class Monitor(database.Model):
    __tablename__="monitor"
    id=database.Column(database.Integer,primary_key=True)
    serial=database.Column(database.String(32),nullable=False)
    location=database.Column(database.String(32),nullable=False)
    temperature=database.Column(database.Numeric,unique=False)
    humidity=database.Column(database.Numeric,unique=False)
    created=database.Column(database.DateTime,default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))

# Create variables for templates to use
@app.context_processor
def template_constants():
    return dict(VERSION="V10.31.24",
                DEBUG=DEBUG,
                DEVELOPMENT=DEVELOPMENT,
                LOCATION=app.config["DEVICE_LOCATION"]
                )
@app.context_processor
def utility_processor():
    return dict(round=round)
# Redirect errors through styled html page
@app.errorhandler(404)
def page_not_found(e):
    flash(e,"danger")
    return render_template("base.html")

@app.route("/",methods=["GET","POST"])
def index():
    return render_template("index.html")

@app.route("/view",methods=["GET","POST"])
def view():
    if request.method=="POST":
        # location=request.form.get("location")
        start_date=request.form.get("start-date")
        end_date=request.form.get("end-date")
        try:
            if start_date and end_date:
                start_datetime=datetime.datetime.strptime(start_date,"%Y-%m-%d")
                end_datetime=datetime.datetime.strptime(end_date,"%Y-%m-%d")
                rows=Monitor.query.filter(start_datetime<=Monitor.created,Monitor.created<=end_datetime).all()
            elif start_date:
                start_datetime=datetime.datetime.strptime(start_date,"%Y-%m-%d")
                rows=Monitor.query.filter(start_datetime<=Monitor.created).all()
            elif end_date:
                end_datetime=datetime.datetime.strptime(end_date,"%Y-%m-%d")
                rows=Monitor.query.filter(Monitor.created<=end_datetime).all()
            else:
                flash('You must have a valid "Start Date" or "End Date"!','danger')
                return render_template("view.html")
            return render_template("view.html",data=rows)
        except:
            flash('Date must be in the format "mm/dd/yyyy"!','danger')
            return render_template("view.html")
    else:
        return render_template("view.html")

@app.route("/live",methods=["GET"])
def live():
    return render_template("live.html",temperature=temperature,humidity=humidity)

@app.route("/data",methods=["GET"])
def data():
    global temperature, humidity
    return jsonify(dict(temperature=temperature,humidity=humidity))

def update():
    global device,temperature,humidity
    with app.app_context():
        timer=time.time()
        while 1:
            device.flush()
            try:
                while 1:
                    data=device.readline().decode()
                    if not data.startswith("#"):
                        break
                data.replace("\r\n","")
            except Exception as E:
                device.open()
                data=device.readline().decode().replace("\r\n","")
            if time.time()-timer>=10:
                id, temperature, humidity, touch=data.split(",")
            if time.time()-timer>=1800:
                row=Monitor(serial=id,location=app.config["DEVICE_LOCATION"],temperature=temperature,humidity=humidity)
                database.session.add(row)
                database.session.commit()

if __name__=="__main__":
    # Create the database on first run
    with app.app_context():
        database.create_all()
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            temperature=None
            humidity=None
            device=serial.Serial(port=app.config["DEVICE_PORT"])
            thread=threading.Thread(target=update,daemon=True)
            thread.start()
    # Run the debug no matter what
    if DEBUG or DEVELOPMENT:
        app.run(host="0.0.0.0",port=443,debug=True,ssl_context="adhoc")
    else:
        hostname=socket.gethostname()
        host=socket.gethostbyname(hostname)
        logger.info(hostname)
        logger.info(host)
        logger.info("Serving at https://"+host+":80")
        waitress.serve(app, host=host, port = 80, url_scheme = 'https')