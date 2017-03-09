#!/usr/bin/env python

import os, serial, time

class FakeSerial(Serial):


	# required variables:
	# map of Pirani commands to test file containing the right data
	# most recent command sent to the object at the port
	# timeout
	# allow read before calling open?

	def __init__(self, port=None, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
		# if port is given, open input file, save input file handle
		self.timeout = timeout
		if self.timeout is None:
			self.timeout = 30 # sanity
		self.lastCmd = None
		self.cmdToFile = {}
		self.cmdToDataLength{}
		# in a real implementation, there should be filehandles in there
		stderr.write("\tFake serial port initialized\n")

	def open(self):
		# if test file is not open, open it
		for fileHandle in cmdToFile.values():
			if fileHandle.closed:
				fileHandle = open(fileHandle.name)

	def close(self):
		for fileHandle in cmdToFile.values():
			if not fileHandle.closed:
				fileHandle.close()

	def __del__(self):
		for fileHandle in cmdToFile.values():
			if not fileHandle.closed:
				fileHandle.close()

	def read(self, size=1):
		# read *size* bytes from the file
		# if not enough bytes, block until either timeout is reached or more bytes appear
		# clear last command when done
		out = ""
		if self.lastCmd is None or self.lastCmd not in self.cmdToFile:
			time.sleep(self.timeout)
		else:
			f = self.cmdToFile[self.lastCmd]
			out = f.read(size)
		return out

	def write(self, data):
		self.lastCmd = data;

	def flush(self):
		# leave this, we prob don't need it for our purposes

	def inWaiting(self):
		# reads how many bytes are waiting in the input buffer -- depends on current command sent
		if self.lastCmd is None or self.lastCmd not in self.cmdToDataLength:
			return 0
		else:
			return self.cmdToDataLength[self.lastCmd]


	def outWaiting(self):
		return 0

	def flushInput(self):
		# do nothing

	def flushOutput(self):
		# do nothing

	# TODO: handle the rest of the methods, so we don;t have any weird unexpected behavior here!