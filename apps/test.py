#!/usr/bin/env python

# Copyright 2007, 2008 VIFF Development Team.
#
# This file is part of VIFF, the Virtual Ideal Functionality Framework.
#
# VIFF is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# VIFF is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with VIFF. If not, see <http://www.gnu.org/licenses/>.

# This example is a tribute to the original example of secure
# multi-party computation by Yao in 1982. In his example two
# millionaires meet in the street and they want to securely compare
# their fortunes. They want to do so without revealing how much they
# own to each other. This problem would be easy to solve if both
# millionaires trust a common third party, but we want to solve it
# without access to a third party.
#
# In this example the protocol is run between three millionaires and
# uses a protocol for secure integer comparison by Toft from 2005.
#
# Give a player configuration file as a command line argument or run
# the example with '--help' for help with the command line options.

from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
import time
from viff.runtime import create_runtime, gather_shares
from viff.comparison import Toft05Runtime
from viff.config import load_config
from viff.util import rand, find_prime
import sys   
sys.setrecursionlimit(2000000)
# We start by defining the protocol, it will be started at the bottom
# of the file.
start = 0

def record_start():
    global start
    start = time.time()
    print "*" * 64
    print "Started"


def record_stop():
    print "am I here?"
    stop = time.time()
    print
    print "Total time used: %.3f sec" % (stop-start)
    if runtime.id == 1:
        f = open('time.txt', 'w')
        f.write(stop-start)
        f.close()
    print "*" * 64
    #return x

class Protocol:

    def __init__(self, runtime):
        # Save the Runtime for later use
        self.runtime = runtime
	self.k = 128
	self.b = 2

	self.matrix = [[0 for x in range(self.k + 1)] for y in range(self.k + 1)]
	self.openmatrix =[[0 for x in range(self.k + 1)] for y in range(self.k + 1)]
	self.prefix = 0

        # This is the value we will use in the protocol.
        self.target = 3
        

	Zp = GF(find_prime(2**271))

	if runtime.id == 1:
	    a = runtime.shamir_share([1], Zp, self.target)
	else:
	    a = runtime.shamir_share([1], Zp)
	self.a = a
	for i in range(self.k + 1):
		if runtime.id == 1:
	    		self.matrix[0][i] = self.runtime.shamir_share([1], Zp, self.b**i)
		else:
	    		self.matrix[0][i] = self.runtime.shamir_share([1], Zp)
		



	for i in range(self.k + 1):
		
		self.openmatrix[0][i] = self.runtime.open(self.matrix[0][i])
		

		

	self.prefix = runtime.open(a - self.matrix[0][1])

	list = [self.prefix,a]
	list = list + [self.openmatrix[0][i] for i in range(self.k + 1)]
	results = gather_shares(list)

	results.addCallback(self.preprocess_ready)

    def preprocess_ready(self, results):
	print "ready!"
	record_start()
	print "what"
	self.matrix[1][0] = self.a
	self.matrix[1][1] = self.matrix[1][0] * self.matrix[0][1]
	#print  "%d"%results[0]
	print  results[1]
	for m in range(2,self.k+1):
		for n in range(0,m):
			if m == 2 and n == 1:
				print "[ab] already calculated"
				
			else:
				if (m - n) != 1 :
					#print "once here?[%d,%d]"%(m-n,n)
					sum = 0
					for p in range(0,m-n):
						sum = sum + self.matrix[m-n-1-p][n+p]
					self.matrix[m-n][n] = results[0] * sum + self.matrix[0][m]
					
				else:
					#print "once here?lol[%d,%d]"%(m-n,n)
					sum = 0

					for p in range(0,n):
						sum = sum + self.matrix[m-n+p][n-1-p]
					self.matrix[m-n][n] = (-1) * results[0] * sum + self.matrix[m][0]
	print "calculation finished"
	record_stop()
	for i in range(1 , self.k + 1):	
		self.openmatrix[i][0] = self.runtime.open(self.matrix[i][0])

	print "reconstruction finished"
	list = [self.openmatrix[i][0] for i in range(1,self.k + 1)]

	#results = gather_shares(list)

	#results.addCallback(self.calculation_ready)
	#results.addCallback(record_stop)

    def calculation_ready(self, results):
	print "ready to print"
	#print self.openmatrix
	for i in range(1,self.k+1):
		print self.openmatrix[i][0]
  
		

# Parse command line arguments.
parser = OptionParser()
Toft05Runtime.add_options(parser)
options, args = parser.parse_args()

if len(args) == 0:
    parser.error("you must specify a config file")
else:
    id, players = load_config(args[0])

# Create a deferred Runtime and ask it to run our protocol when ready.
pre_runtime = create_runtime(id, players, 1, options, Toft05Runtime)
pre_runtime.addCallback(Protocol)

# Start the Twisted event loop.
reactor.run()
