import flask
from flask import render_template
from flask import request
from flask import url_for
import uuid
import sys
import json
import logging
import uuid

# Date handling
import arrow  # Replacement for datetime, based on moment.js
# import datetime # But we still need time
from dateutil import tz  # For interpreting local times
from datetime import datetime

# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2  # used in oauth2 flow

# Google API for services
from apiclient import discovery

# import Data structure
from Model import CalendarEvent

# Mongo database
from pymongo import MongoClient

###
# Globals
###
import config

if __name__ == "__main__":
    CONFIG = config.configuration()
else:
    CONFIG = config.configuration(proxied=True)

app = flask.Flask(__name__)
app.debug = CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)
app.secret_key = CONFIG.SECRET_KEY
MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST,
    CONFIG.DB_PORT,
    CONFIG.DB)

print("Using URL '{}'".format(MONGO_CLIENT_URL))

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = CONFIG.GOOGLE_KEY_FILE  # You'll need this
APPLICATION_NAME = 'MeetMe class project'

####
# Database connection per server process
###

try:
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, CONFIG.DB)
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

#############################
#
#  Pages (routed from URLs)
#  Login page from Credit: https://pythonspot.com/en/login-authentication-with-flask/
#
#############################


@app.route("/")
@app.route("/home")
def home():
    app.logger.debug("Entering home page")
    # get the unique id.
    unique_list = str(uuid.uuid4()).split("-")[0]
    unique_id = "".join(unique_list)
    flask.session["unique_id"] = unique_id
    app.logger.debug(unique_id)

    if flask.session.get["logined"]:
        return index()
    else:
        return render_template('login.html')


@app.route("/login", methods=['POST'])
def login():
    # Since this project doesn't require highly encrypt users' password and username
    # I didn't have some nice ways to hide them

    input_username = request.form.get('username')
    input_password = request.form.get('password')

    # Check username and password with database
    # if existing, check with password/username.
    # Otherwise create new one for new users
    right_user = collection.find_one({"username": input_username}) # it return None if find nothing
    if right_user:
        # the username exsits
        if input_password == right_user["password"]:
            app.logger.debug("You logged in! with exsiting account")
            flask.session["logined"] = True
        else:
            # wrong password
            app.logger.debug("Wrong password")
            flask.flash("Wrong password!")
            flask.session["logined"] = False
    else:
        # if the username doesn't exist, let us create one!
        user = {"username": input_username,
                "password": input_password}
        collection.insert_one(user)
        app.logger.debug("You logged in! with new account")
        flask.session["logined"] = True
    return home()


@app.route("/logout")
def logout():
    flask.session["logined"] = False
    return home()


@app.route("/index/")
def index():
    app.logger.debug("Entering index")
    app.logger.debug("index id: " + id)
    if 'begin_date' not in flask.session:
        init_session_values()
    return render_template('index.html')

@app.route("/app/<id>")
def workonMeeting(id):
    flask.session["unique_id"] = id
    # TODO set up id and time for members

    return home()


@app.route("/choose")
def choose():
    # We'll need authorization to list calendars
    # I wanted to put what follows into a function, but had
    # to pull it back here because the redirect has to be a
    # 'return'
    app.logger.debug("Checking credentials for Google calendar access")
    credentials = valid_credentials()
    if not credentials:
        app.logger.debug("Redirecting to authorization")
        return flask.redirect(flask.url_for('oauth2callback'))
    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    flask.g.calendars = list_calendars(gcal_service)
    return render_template('index.html')


