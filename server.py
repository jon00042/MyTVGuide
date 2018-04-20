import bcrypt
import db.data_layer as db
import json
import pprint
import re
import requests
import sqlalchemy
import urllib.parse

from flask import Flask, session, request, redirect, render_template, flash, url_for

app = Flask(__name__)
app.secret_key = '0d599f0ec05c3bda8c3b8a68c32a1b47'

EMAIL_REGEX = re.compile(r'^([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$')
TVMAZE_API = 'http://api.tvmaze.com/'

@app.route('/')
def index():
    if ('shows' not in session):
        session['shows'] = []
    session['likes'] = {}
    if ('user_id' in session):
        redo_shows = len(session['shows']) == 0
        user = db.get_user_by_id(session['user_id'])
        likes = user.likes.all()
        if (type(likes) == list):
            for like in likes:
                (session['likes'])[str(like.show_id)] = 1
                if (redo_shows):
                    show_item = {}
                    show_item['title'] = like.show.title
                    show_item['image_url'] = like.show.image_url
                    show_item['show_id'] = str(like.show.id)
                    if show_item['image_url'] is None:
                        show_item['image_url'] = url_for('static', filename='images/no-photo.jpg')
                    session['shows'].append(show_item)
    print(session)
    return render_template('index.html')

@app.route('/reset')
def reset():
    if ('have_search' in session):
        del(session['have_search'])
    session['shows'] = []
    return redirect(url_for('index'))

@app.route('/register_form')
def register_form():
    return render_template('register_form.html')

@app.route('/register', methods=['POST'])
def register():
    is_valid = True
    for field in [ 'email', 'fullname', 'password' ]:
        if (len(request.form[field]) <= 0):
            flash('{} cannot be empty!'.format(field))
            is_valid = False
    if (request.form['password'] != request.form['confirm']):
        flash('passwords do not match!')
        is_valid = False
    if (not is_valid):
        return redirect(url_for('register_form'))
    user = None
    try:
        hashed_pw = bcrypt.hashpw(request.form['password'].encode('UTF-8'), bcrypt.gensalt())
        user = db.create_user(request.form['email'], request.form['fullname'], hashed_pw)
    except sqlalchemy.exc.IntegrityError:
        flash('email address already registered!')
    except Exception as ex:
        flash('internal error: {}'.format(ex))
    if (user is None):
        return redirect(url_for('register_form'))
    session.clear()
    session['user_id'] = user.id
    session['fullname'] = user.fullname
    return redirect(url_for('home'))

@app.route('/login_form')
def login_form():
    return render_template('login_form.html')

@app.route('/login', methods=['POST'])
def login():
    if (len(request.form['email']) < 1 or len(request.form['password']) < 1):
        flash('login fields cannot be empty!')
        return redirect(url_for('login_form'))
    user = None
    try:
        user = db.get_user_by_email(request.form['email'])
    except sqlalchemy.orm.exc.NoResultFound:
        flash('failed login attempt!')
    except Exception as ex:
        flash('internal error: {}'.format(ex))
    if (user is None):
        return redirect(url_for('login_form'))
    if (not bcrypt.checkpw(request.form['password'].encode('UTF-8'), user.hashed_pw)):
        flash('failed login attempt!')
        return redirect(url_for('login_form'))
    session.clear()
    session['user_id'] = user.id
    session['fullname'] = user.fullname
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    session['shows'] = []
    if (len(request.form['text']) == 0):
        return redirect(url_for('index'))
    safe_search_text = urllib.parse.quote(request.form['text'])
    search_url = TVMAZE_API + 'search/shows?q=' + safe_search_text
    print('requesting: {}'.format(search_url))
    resp = requests.get(search_url)
    if (resp is None):
        print('  null/empty response!')
        return redirect(url_for('index'))
    items = json.loads(resp.text)
    if (type(items) != list):
        print('  top json result not a list!')
        return redirect(url_for('index'))
    for item_kv in items:
        if (type(item_kv) != dict or 'show' not in item_kv):
            print('  no \'show\' key in json!')
            continue
        show_kv = item_kv['show']
        if (type(show_kv) != dict or 'id' not in show_kv or 'name' not in show_kv):
            print('  no \'id\' or \'name\' key in \'show\' json!')
            continue
        if (show_kv['id'] is None or show_kv['name'] is None):
            print('  null \'id\' or \'name\' in \'show\' json!')
            continue
        show_item = {}
        show_item['title'] = show_kv['name']
        show_item['image_url'] = None
        if ('image' in show_kv and type(show_kv['image']) == dict and 'medium' in (show_kv['image'])):
            show_item['image_url'] = (show_kv['image'])['medium']
        show = db.save_show(show_kv['id'], show_item['title'], show_item['image_url'])
        show_item['show_id'] = str(show.id)
        if show_item['image_url'] is None:
            show_item['image_url'] = url_for('static', filename='images/no-photo.jpg')
        session['shows'].append(show_item)
    session['have_search'] = 1
    return redirect(url_for('index'))

@app.route('/like/<show_id>')
def like(show_id):
    db.add_like(session['user_id'], show_id)
    if ('have_search' not in session):
        session['shows'] = []
    return redirect(url_for('index'))

@app.route('/unlike/<show_id>')
def unlike(show_id):
    db.del_like(session['user_id'], show_id)
    if ('have_search' not in session):
        session['shows'] = []
    return redirect(url_for('index'))

app.run(debug=True)

