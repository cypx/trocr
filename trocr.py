# imports needed for DB initialisation
from __future__ import with_statement
from contextlib import closing
# all the imports
import sqlite3
import string
import random
import time
import os
import shutil
import mimetypes
from PIL import Image
from PIL import ExifTags
from uuid import uuid4
from flask import Flask, request, session, g, redirect, url_for, \
	abort, render_template, flash, send_from_directory
from werkzeug import secure_filename
from werkzeug.contrib.cache import SimpleCache

# create application
app = Flask(__name__)
app.config.from_object('websiteconfig')
# create cache
cache = SimpleCache()


@app.errorhandler(404)
def page_not_found(e):
	error="Page not found"
	return render_template('error.html', error=error), 404

@app.errorhandler(403)
def page_not_allowed(e):
	error="forbidden, you are not allowed to access this page"
	return render_template('error.html', error=error), 403

@app.errorhandler(401)
def page_not_authorized(e):
	error="forbidden, you are not authorized to access this page"
	return render_template('error.html', error=error), 401

@app.errorhandler(413)
def upload_too_big(e):
	error="maximum upload size exceeded. You can't upload more than "+str((app.config['MAX_CONTENT_LENGTH'])/ 1024 / 1024)+"MB in once"
	return render_template('error.html', error=error), 413

def connect_db():
	#if database do not exist, create it
	if not os.path.isfile(app.config['DATABASE']):
		db=sqlite3.connect(app.config['DATABASE'])
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
			db.commit()
		closing(db)
	return sqlite3.connect(app.config['DATABASE'])

def allowed_file(filename):
	if not app.config['RESTRICT_EXTENSIONS']:
		return '.' in filename
	return '.' in filename and \
		(filename.lower()).rsplit('.', 1)[1] in (app.config['ALLOWED_EXTENSIONS'])

def sizeof_fmt(num):
	for x in ['bytes','KB','MB','GB']:
		if num < 1024.0 and num > -1024.0:
			return "%3.1f%s" % (num, x)
		num /= 1024.0
	return "%3.1f%s" % (num, 'TB')

def create_thumb(filename,img_width):
	src_path=os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(filename.split('-')[1:4]) ,filename)
	dest_dir=os.path.join(app.config['THUMBNAIL_FOLDER'], str(img_width), '/'.join(filename.split('-')[1:4]))
	dest_path = os.path.join(dest_dir, filename)
	size = img_width, img_width*100
	image_format = ((mimetypes.guess_type(src_path))[0]).rsplit('/', 1)[1]
	if not os.path.exists(dest_dir):os.makedirs(dest_dir)
	if image_format in (app.config['EXCLUDED_FROM_THUMBNAIL']):
		try:
			shutil.copyfile(src_path,dest_path)
		except IOError:
			print("cannot create thumbnail for '%s'" % filename)
	else:
		try:
			im = Image.open(src_path)
			if im._getexif() is not None:
				exif=dict((ExifTags.TAGS[k], v) for k, v in im._getexif().items() if k in ExifTags.TAGS)
				if 'Orientation' in exif:
					if   exif['Orientation'] == 3 :
						im=im.rotate(180, expand=True)
					elif exif['Orientation'] == 6 :
						im=im.rotate(270, expand=True)
					elif exif['Orientation'] == 8 :
						im=im.rotate(90, expand=True)
				if 'orientation' in exif:
					if   exif['orientation'] == 3 :
						im=im.rotate(180, expand=True)
					elif exif['orientation'] == 6 :
						im=im.rotate(270, expand=True)
					elif exif['orientation'] == 8 :
						im=im.rotate(90, expand=True)
			im.thumbnail(size, Image.ANTIALIAS)
			im.save(dest_path)
		except IOError:
			print("cannot create thumbnail for '%s'" % filename)

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	g.db.close()

@app.route('/galleries')
def show_galleries():
	if not session.get('logged_in'):
		abort(401)
	currentpage = request.args.get('p', '')
	if currentpage == "": currentpage="1"
	cur = g.db.execute('SELECT distinct gallery_id FROM entries ORDER BY id desc')
	all_galleries = [dict(id=row[0]) for row in cur.fetchall()]
	selected_galleries = []
	start_from_gallery = app.config['ENTRY_BY_PAGE']*(int(currentpage)-1)
	end_to_gallery = (app.config['ENTRY_BY_PAGE']*int(currentpage))
	if int(currentpage)>1: previouspage=int(currentpage)-1
	else: previouspage=0
	if end_to_gallery < len(all_galleries): nextpage=int(currentpage)+1
	else: nextpage=0
	for gallery in range(start_from_gallery ,end_to_gallery):
		if gallery < len(all_galleries):
			cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE gallery_id="{gid}" ORDER BY id asc;'.format(
			gid=all_galleries[gallery]['id']))
			gallery_entries = [dict(
					title=row[0],
					date=time.strftime("%D %H:%M", time.localtime(int(row[1]))),
					id=row[3].rsplit('.', 1)[0],
					descr=row[2], filename=row[3],
					size=sizeof_fmt(row[4]),
					mime=row[5],
					type=row[5].split("/")[0],
					gallery_id=row[6],
					author_id=row[7]
					) for row in cur.fetchall()]
			selected_galleries.append(dict(id=all_galleries[gallery]['id'],entries=gallery_entries))
	page_rendered= render_template('show_galleries.html',
		galleries=selected_galleries,
		previouspage=previouspage,
		nextpage=nextpage,
		requested_gallery="")
	return page_rendered