####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
#  Protocol for use ON EACH REQUEST:
#     First, check for valid credentials
#     If we don't have valid credentials
#         Get credentials (jump to the oauth2 protocl)
#         (redirects back to /choose, this time with credentials)
#     If we do have valid credentials
#         Get the service object
#
#  The final result of successful authorization is a 'service'
#  object.  We use a 'service' object to actually retrieve data
#  from the Google services. Service objects are NOT serializable ---
#  we can't stash one in a cookie.  Instead, on each request we
#  get a fresh service object from our credentials, which are
#  serializable.
#  Note that after authorization we always redirect to /choose;
#  If this is unsatisfactory, we'll need a session variable to use
#  as a 'continuation' or 'return address' to use instead.
#
####

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value. 
    """
    if 'credentials' not in flask.session:
        return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
            credentials.access_token_expired):
        return None
    return credentials


def get_gcal_service(credentials):
    """
    We need a Google calendar 'service' object to obtain
    list of calendars, busy times, etc.  This requires
    authorization. If authorization is already in effect,
    we'll just return with the authorization. Otherwise,
    control flow will be interrupted by authorization, and we'll
    end up redirected back to /choose *without a service object*.
    Then the second call will succeed without additional authorization.
    """
    app.logger.debug("Entering get_gcal_service")
    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http_auth)
    app.logger.debug("Returning service")
    return service


@app.route('/oauth2callback')
def oauth2callback():
    """
    The 'flow' has this one place to call back to.  We'll enter here
    more than once as steps in the flow are completed, and need to keep
    track of how far we've gotten. The first time we'll do the first
    step, the second time we'll skip the first step and do the second,
    and so on.
    """
    app.logger.debug("Entering oauth2callback")
    flow = client.flow_from_clientsecrets(
        CLIENT_SECRET_FILE,
        scope=SCOPES,
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    # Note we are *not* redirecting above.  We are noting *where*
    # we will redirect to, which is this function.

    # The *second* time we enter here, it's a callback
    # with 'code' set in the URL parameter.  If we don't
    # see that, it must be the first time through, so we
    # need to do step 1.
    app.logger.debug("Got flow")
    if 'code' not in flask.request.args:
        app.logger.debug("Code not in flask.request.args")
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
        # This will redirect back here, but the second time through
        # we'll have the 'code' parameter set
    else:
        # It's the second time through ... we can tell because
        # we got the 'code' argument in the URL.
        app.logger.debug("Code was in flask.request.args")
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        flask.session['credentials'] = credentials.to_json()
        # Now I can build the service and execute the query,
        # but for the moment I'll just log it and go back to
        # the main screen
        app.logger.debug("Got credentials")
        return flask.redirect(flask.url_for('choose'))


#####
#
#  Option setting:  Buttons or forms that add some
#     information into session state.  Don't do the
#     computation here; use of the information might
#     depend on what other information we have.
#   Setting an option sends us back to the main display
#      page, where we may put the new information to use.
#
#####

@app.route('/setrange', methods=['POST'])
def setrange():
    """
    User chose a date range with the bootstrap daterange
    widget.
    """
    app.logger.debug("Entering setrange")
    flask.flash("Setrange gave us '{}'".format(
        request.form.get('daterange')))
    daterange = request.form.get('daterange')
    flask.session['daterange'] = daterange
    daterange_parts = daterange.split()
    app.logger.debug(daterange_parts)

    # Sample format for date range_parts:
    # ['11/16/2017', '5:00', '-', '12/29/2017', '4:30']

    flask.session['begin_date'] = interpret_date(daterange_parts[0])
    flask.session['end_date'] = interpret_date(daterange_parts[3])
    if flask.session['end_date'] < flask.session['begin_date']:
        raise ValueError("end_date must be after begin_date")
    flask.session['start_time'] = interpret_time(daterange_parts[1])
    flask.session['end_time'] = interpret_time(daterange_parts[4])
    if flask.session['end_time'] < flask.session['start_time']:
        raise ValueError("end_time must be after start_time")
    flask.session['real_start_time'] = splice_real_time(
        flask.session['begin_date'], flask.session['start_time'])
    flask.session['real_end_time'] = splice_real_time(
        flask.session['end_date'], flask.session['end_time'])

    app.logger.debug("Setrange parsed {} - {}  dates as {} - {}".format(
        daterange_parts[0], daterange_parts[3],
        flask.session['begin_date'], flask.session['end_date']))
    app.logger.debug("Setrange parsed {} - {}  time as {} - {}".format(
        daterange_parts[1], daterange_parts[4],
        flask.session['start_time'], flask.session['end_time']))
    app.logger.debug("real time is {} - {}".format(
        flask.session['real_start_time'], flask.session['real_end_time']))
    return flask.redirect(flask.url_for("choose"))


@app.route("/_select", methods=["POST"])
def select():
    """
    According to marked checkbox, re-direct to index.html
    """
    credentials = valid_credentials()
    if not credentials:
        app.logger.debug("Redirecting to authorization")
        return flask.redirect(flask.url_for('oauth2callback'))
    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Select calendars")
    tokens = flask.request.form.getlist("token")
    app.logger.debug("The token: {}".format(tokens))
    events_list_bycalendar = []  # store all events for every selected calendar
    for token in tokens:
        new_event_list = []
        for event in list_events(gcal_service, token):
            new_event_list.append(event)
        events_list_bycalendar.append(new_event_list)
    app.logger.debug(events_list_bycalendar)
    flask.session["translated_events"] = events_list_bycalendar
    flask.g.events = events_list_bycalendar
    return render_template('index.html')


@app.route("/_free", methods=["POST"])
def free():
    """
    According to marked checkbox in busy assignment, list free time for users
    """
    app.logger.debug("Checking credentials for searching free events")

    app.logger.debug("Search free time")
    marks = flask.request.form.getlist("mark")
    app.logger.debug("The mark: {}".format(marks))
    free_naive_events_list = []
    free_events_list = []
    busy_lists = flask.session["translated_events"]

    # get all selected events into a single list
    for calendar in busy_lists:
        free_events_list += calendar
    app.logger.debug(free_events_list)
    # translate these events back to object
    for event in free_events_list:
        free_naive_events_list.append(translator_dictToObject(event))
    app.logger.debug(free_naive_events_list)
    # we remove some events which are not in the right meeting time also some events which are marked as free time
    for mark in marks:
        for event in free_naive_events_list:
            if event.get_id() == mark:
                free_naive_events_list.remove(event)

    # My idea is pretty straightforward but takes long time
    # traverse the date range users picked. For each day, we find the free time
    # then append the free time into free_event_list
    start_date, start_time = flask.session['real_start_time'].split("T")
    end_date, end_time = flask.session['real_end_time'].split("T")
    days = diff_days(start_date, end_date)
    app.logger.debug(days)
    # Reminder: ISO format "2017/01/01T08:00:00-8:00"
    arrow_date = arrow.get(flask.session['real_start_time'])
    for i in range(days):
        # get the whole day object for each day
        new_arrow_date = arrow_date.shift(days=+i)
        date = new_arrow_date.isoformat().split("T")[0]
        whole_day = CalendarEvent.CalendarEvent(
            start_time, end_time, date, status="FREE")
        app.logger.debug(whole_day)
        # grab busy events in the same date
        single_day_events = CalendarEvent.Agenda()
        for event in free_naive_events_list:
            if event.get_date() != whole_day.get_date():
                single_day_events.append(event)

        app.logger.debug(single_day_events)

        # get the free time list for each single day
        free_time = single_day_events.complement(whole_day)
        app.logger.debug(free_time)
        free_naive_events_list += free_time.toList()
    app.logger.debug(free_naive_events_list)
    free_naive_events_list.sort(key=lambda e: e.get_start_time())
    free_translated_list = []
    for event in free_naive_events_list:
        free_translated_list.append(event.translator_classToDict())
    app.logger.debug(free_translated_list)
    flask.g.free_events = free_translated_list
    return render_template('index.html')


@app.route("/_dataAllin", methods=["POST"])
def dataAllin():
    """
    submit final free/busy time choosed by users
    """
    # TODO read all free events and store them into database according to the user name and instance id
    pass


@app.route("/_checkFinalFree", methods=["POST"])
def checkFinalFree():
    """
    Check final free time so far. It is only avaliable for creator
    """
    # TODO compute final free time and then render template
    pass

####
#
#   Initialize session variables
#
####


def init_session_values():
    """
    Start with some reasonable defaults for date and time ranges.
    Note this must be run in app context ... can't call from main. 
    """
    # Default date span = tomorrow to 1 week from now
    now = arrow.now('local')  # We really should be using tz from browser
    tomorrow = now.replace(days=+1)
    nextweek = now.replace(days=+7)
    flask.session["begin_date"] = tomorrow.floor('day').isoformat()
    flask.session["end_date"] = nextweek.ceil('day').isoformat()
    flask.session["daterange"] = "{} - {}".format(
        tomorrow.format("MM/DD/YYYY"),
        nextweek.format("MM/DD/YYYY"))
    # Default time span each day, 8 to 5
    flask.session["begin_time"] = interpret_time("8am")
    flask.session["end_time"] = interpret_time("5pm")


def splice_real_time(date, time):
    """
    Use date and time to splice and return a ISO format time
    Note:
        Due to the tiny bug in the "interpret_time" method,
        The real date/time format are not right.
        Also, I still hope can keep these original but not perfect methods here for re-using them
        So, splice_real_time method takes the responsibility to return a real time
    Args:
        date: a ISO format string, and it represents the real date but no time
            sample: 2017-11-13T00:00:00-08:00
        time: a ISO format string, and it represents the real time but wrong date
            sample: 2016-01-01T19:30:00-08:00
    """
    real_date = date.split("T")[0]
    real_time = time.split("T")[1]
    return real_date + "T" + real_time


def interpret_time(text):
    """
    Read time in a human-compatible format and
    interpret as ISO format with local timezone.
    May throw exception if time can't be interpreted. In that
    case it will also flash a message explaining accepted formats.
    """
    # I still keep these codes because I use splice_real_time to deal with this case
    app.logger.debug("Decoding time '{}'".format(text))
    time_formats = ["ha", "h:mma", "h:mm a", "H:mm"]
    try:
        as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
        as_arrow = as_arrow.replace(year=2016)  # HACK see below
        app.logger.debug("Succeeded interpreting time")
    except:
        app.logger.debug("Failed to interpret time")
        flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
                    .format(text))
        raise
    return as_arrow.isoformat()
    # HACK #Workaround
    # isoformat() on raspberry Pi does not work for some dates
    # far from now.  It will fail with an overflow from time stamp out
    # of range while checking for daylight savings time.  Workaround is
    # to force the date-time combination into the year 2016, which seems to
    # get the timestamp into a reasonable range. This workaround should be
    # removed when Arrow or Dateutil.tz is fixed.
    # on raspberry Pi --- failure is likely due to 32-bit integers on that platform)


def interpret_date(text):
    """
    Convert text of date to ISO format used internally,
    with the local time zone.
    """
    try:
        as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
            tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()


def next_day(isotext):
    """
    ISO date + 1 day (used in query to Google calendar)
    """
    as_arrow = arrow.get(isotext)
    return as_arrow.replace(days=+1).isoformat()


def diff_days(date1, date2):
    """
    return the days between two dates
    """
    d1 = datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.strptime(date2, "%Y-%m-%d")
    return abs((d2 - d1).days)


####
#
#  Functions (NOT pages) that return some information
#
####

def list_calendars(service):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict.
    The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")
    calendar_list = service.calendarList().list().execute()["items"]
    app.logger.debug(calendar_list)
    result = []
    for cal in calendar_list:
        kind = cal["kind"]
        id = cal["id"]
        if "description" in cal:
            desc = cal["description"]
        else:
            desc = "(no description)"
        summary = cal["summary"]
        # Optional binary attributes with False as default
        selected = ("selected" in cal) and cal["selected"]
        primary = ("primary" in cal) and cal["primary"]

        result.append(
            {"kind": kind,
             "id": id,
             "summary": summary,
             "selected": selected,
             "primary": primary,
             "description": desc
             })
    app.logger.debug(result)
    return sorted(result, key=cal_sort_key)


def list_events(service, calendar_id):
    """
    Given a specified calendar, return a list of events which belong
    to this calendar
    Args
        service: a google calendar service object
        calendar: a specified calendarId
    return:
        events, a sorted list of event according to start time
    """
    app.logger.debug("Begin to retrieve events of calendar")
    event_list = service.events().list(
        calendarId=calendar_id).execute()["items"]
    events = []
    for event in event_list:

        # Deal with some non-standard event entries
        if event["status"] == "cancelled":
            continue
        if "description" in event:
            desc = event["description"]
        else:
            desc = "no description for this event"
        try:
            start_time = event["start"]["dateTime"]
        except KeyError:
            continue
            # Initially, I want to deal with these edge cases which only have date
            # but I found them are really useless so I don't want to append them into list
            # start_time = event["start"]["date"]
        try:
            end_time = event["end"]["dateTime"]
        except KeyError:
            continue

        try:
            summary = event["summary"]
        except KeyError:
            continue
        id = event["id"]
        app.logger.debug(event_filter(start_time, end_time))
        if event_filter(start_time, end_time):
            # start_time sample: 2017/01/01T14:00:00-8:00
            events.append(
                {"id": id,
                 "summary": summary,
                 "description": desc,
                 "start_time": start_time,
                 "end_time": end_time,
                 }
            )
    events.sort(key=lambda e: e["start_time"])
    app.logger.debug(events)
    return events


def event_filter(event_start, event_end):
    """
    A event filter. Return true events if and only if the event happens or ends during the start/end date/time where users picked
    Args:
        event_start: a specified event time to start, ISO format
        event_end: a specified event time to end, ISO format
    return:
        True if the event is in the right time otherwise false
    """
    e_start_date, e_start_time = event_start.split("T")
    e_end_date, e_end_time = event_end.split("T")
    start_date, start_time = flask.session['real_start_time'].split("T")
    end_date, end_time = flask.session['real_end_time'].split("T")
    return ((start_date <= e_start_date <= e_end_date <= end_date) and
            (start_time <= e_start_time <= e_end_time <= end_time))


def translator_dictToObject(event):
    """
    translate events whose type is dictionary in python to type "Event"
    Args:
        event: a dictionary, which contains infos of an event
    return:
        event_obj: an Event object
    """
    s_time = event["start_time"].split("T")[1]
    e_time = event["end_time"].split("T")[1]
    date = event["start_time"].split("T")[0]
    id = event["id"]
    summary = event["summary"]
    desc = event["description"]
    event_obj = CalendarEvent.CalendarEvent(
        s_time, e_time, date, summary, desc, id)
    return event_obj


def cal_sort_key(cal):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
        selected_key = " "
    else:
        selected_key = "X"
    if cal["primary"]:
        primary_key = " "
    else:
        primary_key = "X"
    return primary_key, selected_key, cal["summary"]


#################
#
# Functions used within the templates
#
#################

@app.template_filter('fmtdate')
def format_arrow_date(date):
    try:
        normal = arrow.get(date)
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"


@app.template_filter('fmttime')
def format_arrow_time(time):
    try:
        normal = arrow.get(time)
        return normal.format("HH:mm")
    except:
        return "(bad time)"


#############


if __name__ == "__main__":
    # App is created above so that it will
    # exist whether this is 'main' or not
    # (e.g., if we are running under green unicorn)
    app.run(port=CONFIG.PORT, host="0.0.0.0")
