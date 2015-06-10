#!/usr/bin/python
#-----------------------------------------------------
# [netsim] edu.fit.icis.netsim.edu.fit.icis.netsim.test
# User: mcarvalho
# Date: 8/10/14 - 12:07 AM
# Copyright (c) 2014 Florida Institute of Technology
# All rights reserved.
#-----------------------------------------------------

import sys
sys.path.append("..")
#import NetInterface
import traceback
import threading
import random

import time
from NSLab import *

class NodeB(threading.Thread):
    def __init__(self, nodeID, iFace1, iFace2, fsize=512, rws=10, rperror=0):
        threading.Thread.__init__(self)
        self._timer = threading.Timer
        self._nodeID = nodeID
        self._iFace1 = iFace1
        self._iFace2 = iFace2
        self._running = True
        self._timeOutDelay = 100
        self._writeDelay = 0

        self._fsize = fsize
        self._rperror = rperror

        self._rws = rws
        self._lfr = 0
        self._laf = self._lfr + self._rws
        self._max_seq_no = self._rws * 2

        self._valid_recv_seq_no = []
        self._beginTime = 0

        supportedSeqNumStr = ""
        for i in range(self._max_seq_no):
            supportedSeqNumStr += " " + str(i)
        self.__sysout("Supported seqNo:" + supportedSeqNumStr)

    def setBeginTime(self, _beginTime):
        self._beginTime = _beginTime

    def stopNode(self):
        self._running = False

    def _displaySlidingWindow(self):
        lfr = self._valid_recv_seq_no[0][0] - 1
        laf = self._valid_recv_seq_no[-1][0]
        if lfr < 0:
            lfr = self._max_seq_no - 1
        self.__sysout("RWS:" + str(self._rws) + " LFR:" + str(lfr) + " LAF:" + str(laf))

    def run(self):
        for i in range(self._lfr, self._rws):
            self._valid_recv_seq_no.append([i, 0])

        self._laf = self._lfr + len(self._valid_recv_seq_no)
        self._displaySlidingWindow()

        while self._running == True:
            #time.sleep(1)
            msgs = self._iFace1.read()
            decoded = None

            #update valid received sequence number
            curr_time = str(time.time() - self._beginTime)
            for msg in msgs:
                try:
                    decoded = unicode(msg, 'utf-8')
                    #self.__sysout("[RECV][PKT][" + str(time.time() - self._beginTime) + "]: " + decoded)
                    self.__sysout(
                        "[RECV][PKT][" + curr_time + "]: BytesCnt:" + str(len(decoded)) +
                        " seq_no:" + decoded[-2:] + " pktNo:" + decoded[-10:-2]
                    )
                except UnicodeEncodeError:
                    print traceback.print_stack()

                recv_seq_no = int(msg[-2:])
                for valid_recv_seq_no in self._valid_recv_seq_no:
                    if valid_recv_seq_no[0] == recv_seq_no:
                        valid_recv_seq_no[1] = 1

            #update valid sequence number
            #get ack sequence number
            ack_seq_no = []
            while len(self._valid_recv_seq_no) > 0:
                if self._valid_recv_seq_no[0][1] == 1:
                    ack_seq_no.append(self._valid_recv_seq_no[0][0])
                    self._valid_recv_seq_no.pop(0)
                else:
                    break

            if len(ack_seq_no) > 0:
                self._lfr = ack_seq_no[-1]

                if self._lfr + self._rws >= self._max_seq_no:
                    self._laf = self._lfr + self._rws - self._max_seq_no
                else:
                    self._laf = self._lfr + self._rws

            last_valid_seq_no = self._lfr + len(self._valid_recv_seq_no)
            if last_valid_seq_no >= self._max_seq_no:
                last_valid_seq_no -= self._max_seq_no
            for i in range(len(ack_seq_no)):
                last_valid_seq_no += 1
                if last_valid_seq_no >= self._max_seq_no:
                    last_valid_seq_no = 0
                self._valid_recv_seq_no.append([last_valid_seq_no, 0])

            self._displaySlidingWindow()

            lost_ack_seq_no_idx = []
            for i in range(len(ack_seq_no)):
                if int(random.uniform(0, 100)) <= self._rperror:
                    lost_ack_seq_no_idx.append(i)


            curr_time = str(time.time() - self._beginTime)
            for idx in lost_ack_seq_no_idx:
                self.__sysout("[SEND][ACK][DROP][" + curr_time + "]: seqNo:" + str(ack_seq_no[idx]))

            ack_seq_no = [i for j, i in enumerate(ack_seq_no) if j not in lost_ack_seq_no_idx]

            if len(ack_seq_no) > 0:
                self.__setupWriteTimer(ack_seq_no)

    def __setupWriteTimer(self, seq_no):
        delay = self._writeDelay
        self._timer(delay, self.writeMsg, [seq_no]).start()

    def writeMsg(self, seq_no):
        msgList = []
        curr_time = str(time.time() - self._beginTime)
        for i in seq_no:
            msg = str(i).zfill(2)
            msg = msg.zfill(self._fsize)
            msgBytes = msg
            #self.__sysout("[NodeA][SENT]: seq_no: " + "\tBytes:" + str(len(msgBytes)))
            #self.__sysout("[SEND][ACK][" + str(time.time() - self._beginTime) + "]: " + msgBytes)
            self.__sysout(
                "[SEND][ACK][" + curr_time + "]: BytesCnt:" + str(len(msgBytes)) +
                " seqNo:" + msgBytes[-2:]
            )
            msgList.append(msgBytes)

        try:
            self._iFace2.write(msgList)
        except KeyboardInterrupt:
            print traceback.print_stack()

    def __sysout(self, msg):
        print("[" + str(self._nodeID) + "]" + msg)

if __name__ == '__main__':
    nslab = NSLab.getNetSim()
    print("Creating channel")
    nslab.setChannel(1, .001)

    netIface1 = nslab.getInterface(1, -1)
    netIface2 = nslab.getInterface(1, -1)
    test = NodeB(1, netIface1, netIface2, 10, 10, 0)
    test.run()

