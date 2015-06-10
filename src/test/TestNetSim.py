#!/usr/bin/python
#-----------------------------------------------------
# [netsim] edu.fit.icis.netsim.edu.fit.icis.netsim.test
# User: mcarvalho
# Date: 8/9/14 - 11:29 PM
# Copyright (c) 2014 Florida Institute of Technology
# All rights reserved.
#-----------------------------------------------------

import sys
sys.path.append("..")
#import NSLab
from NSLab import *
import traceback
from NodeA import *
from NodeB import *
import time
from optparse import OptionParser

class TestNetSim:
    def __init__(self, **args):
        self.fsize = args['fsize']
        self.sws = args['sws']
        self.rws = args['rws']
        self.pdelay = float(args['rtt']) / 2 / 1000
        self.sperror = args['sperror']
        self.rperror = args['rperror']
        self.rtime = args['rtime']

    def runTest(self):
        nslab = NSLab.getNetSim()

        nslab.setChannel(1, 0, self.pdelay)
        nslab.setChannel(2, 0, self.pdelay)

        try:
            netIface1 = nslab.getInterface(1, -1)
            netIface2 = nslab.getInterface(1, -1)
            netIface3 = nslab.getInterface(2, -1)
            netIface4 = nslab.getInterface(2, -1)

            tnodeA = NodeA("NodeA", netIface1, netIface4, self.fsize, self.sws, self.sperror)
            tnodeB = NodeB("NodeB", netIface2, netIface3, self.fsize, self.rws, self.rperror)
            tnodeA.setTimeOutDelay(self.pdelay * 5)
            beginTime = time.time()
            tnodeA.setBeginTime(beginTime)
            tnodeB.setBeginTime(beginTime)
            tnodeA.start()
            tnodeB.start()
            if self.rtime >= 0:
                time.sleep(self.rtime)
                tnodeA.stopNode()
                tnodeB.stopNode()
                netIface1.stopChannel()
                netIface2.stopChannel()
                netIface3.stopChannel()
                netIface4.stopChannel()

        except:
            print traceback.print_stack()

    @staticmethod
    def main(**args):
        test = TestNetSim(**args)
        test.runTest()

if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-t", "--rtt", dest="rtt", help="Round Trip Time (ms)", default=100, type=int
    )
    parser.add_option(
        "-s", "--sws", dest="sws", help="Sending Window Size", default=10, type=int
    )
    parser.add_option(
        "-r", "--rws", dest="rws", help="Receiving Window Size", default=10, type=int
    )
    parser.add_option(
        "-f", "--fsize", dest="fsize", help="Framing Size", default=10, type=int
    )
    parser.add_option(
        "-p", "--sperror", dest="sperror", help="Sending Probability Error", default=10, type=int
    )
    parser.add_option(
        "-q", "--rperror", dest="rperror", help="Receiving Probability Error", default=10, type=int
    )
    parser.add_option(
        "-e", "--rtime", dest="rtime", help="Run Time: -1:infinite n(n>0):n seconds", default=10, type=int
    )
    
    (options, args) = parser.parse_args()
    
    if options.rtt > 10000:
        options.rtt = 100
        print("options.rtt is changed to " + str(options.rtt))

    if options.sws >= 50:
        options.sws = 10
        print("options.sws is changed to " + str(options.sws))

    if options.rws >= 50:
        options.rws = 10
        print("options.rws is changed to " + str(options.rws))

    if options.fsize >= 1650:
        options.fsize = 1650
        print("options.fsize is changed to " + str(options.fsize))

    if options.sperror >= 100 or options.sperror < 0:
        options.sperror = 10
        print("options.sperror is changed to " + str(options.sperror))

    if options.rperror >= 100 or options.rperror < 0:
        options.rperror = 10
        print("options.rperror is changed to " + str(options.rperror))

    print("\nRun Arguments:")
    for opt, value in options.__dict__.items():
        print opt.ljust(10), ":" , value
    print("\n")

    TestNetSim.main(
        rtt=options.rtt, sws=options.sws, rws=options.rws, fsize=options.fsize, sperror=options.sperror, rperror=options.rperror, rtime=options.rtime
    )
    
