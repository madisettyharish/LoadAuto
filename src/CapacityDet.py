#!/usr/bin/python

import config
import commands


class CapacityDet:
    def __init__(self, number):
        self.number = number
        self.loadAT = config.loadDetails['ATFile']
        self.SATPath = config.SATDetails['SATPath']
        self.loadname = config.loadDetails['loadName']
        self.loadnamecomp = ['conf']


    def Dynamiccheck(self):

        c = 0
        for i in range(len(self.loadnamecomp)):
            if self.loadnamecomp[i] in self.loadname.lower():
                NumofConn1 = commands.getoutput(
                    'grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
                NumofConf1 = commands.getoutput(
                    'grep "^NumberOfConferences=" %s%s | tail -1' % (self.SATPath, self.loadAT))
                print "NumofConn1", NumofConn1
                print "NumofConf1", NumofConf1
                NumofConn = NumofConn1.split("=")[1]
                NumofConf = NumofConf1.split("=")[1]
                CurrentTotalofPorts = int(NumofConn) * int(NumofConf)
                OneofDsp = CurrentTotalofPorts / int(self.number)
                UpdateValOfPorts = int(OneofDsp + 1) * 70
                print "UpdateValOfPorts", UpdateValOfPorts
                UpdateValOfConn = int(UpdateValOfPorts) / int(NumofConn)
                print "UpdateValOfConf", UpdateValOfConn
                commands.getoutput(
                    "sed -i 's/%s/NumberOfConferences=%s/g' %s%s" % (
                    NumofConf1, UpdateValOfConn, self.SATPath, self.loadAT))
                c = 1
                break
        if c != 1:
            NumofConn1 = commands.getoutput('grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
            NumofConn = NumofConn1.split("=")[1]
            OneofDsp_conn = int(NumofConn) / int(self.number)
            UpdateValOfPorts_conn = int(OneofDsp_conn + 1) * 70
            print "UpdateValOfPorts connection", UpdateValOfPorts_conn
            commands.getoutput(
                "sed -i 's/%s/NumberOfConnections=%s/g' %s%s" % (
                NumofConn1, UpdateValOfPorts_conn, self.SATPath, self.loadAT))


    def decreaseThePorts(self):

        c = 0
        for i in range(len(self.loadnamecomp)):
            if self.loadnamecomp[i] in self.loadname.lower():
                NumofConf1 = commands.getoutput('grep NumberOfConferences= %s%s' % (self.SATPath, self.loadAT))
                NumofConf = NumofConf1.split("=")[1]
                UpdateValOfConf = int(NumofConf) - 4
                commands.getoutput(
                    "sed -i 's/%s/NumberOfConferences=%s/g' %s%s" % (
                    NumofConf1, UpdateValOfConf, self.SATPath, self.loadAT))
                c = 1
                break
        if c != 1:
            NumofConn1 = commands.getoutput('grep NumberOfConnections= %s%s' % (self.SATPath, self.loadAT))
            NumofConn = NumofConn1.split("=")[1]
            UpdateValOfConn = int(NumofConn) - 4
            commands.getoutput(
                "sed -i 's/%s/NumberOfConnections=%s/g' %s%s" % (
                NumofConn1, UpdateValOfConn, self.SATPath, self.loadAT))

    def flatincrports(self):

        c = 0
        for i in range(len(self.loadnamecomp)):
            if self.loadnamecomp[i] in self.loadname.lower():
                NumofConn1 = commands.getoutput(
                    'grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
                NumofConf1 = commands.getoutput(
                    'grep "^NumberOfConferences=" %s%s | tail -1' % (self.SATPath, self.loadAT))
                print "NumofConn1", NumofConn1
                print "NumofConf1", NumofConf1
                NumofConn = NumofConn1.split("=")[1]
                NumofConf = NumofConf1.split("=")[1]
                UpdateValOfPorts = int(NumofConf) + 5
                print "UpdateValOfPorts", UpdateValOfPorts
                UpdateValOfConn = int(UpdateValOfPorts) / int(NumofConn)
                print "UpdateValOfConf", UpdateValOfConn
                commands.getoutput(
                    "sed -i 's/%s/NumberOfConferences=%s/g' %s%s" % (
                    NumofConf1, UpdateValOfConn, self.SATPath, self.loadAT))
                c = 1
                break
        if c != 1:
            NumofConn1 = commands.getoutput('grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
            NumofConn = NumofConn1.split("=")[1]
            UpdateValOfPorts_conn = int(NumofConn) + 5
            print "UpdateValOfPorts connection", UpdateValOfPorts_conn
            commands.getoutput(
                "sed -i 's/%s/NumberOfConnections=%s/g' %s%s" % (
                NumofConn1, UpdateValOfPorts_conn, self.SATPath, self.loadAT))
