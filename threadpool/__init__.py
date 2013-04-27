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

from threading import Thread
from Queue import Queue

class ThreadPool:
	'''Implementation of a simple threadpool.
	Creating the threadpool gets it started.
	Put jobs into the threadpool via put() and an
	available thread in the pool will perform the
	job.  Stop the threadpool using quit().'''
	pool = []
	q_in = Queue()
	q_out = Queue()
	n_jobs = 0
	action = None
	def run_thread(self):
		while(True):
			data = self.q_in.get()
			if data[0]=='quit':
				break
			else:
				if self.action is not None:
					self.action(data)
				self.q_out.put(data)
	def quit(self):
		for t in self.pool:
			self.put(['quit'])
		for t in self.pool:
			t.join()
		for t in self.pool:
			del t	
	def __init__(self,action,n_threads=5):
		self.action = action
		for i in xrange(n_threads):
			t = Thread(target=self.run_thread)
			t.start()
			self.pool.append(t)
	def __del__(self):
		self.quit()
	def put(self,data):
		self.n_jobs += 1
		self.q_in.put(data)
	def total_jobs(self):
		return self.n_jobs
	def remaining_jobs(self):
		return self.q_in.count()
	def completed_jobs(self):
		return self.q_out.count()
		
if __name__ == '__main__':
	pass

