import os
import configparser
import time
import requests
import sys
import traceback
import json
from flask import Flask, g, session, redirect, request, make_response, jsonify, render_template
from requests_oauthlib import OAuth2Session
from struct import pack, unpack

config = configparser.ConfigParser(delimiters=('='))
config.read('config.ini')
OAUTH2_CLIENT_ID = config['OAUTH2']['ClientID']
OAUTH2_CLIENT_SECRET = config['OAUTH2']['ClientSecret']
OAUTH2_REDIRECT_URI = 'http://distant-horizon.io/authresult'
LOGIN_EXPIRY = float(config['LOGIN']['Timeout'])
SERVER_URL = config['SERVERS']['Address']
SERVER_SECRET = config['SERVERS']['Secret']

KNOWN_SERVER_LIST = config.items('SERVER_REGISTRY')
KNOWN_SERVERS = {}
for url, secret in KNOWN_SERVER_LIST:
    KNOWN_SERVERS[secret] = url
    
API_BASE_URL = 'https://discordapp.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__, template_folder='', static_folder='', static_url_path='')
application = app #for passenger wsgi
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET

active_servers = {}

requests.Session().verify = False

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

def load_build_time():
    timestr = ""
    with open('lastbuild.txt', 'r') as file:
        timestr = file.read()
    return int(timestr)
    
BUILD_TIME = load_build_time()

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
    if 'oauth2_token' in session: 
        session.pop('oauth2_token')
    return redirect('./tutorial_challenge')
    
@app.route('/tutorial_challenge')
def tutorial_challenge():
    has_tutorial = request.cookies.get('tutorial_done')
    if has_tutorial:
        return redirect('./')
    else:
        return render_template("TutorialChallenge.html")
        
@app.route('/tutorial_challenge_yes')
def tutorial_challenge_yes():
    resp = make_response(redirect('./'))
    resp.set_cookie('tutorial_done', "true",max_age=60*60*24*365)
    return resp
    
@app.route('/authenticate')
def request_auth():
    if 'oauth2_token' in session and session['oauth2_token']:
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
    response = make_response(redirect('./tutorial_challenge'))
    return response

@app.route('/guide')
def guide():
    if session.get('auth_choice_made') and session['auth_choice_made'] == True:
        session['auth_choice_made'] = False
    resp = make_response(render_template("Guide.html"))
    resp.set_cookie('tutorial_done', "true", max_age=60*60*24*365)
    return render_template("Guide.html")

@app.route('/about')
def about():
    return render_template("About.html")
    
@app.route('/me')
def me():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    return jsonify(user=user)

@app.route('/client_login')
def client_begin_login():
    try:
        serv = select_server()
        if not serv:
            return jsonify(logged_in=False, error='no servers registered')
        else:
            server_addr = serv[0]
            discord = make_session(token=session.get('oauth2_token'))
            user = discord.get(API_BASE_URL + '/users/@me').json()
            if user and "username" in user and "discriminator" in user:
                request_url = 'http://' + serv[0] + '/' + serv[1] + '/prepLogin/' + account_name_from_discord_data(user)
                server_response = requests.get(request_url, verify=False)
                if server_response.status_code == 200:
                    return jsonify(logged_in=True, discord_user=user, server_data=server_response.json(), server_address=server_addr)
                else:
                    raise ValueError("unable to connect to server at address " + server_addr) 
            else:
                print("unexpected discord response: ", user)
                return jsonify(logged_in=False, discord_user=None, server_address=server_addr)
    except Exception as e:
        return jsonify(success=False, err=traceback.format_exc())
        
@app.route('/account_data')
def get_account_data():
    serv = select_server()
    request_url = 'http://' + serv[0] + '/' + serv[1] + '/account/' + account_name_from_discord()
    print("proxying request for account data")
    return requests.get(request_url, verify=False).json()
    
@app.route('/create_actor', methods=["POST"])
def create_actor(): 
    try:
        acct_name = account_name_from_discord()
        if acct_name:
            req_json_dict = request.json
            serv = select_server()
            if not serv:
                return jsonify(success=False, err='no servers active')
            else:
                request_url = 'http://' + serv[0] + '/' + serv[1] + '/account/' + account_name_from_discord() + '/createActor'
                server_data = requests.post(request_url, data=json.dumps(req_json_dict), verify=False).json()
                return jsonify(success=True, acct_data=server_data)
        else:
            return jsonify(success=False, err='user not found')
    except Exception as e:
        return jsonify(success=False, err=traceback.format_exc())
   
@app.route('/delete_actor', methods=["POST"])
def delete_actor():
    try:
        acct_name = account_name_from_discord()
        if acct_name:
            req_json_dict = request.json
            serv = select_server()
            if not serv:
                return jsonify(success=False, err='no servers active')
            else:
                request_url = 'http://' + serv[0] + '/' + serv[1] + '/account/' + account_name_from_discord() + '/deleteActor'
                server_data = requests.post(request_url, data=json.dumps(req_json_dict), verify=False).json()
                return jsonify(success=True, acct_data=server_data)
        else:
            return jsonify(success=False, err='user not found')
    except Exception as e:
        return jsonify(success=False, err=traceback.format_exc())
    
@app.route('/build_time')
def get_build_time():
    return jsonify(time=BUILD_TIME)

@app.route('/issues')
def go_to_issues():
    return redirect("https://github.com/Dibujaron/DistantHorizonIssues/issues")

@app.route('/economy')
def go_to_economy():
    return redirect("https://docs.google.com/spreadsheets/d/16FyNIEnfyATNY45AEggCf3WCg6ayvVT-uxJWPeQ1Cls/edit#gid=0")
    
@app.route('/report_bug')
def report_bug():
    return redirect("https://github.com/Dibujaron/DistantHorizonIssues/issues/new")
    
@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    return response
    

@app.route('/server_heartbeat', methods=["POST"])
def server_heartbeat():
    try:
        payload = request.json
        server_secret = payload['secret']
        server_count = payload['player_count']
        server_limit = payload['server_limit']
        if server_secret in KNOWN_SERVERS:
            server_url = KNOWN_SERVERS[server_secret]
            active_servers[server_secret] = {
                'url': server_url,
                'active_players': server_count,
                'max_players': server_limit,
                'last_heartbeat': time.time()
            }
            return jsonify(success=True, num_servers=len(active_servers))
        else:
            return jsonify(success=False, err='server is not registered as a known server.')
    except Exception as e:
        return jsonify(success=False, err=traceback.format_exc())   
        
@app.route('/ecodata')
def get_eco_csv():
    serv = select_server()
    if not serv:
        return jsonify(success=False, err='no servers active')
    else:
        request_url = 'http://' + serv[0] + '/ecodata'
        server_data = requests.get(request_url).text
        return server_data
        
def select_server():
    return [SERVER_URL, SERVER_SECRET]
   #for serv_secret in active_servers:
    #    serv_data = active_servers[serv_secret]
    #    #todo balancing algorithm, right now we just return the first one.
    #    serv_url = serv_data.url
    #    return [serv_url, serv_secret]
    #return None
    
def account_name_from_discord():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    return account_name_from_discord_data(user)
    
def account_name_from_discord_data(discord_data):
    if discord_data and "username" in discord_data and "discriminator" in discord_data:
        return discord_data["username"] + discord_data["discriminator"]
    else:
        return None

if __name__ == '__main__':
    app.run()