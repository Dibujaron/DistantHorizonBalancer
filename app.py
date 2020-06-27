import os
import configparser
from flask import Flask, g, session, redirect, request, make_response, jsonify, render_template
from requests_oauthlib import OAuth2Session

config = configparser.ConfigParser()
config.read('config.ini')
OAUTH2_CLIENT_ID = config['OAUTH2']['ClientID']
OAUTH2_CLIENT_SECRET = config['OAUTH2']['ClientSecret']
OAUTH2_REDIRECT_URI = 'http://distant-horizon.io/authresult'

API_BASE_URL = 'https://discordapp.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__, template_folder='', static_folder='', static_url_path='')
application = app #for passenger wsgi
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET

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
    if 'discord_token' in request.cookies:
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
    response.set_cookie('discord_token', str(token))
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


if __name__ == '__main__':
    app.run()