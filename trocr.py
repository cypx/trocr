#!/usr/bin/env python
# -*- coding: utf-8 -*-

# imports needed for DB initialisation
from __future__ import with_statement
from contextlib import closing
# all the imports
import sqlite3
import string
import random
import time
import os
import mimetypes
from uuid import uuid4
from flask import Flask, request, session, g, redirect, url_for, \
	abort, render_template, flash, send_from_directory
from werkzeug import secure_filename

# configuration
DATABASE = os.getcwd()+'/trocr.db'
DEBUG = True
SECRET_KEY = 'replace by your own key'
USERNAME = 'admin'
PASSWORD = 'default'
UPLOAD_FOLDER = os.getcwd()+'/data'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'zip', 'tar', 'gz', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3','webm'])
IMAGE_FORMATS = set(['jpg','jpeg','gif','png','bmp','tiff','svg'])
VIDEO_FORMATS = set(['mp4','webm','ogg'])
AUDIO_FORMATS = set(['wav','mp3','ogg','aac','mpeg'])

# create application
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql') as f:
			db.cursor().executescript(f.read())
		db.commit()

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	g.db.close()

@app.route('/')
def show_entries():
	searchword = request.args.get('i', '')
	if not session.get('logged_in'):
		logged=False
	else:
		logged=True
	if (searchword == '') & (logged):
		cur = g.db.execute('select title, date, descr, filename, size, mime, gallery_id from entries order by id desc')
	else:
		cur = g.db.execute('select title, date, descr, filename, size, mime, gallery_id from entries where filename like "{pid}.%" or gallery_id="{pid}" order by id desc;'.format(
			pid=searchword))
	entries = [dict(title=row[0], date=time.strftime("%D %H:%M", time.localtime(int(row[1]))), id=row[3].rsplit('.', 1)[0], descr=row[2], filename=row[3], size=sizeof_fmt(row[4]), mime=row[5], type=row[5].split("/")[0], gallery_id=row[6]) for row in cur.fetchall()]
	return render_template('show_entries.html', entries=entries)

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))

@app.route('/data/<filename>')
def uploaded_file(filename):
	return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(filename.split('-')[1:4])), filename)

@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	if not request.files['file']:
		flash('Aborted, you should provide at least one file')
		return redirect(url_for('show_entries'))
	uploaded_files = request.files.getlist("file")
	gallery_uuid=str(uuid4())
	for file in uploaded_files:
		if file and allowed_file(file.filename):
			file_title=file.filename.rsplit('.', 1)[0]
			file_upload_name = secure_filename(file.filename)
			file_uuid=str(uuid4())
			file_name = file_uuid  + '.' + file.filename.rsplit('.', 1)[1]
			file_dir = os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(file_name.split('-')[1:4]))
			file_path = os.path.join(file_dir, file_name)
			if not os.path.exists(file_dir):
				os.makedirs(file_dir)
			file.save(file_path)
			fileinfo = os.stat(file_path)
			dictionnary=string.ascii_letters+string.digits # alphanumeric, upper and lowercase
			g.db.execute('insert into entries (title, author_id, gallery_id, date, descr, filename, size, mime) values ("{title}", "{aid}", "{gid}", "{date}", "{descr}", "{filename}", "{size}", "{mime}");'.format(
				title=file_title,
				aid=app.config['USERNAME'],
				gid=gallery_uuid,
				date=time.time(),
				descr="",
				filename=file_name,
				size=fileinfo.st_size,
				mime=(mimetypes.guess_type(file_path))[0]))
			g.db.commit()
			flash('New entry was successfully posted')
		else:
			flash('Aborted, corrupt or unallowed file')
	if 'addinfo' in request.form:
		return redirect(url_for('edit_entry')+"?i="+gallery_uuid)
	else:
		return redirect(url_for('show_entries'))

@app.route('/edit', methods=['GET', 'POST'])
def edit_entry():
	if not session.get('logged_in'):
		abort(401)
	if request.method == 'POST':
		for entry_id in request.form.getlist("entry_id"):

			g.db.execute('UPDATE entries  SET title="{title}", descr="{descr}" WHERE filename like "{pid}.%";'.format(
				pid=entry_id,
				title=request.form['title'+"_"+entry_id],
				descr=request.form['descr'+"_"+entry_id]))
			g.db.commit()
			flash('Entry was successfully updated')
		return redirect(url_for('show_entries'))
	if request.method == 'GET':
		searchword = request.args.get('i', '')
		if (searchword == ''):
			cur = g.db.execute('SELECT title, date, descr, filename, size, mime FROM entries order by id desc')
		else:
			cur = g.db.execute('SELECT title, date, descr, filename, size, mime FROM entries WHERE filename like "{pid}.%" or gallery_id="{pid}" order by id desc;'.format(
				pid=searchword))
		entries = [dict(title=row[0], date=time.strftime("%D %H:%M", time.localtime(int(row[1]))), id=row[3].rsplit('.', 1)[0], descr=row[2], filename=row[3], size=sizeof_fmt(row[4]), mime=row[5], type=row[5].split("/")[0]) for row in cur.fetchall()]
		return render_template('edit_entries.html', entries=entries)

if __name__ == '__main__':
	if not os.path.isfile(app.config['DATABASE']):
		init_db()
	if not os.path.exists(app.config['UPLOAD_FOLDER']):
		os.makedirs(app.config['UPLOAD_FOLDER'])
	app.run()

