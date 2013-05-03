#!/usr/bin/env python
# encoding: utf-8
"""
__init__.py

The MIT License (MIT)

Copyright (c) 2013 Matt Ryan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import sys
from os import makedirs
from os.path import isfile, isdir, dirname, expanduser
import eyed3
import sqlite3 as sql

class AFLibrary:
	query_fields = [
		('song.name', 'title'),
		('song.path', 'path'),
		('song.base_path', 'base_path'),
		('song.track_num', 'track_num'),
		('song.disc_num', 'disc_num'),
		('album.name', 'album'),
		('album.track_count', 'track_count'),
		('album.disc_count', 'disc_count'),
		('album.year', 'year'),
		('artist.name', 'artist'),
		('publisher.name', 'publisher'),
		('genre.name', 'genre')
	]
	def __init__(self):
		self.dbname = expanduser('~/.audiofile/lib.db')
		if not isdir(dirname(self.dbname)):
			makedirs(dirname(self.dbname))
		con = sql.connect(self.dbname)
		# Figure out if we have the schema yet
		cur = con.cursor()
		cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
		count = cur.fetchone()[0]
		nTables = 5
		if count != nTables:
			self.clear_db(con)
		self.create_db(con)
		con.close()
			
	def clear_db(self, con):
		cur = con.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
		rows = cur.fetchall()
		for row in rows:
			cur.execute('DROP TABLE %s' % row[0])
		con.commit()
			
	def create_db(self, con):
		cur = con.cursor()
		cur.executescript("""
			CREATE TABLE IF NOT EXISTS publisher(id INTEGER PRIMARY KEY, name VARCHAR UNIQUE);
			CREATE TABLE IF NOT EXISTS genre(id INTEGER PRIMARY KEY, name VARCHAR UNIQUE);
			CREATE TABLE IF NOT EXISTS artist(id INTEGER PRIMARY KEY, name VARCHAR UNIQUE);
			CREATE TABLE IF NOT EXISTS album(id INTEGER PRIMARY KEY, name VARCHAR, artist_id INTEGER, track_count INTEGER, disc_count INTEGER DEFAULT 1, publisher_id INTEGER, year VARCHAR DEFAULT NULL, FOREIGN KEY(artist_id) REFERENCES artist(id), FOREIGN KEY(publisher_id) REFERENCES publisher(id));
			CREATE TABLE IF NOT EXISTS song(id INTEGER PRIMARY KEY, name VARCHAR, path VARCHAR, base_path VARCHAR, album_id INTEGER, artist_id INTEGER, genre_id INTEGER, track_num INTEGER, disc_num INTEGER, FOREIGN KEY(album_id) REFERENCES album(id), FOREIGN KEY(artist_id) REFERENCES artist(id), FOREIGN KEY(genre_id) REFERENCES genre(id));
			CREATE UNIQUE INDEX IF NOT EXISTS unique_album ON album(name,artist_id);
			CREATE UNIQUE INDEX IF NOT EXISTS unique_song ON song(name,album_id);
		""")
		con.commit()
				
	def add_mp3(self, path, base_path):
		ent = AFLibraryEntry()
		ent.apply_path(path, base_path)
		ent.save_to_db(self.dbname)
		
	def make_sql_from_query(self,qdict):
		sql = 'SELECT'
		for pair in self.query_fields:
			sql = '%s %s AS %s,' % (sql, pair[0], pair[1])
		sql = '%s FROM song, album, artist, genre, publisher' % sql.rstrip(',')
		w = 'WHERE'
		if qdict:
			for k,v in qdict.items():
				sql = "%s %s %s='%s'" % (sql, w, k.strip('\'').strip('"'), v.strip('\'').strip('"'))
				w = 'AND'
		for jl, jr in {
			'song.album_id':'album.id',
			'song.artist_id':'artist.id',
			'song.genre_id':'genre.id',
			'album.artist_id':'artist.id',
			'album.publisher_id':'publisher.id'
			}.items():
			sql = '%s %s %s=%s' % (sql, w, jl, jr)
			w = 'AND'
		return sql
		
	def get_songs(self, qdict):
		sqlstmt = self.make_sql_from_query(qdict)
		con = sql.connect(self.dbname)
		cur = con.cursor()
		cur.execute(sqlstmt)
		rows = cur.fetchall()
		for row in rows:
			ent = AFLibraryEntry()
			ent.apply_row(row)
			yield ent
		con.close()
		

class AFLibraryEntry:
	base_path = ''
	path = ''
	artist = ''
	album = ''
	title = ''
	track_num = 0
	total_tracks = 0
	disc_num = 0
	total_discs = 0
	publisher = ''
	year = ''
	genre = ''
	def __init__(self):
		pass
	def apply_path(self,path,base_path):
		self.base_path = base_path
		if isfile(path):
			mp3 = eyed3.load(path)
			self.path = path
			if mp3.tag:
				self.artist = mp3.tag.artist
				self.album = mp3.tag.album
				self.title = mp3.tag.title
				self.track_num, self.total_tracks = mp3.tag.track_num
				if not self.track_num:
					self.total_tracks = None
				self.disc_num, self.total_discs = mp3.tag.disc_num
				if not self.total_discs:
					self.total_discs = 1
				if not self.disc_num:
					self.disc_num = 1
				self.publisher = mp3.tag.publisher
				if not self.publisher:
					self.publisher = '(Unknown)'
				if mp3.tag.best_release_date:
					self.year = str(mp3.tag.best_release_date)
				if not self.year:
					self.year = ''
				if mp3.tag.genre:
					self.genre = mp3.tag.genre.name
	def apply_row(self,row):
		self.title = row[0]
		self.path = row[1]
		self.base_path = row[2]
		self.track_num = row[3]
		self.disc_num = row[4]
		self.album = row[5]
		self.total_tracks = row[6]
		self.total_discs = row[7]
		self.year = row[8]
		self.artist = row[9]
		self.publisher = row[10]
		self.genre = row[11]
	def __str__(self):
		song_line = '%s by %s' % (self.title, self.artist)
		album_line = '\tFound on %s' % self.album
		if self.track_num:
			album_line += ', track %d' % self.track_num
			if self.total_tracks:
				album_line += ' of %d' % self.total_tracks
		if self.disc_num:
			album_line += ', disc %d' % self.disc_num
			if self.total_discs:
				album_line += ' of %d' % self.total_discs
		publisher_line = '\tReleased by %s in %s' % (self.publisher, self.year)
		genre_line = '\tGenre: %s' % self.genre
		return '%s\n%s\n%s\n%s' % (song_line, album_line, publisher_line, genre_line)
	def save_to_db(self,dbname):
		dbconn = sql.connect(dbname)
		publisher_id = self.get_or_create_id('publisher',self.publisher,dbconn)
		genre_id = self.get_or_create_id('genre',self.genre,dbconn)
		artist_id = self.get_or_create_id('artist',self.artist,dbconn)
		album_id = None
		if artist_id and publisher_id:
			album_id = self.get_or_create_album_id(self.album,artist_id,self.total_tracks,self.total_discs,publisher_id,self.year,dbconn)
		if album_id and artist_id and genre_id:
			song_id = self.get_or_create_song_id(self.title,self.path,self.base_path,album_id,artist_id,genre_id,self.track_num,self.disc_num,dbconn)
		dbconn.close()
	def get_or_create_id(self,table,name,dbconn):
		if name and len(name):
			cur = dbconn.cursor()
			try:
				cur.execute("INSERT INTO %s(name) VALUES ('%s')" % (table,name))
				dbconn.commit()
				row_id = cur.lastrowid
			except sql.IntegrityError:
				cur.execute("SELECT id FROM %s WHERE name='%s' LIMIT 1" % (table,name))
				row_id = cur.fetchone()[0]
			return row_id
		return None
	def get_or_create_album_id(self,album,artist_id,total_tracks,total_discs,publisher_id,year,dbconn):
		if album and len(album):
			cur = dbconn.cursor()
			try:
				cur.execute("INSERT INTO album(name,artist_id,track_count,disc_count,publisher_id,year) VALUES (?,?,?,?,?,?)", (album,artist_id,total_tracks,total_discs,publisher_id,year,))
				dbconn.commit()
				row_id = cur.lastrowid
			except sql.IntegrityError:
				cur.execute("SELECT id FROM album WHERE name=? AND artist_id=? LIMIT 1", (album,artist_id,))
				row_id = cur.fetchone()[0]
			return row_id
		return None
	def get_or_create_song_id(self,song,path,base_path,album_id,artist_id,genre_id,track_num,disc_num,dbconn):
		if song and len(song):
			cur = dbconn.cursor()
			try:
				cur.execute("INSERT INTO song(name,path,base_path,album_id,artist_id,genre_id,track_num,disc_num) VALUES (?,?,?,?,?,?,?,?)", (song,path,base_path,album_id,artist_id,genre_id,track_num,disc_num,))
				dbconn.commit()
				row_id = cur.lastrowid
			except sql.IntegrityError:
				cur.execute("SELECT id FROM song WHERE name=? AND album_id=? LIMIT 1", (song,album_id,))
				row_id = cur.fetchone()[0]
			return row_id
		return None
		
class Pattern:
	'''Pattern for renaming MP3s:
	%a = artist
	%b = album
	%t = title
	%n = track number
	%N = total tracks
	%d = disc number
	%D = total discs
	%p = publisher
	%g = genre
	%y = year
	'''
	def __init__(self, p):
		for token in p.split('%'):
			if len(token):
				c = token[0]
				if c != 'a' and c != 'b' and c != 't' and \
					c != 'n' and c != 'N' and c != 'd' and \
					c != 'D' and c != 'p' and c != 'g' and c != 'y':
					raise ValueError
		self.pattern = p
		
if __name__ == '__main__':
	pass

