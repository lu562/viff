#!/usr/bin/env python



from optparse import OptionParser
import viff.reactor
viff.reactor.install()
from twisted.internet import reactor

from viff.field import GF
import time
from viff.runtime import create_runtime, gather_shares,Share
from viff.comparison import Toft05Runtime
from viff.passive import PassiveRuntime
from viff.active import ActiveRuntime
from viff.config import load_config
from viff.util import rand, find_prime
from viff.active import TriplesHyperinvertibleMatricesMixin
from pympler import asizeof
from pympler import summary
from pympler import muppy
from pympler import tracker
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
    
    stop = time.time()
    print
    print "Total time used: %.3f sec" % (stop-start)
    '''
    if runtime.id == 1:
        f = open('time.txt', 'w')
        f.write(stop-start)
        f.close()
    '''
    print "*" * 64
    #return x

class Protocol:

    def __init__(self, runtime):
        # Save the Runtime for later use
        self.runtime = runtime
	self.tr = tracker.SummaryTracker();
	self.k = 64
	self.b = 2
	self.threshold = 1
	Zp = GF(find_prime(2**64))

	self.matrix = [[0 for x in range(self.k + 1)] for y in range(self.k + 1)]
	self.openmatrix =[[0 for x in range(self.k + 1)] for y in range(self.k + 1)]
	self.prefix = 0
	 
        # This is the value we will use in the protocol.
        self.target = 3
        

	
	
	if runtime.id == 1:
	    self.a = runtime.shamir_share([1], Zp, self.target)
	else:
	    self.a = runtime.shamir_share([1], Zp)
	print "share allocated"

	'''
	for i in range(self.k + 1):
		if runtime.id == 1:
	    		self.matrix[0][i] = self.runtime.shamir_share([1], Zp, self.b**i)
		else:
	    		self.matrix[0][i] = self.runtime.shamir_share([1], Zp)
		
	'''


	#self.matrix[0][1] = TriplesHyperinvertibleMatricesMixin.single_share_random(1,self.threshold,Zp)
	if runtime.id == 1:
		self.matrix[0][0] = self.runtime.shamir_share([1], Zp,0)
		self.matrix[0][1] = self.runtime.shamir_share([1], Zp, self.b)
	else:
		self.matrix[0][0] = self.runtime.shamir_share([1], Zp)
		self.matrix[0][1] = self.runtime.shamir_share([1], Zp)
 
	for i in range(2,self.k + 1):
		self.matrix[0][i] = self.matrix[0][i - 1] * self.matrix[0][1]
		
	print "triple generated"
	'''
	for i in range(self.k + 1):		
		self.openmatrix[0][i] = self.runtime.open(self.matrix[0][i])

	'''
		

	self.prefix = self.runtime.open(self.a - self.matrix[0][1])
	
	list = [self.prefix]
	results = gather_shares(list)
	results.addCallback(self.preprocess_ready)


    def preprocess_ready(self, results):
	 
	print "ready!"
	Zp = GF(find_prime(2**64))
	self.matrix[1][0] = self.a
	self.matrix[1][1] = self.matrix[1][0] * self.matrix[0][1]
	#print  "%d"%results[0]
	#print  results[1]
	print self.matrix[0][4]
	
	self.tr.print_diff() 
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
						#self.tr.print_diff() 
						
					self.matrix[m-n][n] = results[0] * sum + self.matrix[0][m]
					
				else:
					#print "once here?lol[%d,%d]"%(m-n,n)					
					sum = 0
					for p in range(0,n):
						sum = sum + self.matrix[m-n+p][n-1-p]
						#self.tr.print_diff() 
					self.matrix[m-n][n] = (-1) * results[0] * sum + self.matrix[m][0]
	print "calculation finished"
	
	self.tr.print_diff() 

	#all_objects = muppy.get_objects()
	#sum1 = summary.summarize(all_objects)
	#summary.print_(sum1) 
	#record_stop()

	for i in range(1 , self.k + 1):	
		self.openmatrix[i][0] = self.runtime.open(self.matrix[i][0])
	

	print "reconstruction finished"
	
	list = [self.openmatrix[i][0] for i in range(1,self.k + 1)]



	results = gather_shares(list)

	results.addCallback(self.calculation_ready)
	

	self.runtime.schedule_callback(results, lambda _: self.runtime.synchronize())
        self.runtime.schedule_callback(results, lambda _: self.runtime.shutdown())


    def calculation_ready(self, results):
	print "ready to print"
	#print self.openmatrix
	#for i in range(1,self.k+1):
		#print self.openmatrix[i][0]
	#return results


		

# Parse command line arguments.
parser = OptionParser()
Toft05Runtime.add_options(parser)
options, args = parser.parse_args()

if len(args) == 0:
    parser.error("you must specify a config file")
else:
    id, players = load_config(args[0])

# Create a deferred Runtime and ask it to run our protocol when ready.
pre_runtime = create_runtime(id, players, 1, options,ActiveRuntime)
pre_runtime.addCallback(Protocol)

# Start the Twisted event loop.
reactor.run()