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
import os

import stomp
import json

import afutils.file_pattern as pattern
from aflib3 import AFLibraryEntry

class AFMQ:
	'''Represents a basic connection to an ActiveMQ
	service for AudioFile.
	'''
	def __init__(self, queue_name):
		self.queue_name = queue_name
		self.queue_handle = stomp.Connection()
		self.queue_handle.start()
		self.queue_handle.connect()
		self.queue_handle.subscribe(destination=queue_name, ack='auto')
	def __del__(self):
		self.queue_handle.disconnect()
	def put(self, msg):
		self.queue_handle.send(msg, destination=self.queue_name)
		
class BasicHandler:
	'''Represents an ActiveMQ handler that consumes information
	from the queue.
	'''
	def __init__(self, aflib, queue_name):
		self.aflib = aflib
		self.queue_name = queue_name
		self.queue_handle = stomp.Connection()
		self.queue_handle.set_listener(queue_name, self)
		self.queue_handle.start()
		self.queue_handle.connect()
		self.queue_handle.subscribe(destination=queue_name, ack='auto')
	def __del__(self):
		self.queue_handle.stop()
	def on_error(self, headers, message):
		print '%s: Received an error: "%s"' % (self.__class__, message)
	def on_message(self, headers, message):
		print '%s: Received message: "%s"' % (self.__class__, message)
		
class AddFileHandler(BasicHandler):
	'''Adds files to the AudioFile library as the files
	are posted into a queue.
	'''
	def __init__(self, aflib):
		BasicHandler.__init__(self, aflib, '/audiofile/library_additions')
	def on_message(self, headers, message):
		BasicHandler.on_message(self, headers, message)
		args = json.loads(message)
		self.aflib.add_mp3(args[0], args[1])
		
class RenameFileHandler(BasicHandler):
	'''Renames files from the old path to the new specified
	path as the information is put into a queue.
	'''
	def __init__(self, aflib):
		BasicHandler.__init__(self, aflib, '/audiofile/file_renames')
	def on_message(self, headers, message):
		BasicHandler.on_message(self, headers, message)
		args = json.loads(message)
		song = AFLibraryEntry()
		song.apply_dict(args[0])
		newpath = pattern.get_new_path(song, args[1])
		print 'Renaming "%s" as "%s"...' % (song.path, newpath)
		os.rename(song.path, newpath)

if __name__ == '__main__':
	pass

