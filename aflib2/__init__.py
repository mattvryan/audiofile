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

class AFDataStore:
	'''Abstract base class representing a datastore
	for an audiofile library.
	'''
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
		self._create_db()
	def _create_db(self):
		raise NotImplementedError
	def save_mp3(self,entry):
		raise NotImplementedError
	def get_query_result_set(self,qdict):
		raise NotImplementedError
		
class AFSqliteDataStore(AFDataStore):
	'''Implementation of AFDataStore which stores
	the audiofile library in SQLite.
	'''
	def _get_connection(self):
		return sql.connect(self.dbname)
	def _have_schema(self):
		# Figure out if we have the schema yet
		dbconn = self._get_connection()
		cur = dbconn.cursor()
		cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
		count = cur.fetchone()[0]
		dbconn.close()
		return count == 5
	def _clear_db(self):
		dbconn = self._get_connection()
		cur = dbconn.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
		rows = cur.fetchall()
		for row in rows:
			cur.execute('DROP TABLE %s' % row[0])
		dbconn.commit()
		dbconn.close()		
	def _create_db(self):
		self.dbname = expanduser('~/.audiofile/lib.db')
		if not isdir(dirname(self.dbname)):
			makedirs(dirname(self.dbname))
		if not self._have_schema():
			self._clear_db()
		dbconn = self._get_connection()
		cur = dbconn.cursor()
		cur.executescript("""
			CREATE TABLE IF NOT EXISTS publisher(id INTEGER PRIMARY KEY, name VARCHAR UNIQUE);
			CREATE TABLE IF NOT EXISTS genre(id INTEGER PRIMARY KEY, name VARCHAR UNIQUE);
			CREATE TABLE IF NOT EXISTS artist(id INTEGER PRIMARY KEY, name VARCHAR UNIQUE);
			CREATE TABLE IF NOT EXISTS album(id INTEGER PRIMARY KEY, name VARCHAR, artist_id INTEGER, track_count INTEGER, disc_count INTEGER DEFAULT 1, publisher_id INTEGER, year VARCHAR DEFAULT NULL, FOREIGN KEY(artist_id) REFERENCES artist(id), FOREIGN KEY(publisher_id) REFERENCES publisher(id));
			CREATE TABLE IF NOT EXISTS song(id INTEGER PRIMARY KEY, name VARCHAR, path VARCHAR, base_path VARCHAR, album_id INTEGER, artist_id INTEGER, genre_id INTEGER, track_num INTEGER, disc_num INTEGER, FOREIGN KEY(album_id) REFERENCES album(id), FOREIGN KEY(artist_id) REFERENCES artist(id), FOREIGN KEY(genre_id) REFERENCES genre(id));
			CREATE UNIQUE INDEX IF NOT EXISTS unique_album ON album(name,artist_id);
			CREATE UNIQUE INDEX IF NOT EXISTS unique_song ON song(name,album_id);
		""")
		dbconn.commit()
		dbconn.close()
	def _get_or_create_id(self,table,name,dbconn):
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
	def _get_or_create_album_id(self,album,artist_id,total_tracks,total_discs,publisher_id,year,dbconn):
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
	def _get_or_create_song_id(self,song,path,base_path,album_id,artist_id,genre_id,track_num,disc_num,dbconn):
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
	def _make_sql_from_query(self,qdict):
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

	def save_mp3(self,entry):
		dbconn = self._get_connection()
		publisher_id = self._get_or_create_id('publisher',entry.publisher,dbconn)
		genre_id = self._get_or_create_id('genre',entry.genre,dbconn)
		artist_id = self._get_or_create_id('artist',entry.artist,dbconn)
		album_id = None
		if artist_id and publisher_id:
			album_id = self._get_or_create_album_id(entry.album,
							artist_id,entry.total_tracks,entry.total_discs,
							publisher_id,entry.year,dbconn)
		if album_id and artist_id and genre_id:
			song_id = self._get_or_create_song_id(entry.title,
							entry.path,entry.base_path,album_id,
							artist_id,genre_id,entry.track_num,
							entry.disc_num,dbconn)
		dbconn.close()
	def get_query_result_set(self,qdict):
		sqlstmt = self._make_sql_from_query(qdict)
		dbconn = sql.connect(self.dbname)
		cur = dbconn.cursor()
		cur.execute(sqlstmt)
		rows = cur.fetchall()
		dbconn.close()
		results = []
		for row in rows:
			result = {}
			result['title'] = row[0]
			result['path'] = row[1]
			result['base_path'] = row[2]
			result['track_num'] = row[3]
			result['disc_num'] = row[4]
			result['album'] = row[5]
			result['total_tracks'] = row[6]
			result['total_discs'] = row[7]
			result['year'] = row[8]
			result['artist'] = row[9]
			result['publisher'] = row[10]
			result['genre'] = row[11]
			results.append(result)
		return results


class AFLibrary:
	'''Represents an audiofile library.
	You can add an MP3 to the library via the add_mp3() method.
	Execute a query on the library via the get_songs() method.
	'''
	def __init__(self, datastore):
		self.datastore = datastore
				
	def add_mp3(self, path, base_path):
		ent = AFLibraryEntry()
		ent.apply_path(path, base_path)
		self.datastore.save_mp3(ent)
		
	def get_songs(self, qdict):
		for result in self.datastore.get_query_result_set(qdict):
			ent = AFLibraryEntry()
			ent.apply_dict(result)
			yield ent
		

class AFLibraryEntry:
	'''Represents an audiofile library entry (a song).
	Instances can be created from an MP3 file by suppling the
	path to the MP3 file and the base path to the MP3 library via
	the "apply_path() method, or from a dictionary with the
	instance variable names as keys using the apply_dict() method.
	'''
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
				if mp3.tag.best_release_date:
					self.year = str(mp3.tag.best_release_date)
				if not self.year:
					self.year = ''
				if mp3.tag.genre:
					self.genre = mp3.tag.genre.name
	def apply_dict(self,d):
		self.title = d['title']
		self.path = d['path']
		self.base_path = d['base_path']
		self.track_num = d['track_num']
		self.disc_num = d['disc_num']
		self.album = d['album']
		self.total_tracks = d['total_tracks']
		self.total_discs = d['total_discs']
		self.year = d['year']
		self.artist = d['artist']
		self.publisher = d['publisher']
		self.genre = d['genre']
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
		
class Pattern:
	'''Pattern syntax used for renaming MP3s.
	The syntax is:
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

