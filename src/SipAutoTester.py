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
        self.loadDur = config.loadDurationDetails['loadduration']
        self.satIP = config.SATDetails['satIP']
        self.SATPath = config.SATDetails['SATPath']
        self.logPath = logpath
        self.logger = logging.getLogger("ClearMrfLog.py")
        self.logger.debug("clearing MRF Log ")
        self.loadAT = config.loadDetails['ATFile']
        #self.loadATmodel = config.loadDetails['modelCfg']
        self.sutctrlip = config.swMrfCredentials['MS_Server_Control_IP']
        self.loadcapacity = config.CapacityDetails['LoadCapacity']
        self.selection1 = config.loadDetails['selection1'].strip()
        self.selection2 = config.loadDetails['selection2'].strip()
        self.loadname = config.loadDetails['loadName']

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

    def prepareMscConfig(self):

        print "Replacing LocalHost=" + self.satIP
        commands.getoutput("sed -i '/LocalHost/d' %s/%s" %(self.SATPath, self.loadAT))
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
        time.sleep(2)
        #os.system('cp %s%s %s/models.standard/' %(self.SATPath, self.loadATmodel, self.SATPath))
        comoutput = commands.getstatusoutput(
            'ls %s/SipAutoTester_Rel_* | tail -1 | awk -F" " "{print $NF}"' %(self.SATPath))

        child = pexpect.spawn('%s -c %s%s' % (comoutput[1], self.SATPath, self.loadAT))
        child.timeout = float(self.loadDur)
        first = child.expect(['0 : %s' %(self.rtpgIp)])
        child.logfile = sys.stdout
        child_before = child.before
        print child_before
        child_after = child.after
        print child_after
        if first == 0:
            #child.sendline('10')
            rtpgenobj.collectpcap()
            child.sendline('%s' %(self.selection1))
            print "sent 1st selection " + self.selection1
            #next_menu = child.expect(["Append '-'"])
            next_menu = child.expect(["VERSION"])
            if next_menu == 0:
                #child.sendline('1050')
                child.sendline('%s' % (self.selection2))
                print "sent 2nd selection " + self.selection2
                try:
                    exit = child.expect('Anything', timeout=180)
                except pexpect.TIMEOUT:
                    print "value :"

                check_syslog = msconfigobj.is_syslogerror()
                if check_syslog:
                    print "***ERROR there is syslog errors in the load model " + self.loadname
                    child.sendline('5')
                    quit = child.expect("selection", timeout=1200)
                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    os.system("echo 'FAILED!!! Due to syslog errors ' > verdict.txt")
                    return True

                maxAudioModel = snmpobj.snmpget('dspstatMaxAudioDspUtilizationModeled.2')
                print "The MAX Audio Util in SUT is " + maxAudioModel + " %"

                if int(maxAudioModel) == 0:
                    print "DSP Util is zero, increasing no.of ports to +5"
                    child.timeout = 600
                    child.sendline('5')
                    quit = child.expect("selection", timeout=1200)
                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    CapacityDetobj = CapacityDet.CapacityDet(maxAudioModel)
                    CapacityDetobj.flatincrports()
                    return False

                elif int(maxAudioModel) <= (int(self.loadcapacity) - 5):
                    # time.sleep(float(self.loadDur))
                    print "DSP Utilization is less than 65%, increasing the ports. "
                    child.timeout = 600
                    child.sendline('5')
                    quit = child.expect("selection", timeout=1200)
                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    CapacityDetobj = CapacityDet.CapacityDet(maxAudioModel)
                    CapacityDetobj.Dynamiccheck()
                    return False

                elif int(maxAudioModel) > (int(self.loadcapacity) + 5):
                    print "DSP Utilization is more than 75%, decreasing the ports. "
                    child.sendline('5')
                    quit = child.expect("selection", timeout=1200)
                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    CapacityDetobj = CapacityDet.CapacityDet(maxAudioModel)
                    CapacityDetobj.decreaseThePorts()
                    return False
                else:
                    # child.timeout=float(self.loadDur)
                    print "DSP % is b/w " + str((int(self.loadcapacity) - 5)) + "&" + str((int(self.loadcapacity) + 5))
                    print "Continuing the load model for the specified " + self.loadDur + " seconds. "
                    child.timeout = float(self.loadDur)
                    child.sendline(' ')
                    try:
                        exit = child.expect('Anything')
                    except pexpect.TIMEOUT:
                        print "value :"
                    print "Stopping the Load Model. "
                    child.sendline('5')
                    print "Waiting to exit from the Load Model"
                    quit = child.expect('selection', timeout=1200)
                    child.sendline('0')
                    final_quit = child.expect("Entered")
                    child.sendline('Y')
                    print "Load Model ended. @ The End"
                    os.system('rm -rf atoutput*')
                    os.system("echo 'PASSED!!!' > verdict.txt")
                    return True