@app.route('/')
def show_entries():
	requested_id = request.args.get('i', '')
	requested_gallery = request.args.get('g', '')
	currentpage = request.args.get('p', '')
	if currentpage == "": currentpage="1"
	if not session.get('logged_in'):
		if requested_id != "":
			cached_page=cache.get('i'+requested_id+'gp')
		elif requested_gallery != "":
			cached_page=cache.get('ig'+requested_gallery+'p'+currentpage)
		else:
			cached_page = None
		if cached_page is not None:
			return cached_page
		logged = False
	else:
		logged = True
	if (requested_id == '') & (requested_gallery == '') & (logged):
		if session['id'] in app.config['ADMINS']:
			cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries ORDER BY id desc')
		else:
			cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE author_id="{aid}" ORDER BY id desc'.format(
			aid=session['id']))
	elif (requested_id != ''):
		cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE filename like "{pid}.%" ORDER BY id desc;'.format(
			pid=requested_id))
	elif (requested_gallery != ''):
		cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE gallery_id="{gid}" ORDER BY id asc;'.format(
			gid=requested_gallery))
	else:
		cur = g.db.cursor()
	all_entries = [dict(
		title=row[0],
		date=time.strftime("%D %H:%M", time.localtime(int(row[1]))),
		id=row[3].rsplit('.', 1)[0],
		descr=row[2], filename=row[3],
		size=sizeof_fmt(row[4]),
		mime=row[5],
		type=row[5].split("/")[0],
		gallery_id=row[6],
		author_id=row[7]
		) for row in cur.fetchall()]
	selected_entries = []
	start_from_entry = app.config['ENTRY_BY_PAGE']*(int(currentpage)-1)
	end_to_entry = (app.config['ENTRY_BY_PAGE']*int(currentpage))-1
	if int(currentpage)>1: previouspage=int(currentpage)-1
	else: previouspage=0
	if end_to_entry < len(all_entries): nextpage=int(currentpage)+1
	else: nextpage=0
	for entry in range(start_from_entry ,end_to_entry):
		if entry < len(all_entries):
			selected_entries.append(all_entries[entry])
	page_rendered= render_template('show_entries.html',
		entries=selected_entries,
		previouspage=previouspage,
		nextpage=nextpage,
		requested_gallery=requested_gallery,
		requested_id=requested_id,
		entries_number=len(selected_entries),
		max_upload_size=str((app.config['MAX_CONTENT_LENGTH'])/ 1024 / 1024))
	if not logged:
		if requested_id != "":
			cache.set('i'+requested_id+'gp', page_rendered, timeout=60 * 60)
		elif requested_gallery != "":
			cache.set('ig'+requested_gallery+'p'+currentpage, page_rendered, timeout=60 * 60)
	return page_rendered

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	allowed = app.config['USERS'].copy()
	allowed.update(app.config['ADMINS'])
	if request.method == 'POST':
		if request.form['username'] not in allowed:
			error = 'Invalid username'
		elif request.form['password'] != allowed.get(request.form['username']):
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			session['id'] = request.form['username']
			if session['id'] in app.config['ADMINS']:
				session['admin'] = True
			else:
				session['admin'] = False
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	session.pop('id', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))

@app.route('/data/<filename>')
def uploaded_file(filename):
	return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(filename.split('-')[1:4])), filename)

@app.route('/tb/<int:size>/<filename>')
def show_thumbnail(filename,size):
	if size not in app.config['ALLOWED_THUMBNAIL_SIZE']:
		abort(401)
	file_dir=os.path.join(app.config['THUMBNAIL_FOLDER'], str(size), '/'.join(filename.split('-')[1:4]))
	file_path=os.path.join(file_dir, filename)
	if not os.path.exists(file_path):
		create_thumb(filename,size)
	return send_from_directory(file_dir,filename)

@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	if not request.files['file']:
		flash('Aborted, you should provide at least one file')
		return redirect(url_for('show_entries'))
	uploaded_files = request.files.getlist("file")
	if request.form['requested_gallery']=="":
		gallery_uuid=str(uuid4())
	else:
		gallery_uuid=request.form['requested_gallery']
	add_success=0
	add_fail=0
	for file in uploaded_files:
		file.filename=file.filename
		type(file.filename)
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
			g.db.execute('INSERT INTO entries (title, author_id, gallery_id, date, descr, filename, size, mime) VALUES ("{title}", "{aid}", "{gid}", "{date}", "{descr}", "{filename}", "{size}", "{mime}");'.format(
				title=file_title,
				aid=session.get('id'),
				gid=gallery_uuid,
				date=time.time(),
				descr="",
				filename=file_name,
				size=fileinfo.st_size,
				mime=(mimetypes.guess_type(file_path))[0]))
			g.db.commit()
			add_success=add_success+1
		else:
			add_fail=add_fail+1
	if add_success!=0:flash(str(add_success)+' file(s) was successfully posted')
	if add_fail!=0:flash(str(add_fail)+' file(s) aborted, corrupt or unallowed file')
	if 'addinfo' in request.form:
		return redirect(url_for('edit_entry')+"?g="+gallery_uuid)
	else:
		return redirect(url_for('show_entries'))

