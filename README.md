# Spot Fleet Request

Web app created with Flask to monitor and launch spot fleet request and also to monitor those responses.  
This was a part of tasks provided by a company.

Database: `MongoDB` hosted on mLabs.com  
Frontend: basic `Bootstrap` and `Jinja2 Templating`

Hosted at: [spot-fleet-request.herokuapp.com/](https://spot-fleet-request.herokuapp.com/)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.


### Prerequisites

What things you need to install the software and how to install them

* Python 2.7.11
* MongoDB (installed or hosted)

### Installing

```
git clone https://github.com/raajitr/spot-fleet-request.git
cd spot-fleet-request/
```
Preferably start a virtual environment

```
pip install -r requirements.txt
```

### Create environment variables

```
export SECRET_KEY=anysecretkey
export MONGO_DBNAME=mongodbname
export MONGO_URI=mongodburi
```

### Start

```
export FLASK_APP=main.py
flask run
```
Or
```
python main.py
```

## Acknowledgement

* [BOTO 3 Documentations](https://boto3.readthedocs.io/en/latest/)
* [AWS EC2 Spot Documentation](https://aws.amazon.com/ec2/spot/)
* [World's Best WebDev Tool](https://www.google.com)
