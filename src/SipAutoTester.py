#!/usr/bin/python
import pexpect
import sys
import config
import logging
from SNMPLib import SNMPLib
from MSConfig import MSConfig
from RTPGenerator import RTPGenerator
import CapacityDet
import commands
import os
import time
import csv

snmpobj = SNMPLib()
msconfigobj = MSConfig()
rtpgenobj = RTPGenerator()


class SipAutoTester:

    def __init__(self, logpath):

        self.mrfIp = config.swMrfCredentials['mrfIp']
        self.mrfUserName = config.swMrfCredentials['mrfUserName']
        self.mrfPassword = config.swMrfCredentials['mrfPassword']
        self.rtpgIp = config.rtpgCredentials['rtpgIp']
        self.rtpgPort = config.rtpgCredentials['RTPG_PORT']
        self.loadDur = str(int(config.loadDurationDetails['loadduration']) * 60)
        self.loadDurConsumed = 0
        self.satIP = config.SATDetails['satIP']
        self.SATPath = config.SATDetails['SATPath']
        self.logPath = logpath
        self.logger = logging.getLogger("ClearMrfLog.py")
        self.logger.debug("clearing MRF Log ")
        self.loadAT = config.loadDetails['ATFile']
        self.loadModelFile = config.loadDetails['ModelFile']
        self.sutctrlip = config.swMrfCredentials['MS_Server_Control_IP']
        self.loadcapacity = config.CapacityDetails['LoadCapacity']
        #self.selection1 = config.loadDetails['selection1'].strip()
        #self.selection2 = config.loadDetails['selection2'].strip()
        self.loadname = config.loadDetails['loadName']
        self.internalSATcounter = config.loadDetails['firstrun']
        self.loadType = config.loadDetails['loadType']
        self.ignoreallErrors = config.loadDetails['ignoreallErrors']
        portInfo = config.loadDetails['portsInfo']

        with open('lmdb.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                if self.loadname in row:
                    self.selection1 = list(row)[0]
                    self.selection2 = list(row)[1]

        if "automatic" not in portInfo:
            self.fixedPortInfo = config.loadDetails['portsInfo'].split(';')
            self.fixedConn = self.fixedPortInfo[0]
            self.fixedConf = self.fixedPortInfo[-1].split(',')[0]

    def modelstandardname(self, comoutput):

        print "Getting the ModelStandard Cfg Name ..."
        child = pexpect.spawn('%s -c %s%s' % (comoutput, self.SATPath, self.loadAT))

        try:
            first = child.expect(['0 : %s' %(self.rtpgIp)])
        except pexpect.TIMEOUT:
            print "AT.cfg is not present exiting the Load Model ..."

        child.sendline('%s' %(self.selection1))
        next_menu = child.expect(["VERSION"])
        if next_menu == 0:
            child.sendline('-%s' %(self.selection2))
            time.sleep(2)
            next_menu1 = child.expect(["VERSION"])
            if next_menu1 ==0:
                mike = child.before
                mike1 = mike.split('\n')
                muk = filter(lambda s: "Config file:" in str(s), mike1)
                modelstand = ''.join(map(str, muk)).split(':')[-1]
                child.sendline('0')
                final_quit = child.expect("Entered")
                if final_quit == 0:
                    child.sendline('Y')
                    print modelstand.strip()
                    os.system('rm -rf *.dat')
                    os.system("echo '%s' > /tmp/mname.txt" %(modelstand.strip()))
                    #return modelstand.strip()
                else:
                    print "Error in exiting the SAT ..."
            else:
                print "Error in getting model.cfg name ..."

        return None

    def prepareATcfg(self):

        print "Replacing SipMSIPAddress=" + self.sutctrlip + "& SipMSIPAddressSCC=" + self.mrfIp
        commands.getoutput("sed -i '/SipMSIPAddress/d' %s/%s" %(self.SATPath, self.loadAT))
        commands.getoutput('sed -i "\$aSipMSIPAddress=%s" %s/%s' %(self.sutctrlip, self.SATPath, self.loadAT))
        commands.getoutput('sed -i "\$aSipMSIPAddressSCC=%s" %s/%s' %(self.mrfIp, self.SATPath, self.loadAT))

        print "Replacing RTPGeneratorHost1=" + self.rtpgIp
        commands.getoutput("sed -i '/RTPGeneratorHost1/d' %s/%s" %(self.SATPath, self.loadAT))
        commands.getoutput('sed -i "\$aRTPGeneratorHost1=%s" %s/%s' %(self.rtpgIp, self.SATPath, self.loadAT))

        print "Replacing RTPGeneratorPort1=" + self.rtpgPort
        commands.getoutput("sed -i '/RTPGeneratorPort1/d' %s/%s" % (self.SATPath, self.loadAT))
        commands.getoutput('sed -i "\$aRTPGeneratorPort1=%s" %s/%s' %(self.rtpgPort, self.SATPath, self.loadAT))

        print "Replacing LoadRtpgClips=yes"
        commands.getoutput("sed -i '/LoadRtpgClips/d' %s/%s" % (self.SATPath, self.loadAT))
        commands.getoutput('sed -i "\$aLoadRtpgClips=yes" %s/%s' %(self.SATPath, self.loadAT))

    def prepareMscConfig(self):

        print "Replacing LocalHost=" + self.satIP
        commands.getoutput("sed -i '/^LocalHost/d' %s/MscConfig.cfg" %(self.SATPath))
        commands.getoutput('sed -i "\$aLocalHost=%s" %s/MscConfig.cfg' %(self.satIP, self.SATPath))

    def eval_local_pexpect(self, con):

        COMMAND_PROMPT = '[#] '
        i = con.expect([pexpect.TIMEOUT, COMMAND_PROMPT, pexpect.EOF], timeout=10)
        if i == 0:
            print "***ERROR pexpect timeout. "
            return False
        elif i == 1:
            # print "Received command prompt"
            pass
        else:
            print "There is some issue in the pexpect, Please check"
            return False
        return True

    def startSAT(self):

        os.system('rm -rf %sat*'%(self.SATPath))
        os.system('rm -rf *.dat')
        os.system('scp %sMscConfig.cfg .'%(self.SATPath))
        os.system('scp -r %s/models.standard .'%(self.SATPath))

        satBin = commands.getstatusoutput(
            'ls %s/SipAutoTester_Rel_* | grep -v "tar.gz" | tail -1 | awk -F" " "{print $NF}"' % (self.SATPath))

        internalsatcount = int(config.loadDetails['firstrun']) + 1
        commands.getoutput(
            "sed -i \"s/first.*,/firstrun\':\'%s\',/g\" /root/DV_Load_Python_Files/config.py" % (internalsatcount))
        reload(config)

        if int(self.internalSATcounter) == 1:
            #modelstandname = self.modelstandardname(satBin[1])
            self.modelstandardname(satBin[1])
            #os.system(
            #    'scp %s/models.standard/%s %s/%s' %(self.SATPath, self.loadModelFile, self.SATPath, modelstandname))

        time.sleep(2)
        modelstandname = commands.getstatusoutput('cat /tmp/mname.txt' )
        ttlModel = commands.getstatusoutput(
            'cat %s/%s | grep "^TimeToLiveTimer=" | wc -l ' %(self.SATPath, modelstandname[1]))

        if int(ttlModel[1]) != 0:
            ttlAT = commands.getstatusoutput(
                'cat %s/%s | grep "^TimeToLiveTimer=" | tail -1 ' %(self.SATPath, modelstandname[1]))
            ttlValue = ttlAT[1].split('=')[1]
        else:
            ttlAT = commands.getstatusoutput(
                'cat %s/%s | grep "^TimeToLiveTimer=" | tail -1 ' % (self.SATPath, self.loadAT))
            ttlValue = ttlAT[1].split('=')[1]

        print "The TTL value is " + ttlValue

        # Checking the type of load type
        if self.loadType == "Dynamic" and int(self.internalSATcounter) == 1:

            print "Selected load type as Dynamic, calculating and configuring initial ports "
            CapacityDetobj = CapacityDet.CapacityDet(float(0))
            CapacityDetobj.flatincrports()

        elif self.loadType == "Fixed":

            NumofConn1 = commands.getoutput(
                'grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
            NumofConf1 = commands.getoutput(
                'grep "^NumberOfConferences=" %s%s | tail -1' % (self.SATPath, self.loadAT))
            commands.getoutput(
                "sed -i 's/%s/NumberOfConnections=%s/g' %s%s" % (
                    NumofConn1, self.fixedConn, self.SATPath, self.loadAT))
            commands.getoutput(
                "sed -i 's/%s/NumberOfConferences=%s/g' %s%s" % (
                    NumofConf1, self.fixedConf, self.SATPath, self.loadAT))
            NumofConn1 = commands.getoutput(
                'grep "^NumberOfConnections=" %s%s | tail -1' % (self.SATPath, self.loadAT))
            NumofConf1 = commands.getoutput(
                'grep "^NumberOfConferences=" %s%s | tail -1' % (self.SATPath, self.loadAT))
            print "Selected load type as Fixed ..."
            print "Updated AT files with Conn = " + NumofConn1 + " and Conf " + NumofConf1
        if int(self.internalSATcounter) != 1 :
            print "Replacing LoadRtpgClips=no"
            commands.getoutput("sed -i '/LoadRtpgClips/d' %s/%s" % (self.SATPath, self.loadAT))
            commands.getoutput('sed -i "\$aLoadRtpgClips=no" %s/%s' % (self.SATPath, self.loadAT))

        child = pexpect.spawn('%s -c %s%s' % (satBin[1], self.SATPath, self.loadAT))
        child.timeout = float(60)
        first = child.expect(['0 : %s' %(self.rtpgIp)])
        child.logfile = sys.stdout
        child_before = child.before
        print child_before
        child_after = child.after
        print child_after
        if first == 0:
            rtpgenobj.collectpcap()
            child.sendline('%s' %(self.selection1))
            print "sent 1st selection " + self.selection1
            next_menu = child.expect(["VERSION"])
            if next_menu == 0:
                time.sleep(2)
                child.sendline('%s' %(self.selection2))
                print "sent 2nd selection " + self.selection2
                try:
                    #t_value = int(ttlValue) * 3
                    #print "Waiting for " + str(t_value) + " Before syslog collection "
                    exit = child.expect('start test', timeout=1200)
                except pexpect.TIMEOUT:
                    print "value :"
                child.sendline(' ')
                try:
                    t_value = int(ttlValue) * 3
                    print "Waiting for " + str(t_value) + " Before syslog collection "
                    exit = child.expect('Anything', timeout=t_value)
                except pexpect.TIMEOUT:
                    print "value :"
                check_syslog = []
                check_syslog = msconfigobj.syslogcheck()

                if self.ignoreallErrors == 'false':
                    # Checking mandatory error messages
                    if check_syslog[0]:
                        print "***ERROR there is syslog errors in the load model " + self.loadname
                        child.sendline('5')
                        try:
                            quit = child.expect('selection', timeout=1200)
                        except pexpect.TIMEOUT:
                            print "TIMEOUT while waiting to stop the load model gracefully... Stopping forcefully"
                        child.sendline('0')
                        final_quit = child.expect("Entered")
                        child.sendline('Y')
                        os.system("echo 'FAILED!!! Due to syslog errors ' > verdict.txt")
                        return True

                    # Checking errors which can be ignored
                    if check_syslog[2]:
                        print "There are errors but can be ignored"

                avgaudioload = float(check_syslog[1].strip())

                print "The MAX Audio Util in SUT is " + check_syslog[1] + " %"
                if int(avgaudioload) == 0:

                    print "DSP Util is zero, increasing no.of ports to +5"
                    child.sendline('5')
                    try:
                        quit = child.expect('selection', timeout=1200)
                    except pexpect.TIMEOUT:
                        print "TIMEOUT while waiting to stop the load model gracefully... Stopping forcefully"
                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    print "Exiting out of the load model, please check the AT.cfg"
                    os.system("echo 'FAILED!!!' >> verdict.txt")
                    return True

                if check_syslog[3]:
                    print "There are DSP of out resource errors, so decreasing loadcapacity by 10% "
                    newLoadCapacity = (int(self.loadcapacity) - 10)
                    commands.getoutput(
                        "sed -i \"s/LoadCapacity.*}/LoadCapacity\':\'%s\'}/g\" /root/DV_Load_Python_Files/config.py"
                        %(newLoadCapacity))
                    reload(config)
                    print "New LoadCapacity is configured as " + str(newLoadCapacity)
                    print "Re-Running the load with newly configured load capacity ..."
                    CapacityDetobj = CapacityDet.CapacityDet(avgaudioload)
                    CapacityDetobj.Dynamiccheck()
                    return False
                else:
                    minLoadToAcheive = (int(self.loadcapacity) - 5)
                    maxLoadToAcheive = (int(self.loadcapacity) + 5)


                if self.loadType == "Dynamic" \
                    and (int(avgaudioload) <= minLoadToAcheive or int(avgaudioload) > maxLoadToAcheive):

                    print "DSP Utilization is not b/w " + str(minLoadToAcheive) + " & " + str(maxLoadToAcheive)
                    child.sendline('5')
                    try:
                        quit = child.expect('selection', timeout=1200)
                    except pexpect.TIMEOUT:
                        print "TIMEOUT while waiting to stop the load model gracefully... Stopping forcefully"
                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    if check_syslog[3]:
                        os.system("echo 'FAILED!!! OUT_OF_DSP errors with less CPU Util' > verdict.txt")
                        return True
                    CapacityDetobj = CapacityDet.CapacityDet(avgaudioload)
                    CapacityDetobj.Dynamiccheck()
                    os.system("echo 'FAILED!!! OUT_OF_DSP' > verdict.txt")
                    return False

                else:

                    if self.loadType == "Fixed":
                        print "Running the Load Model in the Fixed Mode. Ignoring load capacity ... "
                    else:
                        print "DSP % is b/w " + str(minLoadToAcheive) + "&" + str(maxLoadToAcheive)

                    print "Continuing the load model for the specified " + str(float(self.loadDur)/60) + " Min. "

                    while self.loadDurConsumed < int(self.loadDur):

                        print "In the main load run loop ... To stop the load model make  loadduration = 0 "
                        self.loadDurConsumed = self.loadDurConsumed + 300
                        child.timeout = float(300)
                        child.sendline(' ')
                        try:
                            exit = child.expect('Anything')
                        except pexpect.TIMEOUT:
                            print " Ran for " + str(self.loadDurConsumed / 60) + " Min..."

                        reload(config)
                        self.loadDur = str(int(config.loadDurationDetails['loadduration']) * 60)

                    child.timeout = float(10)
                    child.sendline(' ')
                    try:
                        exit = child.expect('Anything')
                    except pexpect.TIMEOUT:
                        print "value :"
                    print "Stopping the Load Model. "
                    child.sendline('5')
                    print "Waiting to exit from the Load Model"
                    try:
                        quit = child.expect('selection', timeout=1200)
                    except pexpect.TIMEOUT:
                        os.system("echo 'PASSED!!! FORCEFUL STOP' > verdict.txt")
                        print "TIMEOUT while waiting to stop the load model gracefully... Stopping forcefully"

                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    print "Load Model ended. @ The End"
                    print "Load Model Ran for " + str(self.loadDurConsumed / 60) + " Min..."
                    os.system('rm -rf atoutput*')
                    os.system("echo 'PASSED!!!' >> verdict.txt")
                    return True

        else:
            print "RTPG is not running"
            os.system("echo 'FAILED!!! No RTPG is running. Please checking the rtpg config's ... ' >> verdict.txt")
            return True
