import os
import configparser
import time
from flask import Flask, g, session, redirect, request, make_response, jsonify, render_template
from requests_oauthlib import OAuth2Session
from struct import pack, unpack

config = configparser.ConfigParser()
config.read('config.ini')
OAUTH2_CLIENT_ID = config['OAUTH2']['ClientID']
OAUTH2_CLIENT_SECRET = config['OAUTH2']['ClientSecret']
OAUTH2_REDIRECT_URI = 'http://distant-horizon.io/authresult'
LOGIN_EXPIRY = float(config['LOGIN']['Timeout'])
SERVER_URL = config['SERVERS']['Address']
API_BASE_URL = 'https://discordapp.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__, template_folder='', static_folder='', static_url_path='')
application = app #for passenger wsgi
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET

pending_logins = {}

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)

@app.route('/')
def index():
    if session.get('auth_choice_made') and session['auth_choice_made'] == True:
        session['auth_choice_made'] = False
        return render_template("Distant-Horizon.html")
    else:
        return render_template("Welcome.html")
    
@app.route('/quickplay')
def quick_play():
    session['auth_choice_made'] = True
    return redirect('./')
    
@app.route('/authenticate')
def request_auth():
    if session['oauth2_token']:
        session['auth_choice_made'] = True
        return redirect('./')
    discord = make_session(scope=['identify'])
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    ultimate_url = authorization_url + '&prompt=none'
    return redirect(ultimate_url)


@app.route('/authresult')
def auth_result():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    session['auth_choice_made'] = True
    response = make_response(redirect('./'))
    return response

@app.route('/controls')
def controls():
    return render_template("Controls.html")

@app.route('/about')
def about():
    return render_template("About.html")
    
@app.route('/me')
def me():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    return jsonify(user=user)

@app.route('/client_start_login')
def client_begin_login():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    client_key = generate_login_key()
    if client_key:
        pending_logins[client_key] = {
            'user_info': user,
            'expiry': time.time() + LOGIN_EXPIRY
        }        
        return jsonify(logged_in=True, user=user, client_key=client_key, server_address=get_server_address())
    else:
        return jsonify(logged_in=False, server_address=get_server_address())
        
@app.route('/server_check_login/<client_key>')
def server_check_login(client_key):
    clean_pending_logins()
    val = pending_logins[client_key]
    if val:
        user_data = val['user_info']
        return jsonify(found=True, user=user_data)
    else:
        return jsonify(found=False)
        
def get_server_address():
    return SERVER_URL
    
def clean_pending_logins():
    current_time = time.time()
    for key in pending_logins:
        val = pending_logins[key]
        if val['expiry'] < current_time:
            del pending_logins[key]
            
def generate_login_key():
    tok = session.get('oauth2_token')
    if tok:
        hashval = hash(jsonify(token=tok))
        return str(unpack('i', pack('f', hashval))[0])
    else:
        return None
        
if __name__ == '__main__':
    app.run()