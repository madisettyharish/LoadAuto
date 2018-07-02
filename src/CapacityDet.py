#!/usr/bin/python

import config
import commands

from SNMPLib import SNMPLib
snmpobj = SNMPLib()

class CapacityDet:
    def __init__(self, number):
        self.number = number
        self.loadAT = config.loadDetails['ATFile']
        self.SATPath = config.SATDetails['SATPath']
        self.loadname = config.loadDetails['loadName']
        self.loadnamecomp = ['conf']
        self.loadcapacity = config.CapacityDetails['LoadCapacity']


    def Dynamiccheck(self):

        c = 0
        self.loadcapacity = config.CapacityDetails['LoadCapacity']
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
                onePortDSP = self.number / CurrentTotalofPorts
                print "CurrentTotalofPorts " + str(CurrentTotalofPorts)
                print "DSP Avg is " + str(self.number)
                print "One port is using DSP of " + str(onePortDSP)
                #OneofDsp = CurrentTotalofPorts / int(self.number)
                UpdateValOfPorts = int(float(self.loadcapacity) / onePortDSP)
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
            UpdateValOfPorts_conn = int(OneofDsp_conn + 1) * int(self.loadcapacity)
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
        audcores = snmpobj.getMSaudiocores()
        for i in range(len(self.loadnamecomp)):
            if self.loadnamecomp[i] in self.loadname.lower():
                NumofConn1 = commands.getoutput(
                    'grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
                NumofConf1 = commands.getoutput(
                    'grep "^NumberOfConferences=" %s%s | tail -1' % (self.SATPath, self.loadAT))
                codecs = commands.getoutput(
                    'grep \'^CodecType=\' %s%s | tail -1 tail -1 | awk -F\'=\' \'{print $2}\''
                    % (self.SATPath, self.loadAT))
                codeclist = codecs.split(';')

                #import re
                #regex = re.compile('telephone-event.*')
                # Removing telephone event from the codec list
                #codeclist = [x for x in codeclist if not regex.match(x)]

                print "NumofConn1", NumofConn1
                print "NumofConf1", NumofConf1
                NumofConn = NumofConn1.split("=")[1]
                NumofConf = NumofConf1.split("=")[1]
                TotalNumofPortsNeeded = int(audcores) * 10
                print "TotalNumofPortsNeeded", TotalNumofPortsNeeded
                if int(NumofConn) < 3:
                    # Making the NumberOfConnections as 3 as there are less connections configured
                    NumofConn = 3
                    commands.getoutput(
                        "sed -i 's/%s/NumberOfConnections=%s/g' %s%s" % (
                            NumofConn1, NumofConn, self.SATPath, self.loadAT))

                UpdateValOfConf = int(TotalNumofPortsNeeded) / int(NumofConn)
                print "UpdateValOfConf", UpdateValOfConf
                commands.getoutput(
                    "sed -i 's/%s/NumberOfConferences=%s/g' %s%s" % (
                    NumofConf1, UpdateValOfConf, self.SATPath, self.loadAT))
                c = 1
                break
        if c != 1:
            NumofConn1 = commands.getoutput('grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
            UpdateValOfPorts_conn = int(audcores) * 10
            print "UpdateValOfPorts connection", UpdateValOfPorts_conn
            commands.getoutput(
                "sed -i 's/%s/NumberOfConnections=%s/g' %s%s" % (
                NumofConn1, UpdateValOfPorts_conn, self.SATPath, self.loadAT))

    def decports(self, newReqLoad):

        c = 0
        print "Decreasing the number of connections ..."
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
                onePortDSP = self.number / CurrentTotalofPorts
                print "CurrentTotalofPorts " + str(CurrentTotalofPorts)
                print "DSP Avg is " + str(self.number)
                print "One port is using DSP of " + str(onePortDSP)
                #OneofDsp = CurrentTotalofPorts / int(self.number)
                UpdateValOfPorts = int(float(newReqLoad) / onePortDSP)
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
            UpdateValOfPorts_conn = int(OneofDsp_conn + 1) * newReqLoad
            print "UpdateValOfPorts connection", UpdateValOfPorts_conn
            commands.getoutput(
                "sed -i 's/%s/NumberOfConnections=%s/g' %s%s" % (
                NumofConn1, UpdateValOfPorts_conn, self.SATPath, self.loadAT))