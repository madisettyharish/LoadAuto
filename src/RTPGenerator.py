#!/usr/bin/python
import pexpect
import sys
import config
import logging
from SNMPLib import SNMPLib
import CapacityDet
import commands

snmpobj = SNMPLib()

class RTPGenerator:

    def __init__(self, logpath):
        self.mrfIp = config.swMrfCredentials['mrfIp']
        self.rtpgIp = config.rtpgCredentials['rtpgIp']
        self.rtpgPath = config.rtpgCredentials['rtpgPath']
        self.rtpgPort = config.rtpgCredentials['RTPG_PORT']
        self.SATPath = config.SATDetails['SATPath']
        self.logPath = logpath
        self.logger = logging.getLogger("ClearMrfLog.py")
        self.logger.debug("clearing MRF Log ")
        self.loadAT = config.loadDetails['ATFile']
        self.loadATmodel = config.loadDetails['modelCfg']
        self.sutctrlip = config.swMrfCredentials['MS_Server_Control_IP']

    def prepareRtpgCfg(self):

        print "Replacing TrafficAddress=" + self.rtpgIp + "& SignalPort=" + self.rtpgPort
        commands.getoutput("sed -i '/TrafficAddress/d' %s/rtpg.cfg" %(self.rtpgPath))
        commands.getoutput("sed -i '/SignalPort/d' %s/rtpg.cfg" %(self.rtpgPath))
        commands.getoutput('sed -i "\$aTrafficAddress=%s" %s/rtpg.cfg' %(self.rtpgIp, self.rtpgPath))
        commands.getoutput('sed -i "\$aSignalPort=%s" %s/rtpg.cfg' %(self.rtpgPort, self.rtpgPath))

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

    def startRTPG(self):

        os.system('cp %sMscConfig.cfg .'%(self.SATPath))
        time.sleep(2)
        os.system('cp %s%s %s/models.standard/' %(self.SATPath, self.loadATmodel, self.SATPath))
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
            child.sendline('10')
            next_menu = child.expect(["Append '-'"])
            if next_menu == 0:
                child.sendline('1050')
                try:
                    exit = child.expect('Anything', timeout=180)
                except pexpect.TIMEOUT:
                    print "value :"