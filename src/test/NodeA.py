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

import time
from NSLab import *

class NodeA(threading.Thread):
    def __init__(self, nodeID, iFace1, iFace2, fsize=512, sws=10, sperror=0):
        threading.Thread.__init__(self)
        self._timer = threading.Timer
        self._nodeID = nodeID
        self._iFace1 = iFace1
        self._iFace2 = iFace2
        self._running = True
        self._sendWriteThreads = []
        self._timeOutDelay = 100
        self._writeDelay = 0
        self.__lock = threading.RLock()

        self._fsize = fsize
        self._sperror = sperror

        self._sws = sws
        self._lar = 0
        self._lfs = 1
        self._max_seq_no = self._sws * 2
        self._timeOutCnt = 0
        self._valid_send_pkt_no = []

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
        #for valid_send_pkt_no in self._valid_send_pkt_no:
        #    if valid_send_pkt_no[3] == 0:
        #        no_ack
        self._lar = self._valid_send_pkt_no[0][1] - 1
        self._lfs = self._valid_send_pkt_no[-1][1]
        if self._lar < 0:
            self._lar = self._max_seq_no - 1
        self.__sysout("SWS:" + str(self._sws) + " LAR:" + str(self._lar) + " LFS:" + str(self._lfs))

    def run(self):
        curr_seq_no = 0
        self.__setupTimeOut()

        #calculate sequence number
        for i in range(self._lar, self._sws+self._lar):
            self._valid_send_pkt_no.append([i, i, 0, 0])

        self._displaySlidingWindow()
        curr_time = str(time.time() - self._beginTime)
        for valid_send_pkt_no in self._valid_send_pkt_no:
            if valid_send_pkt_no[2] == 0:
                if int(random.uniform(0, 100)) <= self._sperror:
                    self.__sysout(
                        "[SEND][PKT][DROP][" + curr_time + "]: pktNo:" + 
                        str(valid_send_pkt_no[0]) + " seqNo:" + str(valid_send_pkt_no[1])
                    )
                    valid_send_pkt_no[2] = 1

        if len(self._valid_send_pkt_no) > 0:
            #self._lfs = self._valid_send_pkt_no[-1][1]
            self.__setupWriteTimer()

        while self._running == True:
            #time.sleep(1)
            msgs = self._iFace2.read()

            decoded = None
            curr_time = str(time.time() - self._beginTime)
            for msg in msgs:
                try:
                    decoded = unicode(msg, 'utf-8')
                    #self.__sysout("[RECV][ACK][" + str(time.time() - self._beginTime) + "]: " + decoded)
                    self.__sysout(
                        "[RECV][ACK][" + curr_time + "]: BytesCnt:" + str(len(decoded)) +
                        " seqNo:" + decoded[-2:]
                    )
                except UnicodeEncodeError:
                    print traceback.print_stack()

            #update lar
            with self.__lock:
                for msg in msgs:
                    ack_seq_no = int(msg[-2:])
                    for i in self._valid_send_pkt_no:
                        if i[1] == ack_seq_no:
                            i[3] = 1

                pkt_no_inc = 0
                item_pos = 0
                for i in self._valid_send_pkt_no:
                    item_pos += 1
                    if i[3] == 1:
                        pkt_no_inc = item_pos

                #print "pkt_no_inc ", pkt_no_inc
                #print self._valid_send_pkt_no

                #calculate sequence number
                last_send_pkt_no = self._valid_send_pkt_no[-1][0]
                last_seq_no = self._valid_send_pkt_no[-1][1]
                for i in range(pkt_no_inc):
                    last_send_pkt_no += 1
                    last_seq_no += 1
                    if last_seq_no >= self._max_seq_no:
                        last_seq_no = 0
                    self._valid_send_pkt_no.pop(0)
                    self._valid_send_pkt_no.append([last_send_pkt_no, last_seq_no, 0, 0])

                self._displaySlidingWindow()
                curr_time = str(time.time() - self._beginTime)
                for valid_send_pkt_no in self._valid_send_pkt_no:
                    if valid_send_pkt_no[2] == 0:
                        if int(random.uniform(0, 100)) <= self._sperror:
                            self.__sysout(
                                "[SEND][PKT][DROP][" + curr_time + "]: pktNo:" + 
                                str(valid_send_pkt_no[0]) + " seqNo:" + str(valid_send_pkt_no[1])
                            )
                            valid_send_pkt_no[2] = 1

                if len(self._valid_send_pkt_no) > 0:
                    #self._lfs = self._valid_send_pkt_no[-1][1]
                    self.__setupWriteTimer()

        for sendWriteThread in self._sendWriteThreads:
            sendWriteThread.cancel()

    def setTimeOutDelay(self, timeOutDelay):
        self._timeOutDelay = timeOutDelay

    def __setupTimeOut(self):
        if self._running == False:
            return

        if self._timeOutCnt > 0:
            self.__sysout("[SENT][TIMEOUT][" + str(time.time() - self._beginTime) + "]: " + str(self._timeOutCnt))
        self._timeOutCnt += 1

        #update sliding window variable
        with self.__lock:
            for valid_send_pkt_no in self._valid_send_pkt_no:
                valid_send_pkt_no[2] = 0

            if len(self._valid_send_pkt_no) > 0:
                self._displaySlidingWindow()

            curr_time = str(time.time() - self._beginTime) 
            for valid_send_pkt_no in self._valid_send_pkt_no:
                if valid_send_pkt_no[2] == 0:
                    if int(random.uniform(0, 100)) <= self._sperror:
                        self.__sysout(
                            "[SEND][PKT][DROP][" + curr_time + "]: pktNo:" + 
                            str(valid_send_pkt_no[0]) + " seqNo:" + str(valid_send_pkt_no[1])
                        )
                        valid_send_pkt_no[2] = 1

            self.__setupWriteTimer()

        #restart timeOut
        delay = self._timeOutDelay
        self._timer(delay, self.__setupTimeOut).start()

    def __setupWriteTimer(self):
        delay = self._writeDelay
        self._timer(delay, self.writeMsg).start()

    def writeMsg(self):
        msgList = []
        #print self._valid_send_pkt_no
        curr_time = str(time.time() - self._beginTime)
        for i in self._valid_send_pkt_no:
            if i[2] == 0:
                i[2] = 1
                msg = str(i[0]).zfill(8) + str(i[1]).zfill(2)
                msg = msg.zfill(self._fsize)
                msgBytes = msg
                #self.__sysout("[NodeA][SENT]: seq_no: " + "\tBytes:" + str(len(msgBytes)))
                #self.__sysout("[SENT][PKT][" + str(time.time() - self._beginTime) + "]: " + msgBytes)
                self.__sysout(
                    "[SENT][PKT][" + curr_time + "]: BytesCnt:" + str(len(msgBytes)) +
                    " seqNo:" + msgBytes[-2:] + " pktNo:" + msgBytes[-10:-2]
                )
                msgList.append(msgBytes)

        try:
            self._iFace1.write(msgList)
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
    test = NodeA(1, netIface1, netIface2)
    test.setTimeOutDelay(10)
    test.run()

