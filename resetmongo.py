#!/usr/bin/env python
# encoding: utf-8
"""
resetmongo.py

Created by Matt Ryan on 2013-04-28.
Copyright (c) 2013 Seventeen Stones, Inc. All rights reserved.
"""

import sys
import os
import pymongo


def main():
	c = pymongo.MongoClient()
	db = c.audiofile
	db.drop_collection(db.songs)


if __name__ == '__main__':
	main()

