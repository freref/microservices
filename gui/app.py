from flask import Flask, render_template, redirect, request, url_for, make_response
import requests
from flasgger import Swagger

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

app = Flask(__name__)
swagger = Swagger(app, config=swagger_config)

AUTH_SERVICE_URL = "http://auth:5000"
EVENTS_SERVICE_URL = "http://events:5000"

# The Username & Password of the currently logged-in User, this is used as a pseudo-cookie, as such this is not session-specific.
username = None
password = None

session_data = dict()


def save_to_session(key, value):
    session_data[key] = value


def load_from_session(key):
    return session_data.pop(key) if key in session_data else None  # Pop to ensure that it is only used once


def succesful_request(r):
    return r.status_code == 200 or r.status_code == 201


# ================================
# FEATURE (list of public events)
#
# Retrieve the list of all public events. The webpage expects a list of (title, date, organizer) tuples.
# Try to keep in mind failure of the underlying microservice
# =================================
@app.route("/")
def home():
    global username

    if username is None:
        return render_template('login.html', username=username, password=password)
    else:
        response = requests.get(f"{EVENTS_SERVICE_URL}/events/", json={"is_public": True})
        # Destructure the response to get the events
        events = response.json().get('events', [])
        public_events = [(event['title'], event['date'], event['organizer']) for event in events]

        return make_response(render_template('home.html', username=username, password=password, events = public_events), response.status_code)
    
#==========================
# FEATURE (create an event)
#
# Given some data, create an event and send out the invites.
#==========================
@app.route("/event", methods=['POST'])
def create_event():
    """
    Create an event
    ---
    tags:
        - Events
    parameters:
        - name: title
          in: formData
          type: string
          required: true
        - name: description
          in: formData
          type: string
          required: true
        - name: date
          in: formData
          type: string
          required: true
        - name: publicprivate
          in: formData
          type: string
          required: true
        - name: invites
          in: formData
          type: string
          required: false
    responses:
        201:
            description: Event created
        400:
            description: Event creation failed
    """
    title, description, date, publicprivate, invites = request.form['title'], request.form['description'], request.form['date'], request.form['publicprivate'], request.form['invites']

    response = requests.post(f"{EVENTS_SERVICE_URL}/events/", json={
        "date": date,
        "organizer": username,
        "title": title,
        "description": description,
        "is_public": publicprivate == "public"
    })

    if (response.status_code != 201):
        return make_response("Event creation failed", response.status_code)

    # TODO: send invites

    return redirect('/')


@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    calendar_user = request.form['calendar_user'] if 'calendar_user' in request.form else username

    # ================================
    # FEATURE (calendar based on username)
    #
    # Retrieve the calendar of a certain user. The webpage expects a list of (id, title, date, organizer, status, Public/Private) tuples.
    # Try to keep in mind failure of the underlying microservice
    # =================================

    success = True # TODO: this might change depending on if the calendar is shared with you

    if success:
        calendar = [(1, 'Test event', 'Tomorrow', 'Benjamin', 'Going', 'Public')]  # TODO: call
    else:
        calendar = None


    return render_template('calendar.html', username=username, password=password, calendar_user=calendar_user, calendar=calendar, success=success)

@app.route('/share', methods=['GET'])
def share_page():
    return render_template('share.html', username=username, password=password, success=None)

@app.route('/share', methods=['POST'])
def share():
    share_user = request.form['username']

    #========================================
    # FEATURE (share a calendar with a user)
    #
    # Share your calendar with a certain user. Return success = true / false depending on whether the sharing is succesful.
    #========================================

    success = True  # TODO
    return render_template('share.html', username=username, password=password, success=success)


@app.route('/event/<eventid>')
def view_event(eventid):

    # ================================
    # FEATURE (event details)
    #
    # Retrieve additional information for a certain event parameterized by an id. The webpage expects a (title, date, organizer, status, (invitee, participating)) tuples.
    # Try to keep in mind failure of the underlying microservice
    # =================================

    success = True # TODO: this might change depending on whether you can see the event (public, or private but invited)

    if success:
        event = ['Test event', 'Tomorrow', 'Benjamin', 'Public', [['Benjamin', 'Participating'], ['Fabian', 'Maybe Participating']]]  # TODO: populate this with details from the actual event
    else:
        event = None  # No success, so don't fetch the data

    return render_template('event.html', username=username, password=password, event=event, success = success)

@app.route("/login", methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
        - Auth
    parameters:
        - name: username
          in: formData
          type: string
          required: true
        - name: password
          in: formData
          type: string
          required: true
    responses:
        200:
            description: Login successful
        401:
            description: Login failed
    """
    req_username, req_password = request.form['username'], request.form['password']

    response = requests.post(f"{AUTH_SERVICE_URL}/login/", json={
        "username": req_username,
        "password": req_password
    })

    success = succesful_request(response)
    save_to_session('success', success)

    if success:
        global username, password

        username = req_username
        password = req_password
    
    return make_response(render_template('login.html', username=username, password=password, success=success, login=True), response.status_code)

@app.route("/register", methods=['POST'])
def register():
    """
    User Registration
    ---
    tags:
        - Auth
    parameters:
        - name: username
          in: formData
          type: string
          required: true
        - name: password
          in: formData
          type: string
          required: true
    responses:
        201:
            description: Registration successful
        400:
            description: Registration failed
    """
    req_username, req_password = request.form['username'], request.form['password']

    response = requests.post(f"{AUTH_SERVICE_URL}/register/", json={
        "username": req_username,
        "password": req_password
    })

    success = succesful_request(response)
    save_to_session('success', success)

    if success:
        global username, password

        username = req_username
        password = req_password
    
    return make_response(render_template('login.html', username=username, password=password, success=success, registration=True), response.status_code)

@app.route('/invites', methods=['GET'])
def invites():
    #==============================
    # FEATURE (list invites)
    #
    # retrieve a list with all events you are invited to and have not yet responded to
    #==============================

    my_invites = [(1, 'Test event', 'Tomorrow', 'Benjamin', 'Private')] # TODO: process
    return render_template('invites.html', username=username, password=password, invites=my_invites)

@app.route('/invites', methods=['POST'])
def process_invite():
    eventId, status = request.json['event'], request.json['status']

    #=======================
    # FEATURE (process invite)
    #
    # process an invite (accept, maybe, don't accept)
    #=======================

    pass # TODO: send to microservice

    return redirect('/invites')

@app.route("/logout")
def logout():
    global username, password

    username = None
    password = None
    return redirect('/')
