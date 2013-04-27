#!/usr/bin/env python
# encoding: utf-8
"""
file_pattern.py

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

# Pattern for renaming MP3s:
# %a = artist
# %b = album
# %t = title
# %n = track number
# %N = total tracks
# %d = disc number
# %D = total discs
# %p = publisher
# %g = genre
# %y = year

def is_valid(p):
	for token in p.split('%'):
		if len(token):
			c = token[0]
			if c != 'a' and c != 'b' and c != 't' and \
				c != 'n' and c != 'N' and c != 'd' and \
				c != 'D' and c != 'p' and c != 'g' and c != 'y':
				return False
	return True
	
def get_new_path(song, p):
	new_path = ''
	have_token = False
	for c in p:
		if c == '%':
			have_token = True
		elif have_token:
			new_path += get_value_for_token(song, c)
			have_token = False
		else:
			new_path += c
			have_token = False
	return os.path.join(song.base_path, new_path)
	
def get_value_for_token(song, token):
	if token == 'a':
		return song.artist
	elif token == 'b':
		return song.album
	elif token == 't':
		return song.title
	elif token == 'n':
		return str(song.track_num)
	elif token == 'N':
		return str(song.total_tracks)
	elif token == 'd':
		return str(song.disc_num)
	elif token == 'D':
		return str(song.total_discs)
	elif token == 'p':
		return song.publisher
	elif token == 'g':
		return song.genre
	elif token == 'y':
		return song.year
	
if __name__ == '__main__':
	pass