@app.route('/edit', methods=['GET', 'POST'])
def edit_entry():
	if not session.get('logged_in'):
		abort(401)
	if request.method == 'POST':
		update_success=0
		del_success=0
		for entry_id in request.form.getlist("entry_id"):
			g.db.execute('UPDATE entries  SET title="{title}", descr="{descr}" WHERE filename like "{pid}.%";'.format(
				pid=entry_id,
				title=request.form['title'+"_"+entry_id].encode('utf-8'),
				descr=request.form['descr'+"_"+entry_id].encode('utf-8')))
			g.db.commit()
			update_success=update_success+1
		for del_id in request.form.getlist("del_id"):
			cur = g.db.execute('SELECT filename FROM entries WHERE filename like "{pid}.%"'.format(pid=del_id))
			filename = cur.fetchone()[0]
			if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(filename.split('-')[1:4]), filename)):
				os.remove(os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(filename.split('-')[1:4]), filename))
			for dir_level in range(4,1,-1):
				if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(filename.split('-')[1:dir_level]))):
					rm_dir=os.path.join(app.config['UPLOAD_FOLDER'], '/'.join(filename.split('-')[1:dir_level]))
					if os.listdir(rm_dir) == []:
						os.rmdir(rm_dir)
			for size in app.config['ALLOWED_THUMBNAIL_SIZE']:
				if os.path.exists(os.path.join(app.config['THUMBNAIL_FOLDER'], str(size), '/'.join(filename.split('-')[1:4]), filename)):
					os.remove(os.path.join(app.config['THUMBNAIL_FOLDER'], str(size), '/'.join(filename.split('-')[1:4]), filename))
				for dir_level in range(4,1,-1):
					if os.path.exists(os.path.join(app.config['THUMBNAIL_FOLDER'], str(size), '/'.join(filename.split('-')[1:dir_level]))):
						rm_dir=os.path.join(app.config['THUMBNAIL_FOLDER'], str(size), '/'.join(filename.split('-')[1:dir_level]))
						if os.listdir(rm_dir) == []:
							os.rmdir(rm_dir)
			g.db.execute('DELETE FROM entries  WHERE filename like "{pid}.%";'.format(pid=del_id))
			g.db.commit()
			del_success=del_success+1
			update_success=update_success-1
		if update_success!=0:flash(str(update_success)+' file(s) was successfully updated')
		if del_success!=0:flash(str(del_success)+' file(s) was successfully deleted')
		for entry_id in request.form.getlist("entry_id"):
			cache.delete('i'+entry_id+'gp')
		for gallery_id in request.form.getlist("gallery_id"):
			cache.delete('ig'+gallery_id+'p')
			gallery_page=1
			cached_page=cache.delete('ig'+str(gallery_id)+'p'+str(gallery_page))
			while cached_page is not None:
				gallery_page=gallery_page+1
				cached_page=cache.delete('ig'+str(gallery_id)+'p'+str(gallery_page))
		return redirect(url_for('show_entries'))
	if request.method == 'GET':
		requested_id = request.args.get('i', '')
		requested_gallery = request.args.get('g', '')
		if (requested_id == '') & (requested_gallery == ''):
			if session['id'] in app.config['ADMINS']:
				cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries ORDER BY id desc')
			else:
				cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE author_id="{aid}" ORDER BY id desc'.format(
				aid=session['id']))
		elif (requested_id != ''):
			if session['id'] in app.config['ADMINS']:
				cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE filename LIKE "{pid}.%" ORDER BY id desc;'.format(
					pid=requested_id))
			else:
				cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE filename LIKE "{pid}.%" AND author_id="{aid}" ORDER BY id desc;'.format(
					aid=session['id'],
					pid=requested_id))
		elif (requested_gallery != ''):
			if session['id'] in app.config['ADMINS']:
				cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE gallery_id="{gid}" ORDER BY id asc;'.format(
				gid=requested_gallery))
			else:
				cur = g.db.execute('SELECT title, date, descr, filename, size, mime, gallery_id, author_id FROM entries WHERE gallery_id="{gid}" AND author_id="{aid}" ORDER BY id asc;'.format(
				aid=session['id'],
				gid=requested_gallery))
		entries = [dict(
			title=row[0],
			date=time.strftime("%D %H:%M",
			time.localtime(int(row[1]))),
			id=row[3].rsplit('.', 1)[0],
			descr=row[2],
			filename=row[3],
			size=sizeof_fmt(row[4]),
			mime=row[5],
			type=row[5].split("/")[0],
			gallery_id=row[6],
			author_id=row[7]) for row in cur.fetchall()]
		return render_template('edit_entries.html', entries=entries)

if __name__ == '__main__':
	app.run()
