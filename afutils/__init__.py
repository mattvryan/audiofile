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
from os import walk
from os.path import join, splitext
from argparse import ArgumentParser


def get_clargs(argv):
	parser = ArgumentParser(description='Take control of your MP3 library.')
	parser.add_argument('-a','--add',
						help='Add MP3s in the supplied path to the library.',
						metavar='MP3 library path',
						dest='path')
	parser.add_argument('-q','--query',
						help='Query the MP3 library (artist|album|title|genre|year=string)',
						metavar='Query string(s)',
						dest='query')
	parser.add_argument('-r','--rename',
						help='''Rename MP3s according to a pattern''',
						metavar='Pattern',
						dest='pattern')
	return vars(parser.parse_args(argv))

def find_files_with_ext(dir, ext):
	if not ext.startswith('.'):
		ext = '.%s' % ext
	for dirname, dirnames, filenames in walk(dir):
		for filename in filenames:
			if filename.startswith('.'):
				continue
			elif splitext(filename)[1].lower() != ext:
				continue
			yield join(dirname, filename)

def extract_next(s,expect):
	start = 1
	sep = expect
	if s[0] == '\'':
		sep = '\''
	elif s[0] == '"':
		sep = '"'
	else:
		start = 0
	try:
		end = s.index(sep,start)
		w = s[start:end]
		if sep != expect:
			start = s.index(expect,end)
		else:
			start = end + 1
		ns = s[start:]
		return (w,ns)
	except ValueError:
		return (s, None)

def parse_query(s):
	while True:
		(k, s) = extract_next(s,'=')
		if k is None:
			yield None
		(v, s) = extract_next(s,',')
		if v is None:
			yield None
		yield (k, v)
		if s is None:
			break



if __name__ == '__main__':
	pass

