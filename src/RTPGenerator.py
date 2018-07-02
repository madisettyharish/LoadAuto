#!/usr/bin/python
import pexpect
import sys
import config
import logging
from SNMPLib import SNMPLib
import os
import commands
import time

snmpobj = SNMPLib()

class RTPGenerator:

    def __init__(self):
        self.rtpgIp = config.rtpgCredentials['rtpgIp']
        self.rtpgPath = config.rtpgCredentials['rtpgPath']
        self.rtpgPort = config.rtpgCredentials['RTPG_PORT']
        self.rtpgUserName = config.rtpgCredentials['rtpgUserName']
        self.rtpgPassword = config.rtpgCredentials['rtpgPassword']
        self.loadDur = config.loadDurationDetails['loadduration']
        self.loadname = config.loadDetails['loadName']

    def prepareRtpgCfg(self, con):

        print "Replacing TrafficAddress=" + self.rtpgIp + "& SignalPort=" + self.rtpgPort
        con.sendline("sed -i '/TrafficAddress/d' %s/rtpg.cfg" %(self.rtpgPath))
        first = self.eval_local_pexpect(con)
        con.sendline('sed -i "\$aTrafficAddress=%s" %s/rtpg.cfg' %(self.rtpgIp, self.rtpgPath))
        first = self.eval_local_pexpect(con)

        con.sendline("sed -i '/SignalPort/d' %s/rtpg.cfg" %(self.rtpgPath))
        first = self.eval_local_pexpect(con)
        con.sendline('sed -i "\$aSignalPort=%s" %s/rtpg.cfg' %(self.rtpgPort, self.rtpgPath))
        first = self.eval_local_pexpect(con)

    def eval_local_pexpect(self, con):

        COMMAND_PROMPT = '[#] '
        SSH_NEWKEY = r'(?i)are you sure you want to continue connecting \(yes/no\)\?'
        i = con.expect([pexpect.TIMEOUT, COMMAND_PROMPT, SSH_NEWKEY, '(?i)password', pexpect.EOF], timeout=10)
        if i == 0:
            print "***ERROR pexpect timeout. "
            return False
        elif i == 1:
            # print "Received command prompt"
            pass
        elif i == 2:
            con.sendline('yes')
            first = self.eval_local_pexpect(con)
            con.sendline('%s' %(self.rtpgPassword))
            first = self.eval_local_pexpect(con)
        elif i == 3:
            con.sendline('%s' %(self.rtpgPassword))
            first = self.eval_local_pexpect(con)
        else:
            print "There is some issue in the pexpect, Please check"
            return False
        return True

    def eval_local_pexpect_pwd(self, con, password):

        COMMAND_PROMPT = '[#] '
        SSH_NEWKEY = r'(?i)are you sure you want to continue connecting \(yes/no\)\?'
        i = con.expect([pexpect.TIMEOUT, COMMAND_PROMPT, SSH_NEWKEY, '(?i)password', pexpect.EOF], timeout=10)
        if i == 0:
            print "***ERROR pexpect timeout. "
            return False
        elif i == 1:
            # print "Received command prompt"
            pass
        elif i == 2:
            con.sendline('yes')
            first = self.eval_local_pexpect(con)
            con.sendline('%s' %(password))
            first = self.eval_local_pexpect(con)
        elif i == 3:
            con.sendline('%s' %(password))
            first = self.eval_local_pexpect(con)
        else:
            print "There is some issue in the pexpect, Please check"
            return False
        return True

    def startRTPG(self):

        try:
            child = pexpect.spawn('ssh %s@%s' % (self.rtpgUserName, self.rtpgIp))
        except IOError:
            print "there is problem"
        else:
            child.timeout = 300
            first = self.eval_local_pexpect(child)
            print child.before
            self.prepareRtpgCfg(child)
            child.sendline("scp %s/rtpg.cfg ." %(self.rtpgPath))
            first = self.eval_local_pexpect(child)
            print child.before
            child.sendline("cd %s " %(self.rtpgPath))
            first = self.eval_local_pexpect(child)
            print child.before
            child.sendline("pwd")
            first = self.eval_local_pexpect(child)
            print child.before
            print "Killing the RTPG if present & Running new instance... "
            child.timeout = float(self.loadDur)
            child.sendline('nohup /root/start_rtpg.sh %s &' %(self.rtpgPath))
            first = self.eval_local_pexpect(child)
            print child.before
            if first:
                print "RTPG Started Successfully... "
            else:
                print "There is some issue in starting RTPG script, please check"

    def killRTPG(self):

        try:
            child = pexpect.spawn('ssh %s@%s' % (self.rtpgUserName, self.rtpgIp))
        except IOError:
            print "there is problem"
        else:
            child.sendline("cat /root/start_rtpg.sh | grep -v '^\$rtpg_bin' > /root/kill_rtpg.sh")
            first = self.eval_local_pexpect(child)
            child.sendline("chmod +x /root/kill_rtpg.sh")
            first = self.eval_local_pexpect(child)
            child.sendline("nohup /root/kill_rtpg.sh %s &")
            first = self.eval_local_pexpect(child)
            if first:
                print "RTPG killed Successfully... "
            else:
                print "There is some issue in killing RTPG script, please check"

    def collectpcap(self):

        print "Collecting pcap for 2 min"
        os.system("nohup /root/start_tcpdump.sh %s %s &" %(self.rtpgIp, self.loadname))

    def transferpcap(self):

        print "Transferring collected pcap ..."
        #os.system("nohup /root/start_tcpdump.sh %s %s &" % (self.rtpgIp, self.loadname))
        child1 = pexpect.spawn("scp  %s@%s:/root/%s.pcap  /root/%s/."
                               % (self.rtpgUserName, self.rtpgIp, self.loadname, self.loadname))
        first = self.eval_local_pexpect_pwd(child1, self.rtpgPassword)
        time.sleep(5)
