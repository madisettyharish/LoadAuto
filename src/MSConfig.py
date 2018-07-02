#!/usr/bin/python
from SNMPLib import SNMPLib
import config
import time
import logging
import pexpect

loggerlocal = logging.getLogger('framework.log')

snmpobj = SNMPLib()

class MSConfig:

    def __init__(self):

        self.mrfIp = config.swMrfCredentials['mrfIp']
        self.mrfUserName = config.swMrfCredentials['mrfUserName']
        self.mrfPassword = config.swMrfCredentials['mrfPassword']
        self.ignore_user_err = config.ignore_Specific_Errors['ErrorList'].split('=')

    def checkmscores(self):

        audiocores = snmpobj.getMSaudiocores()
        loggerlocal.debug("Checking the MS cores")
        if audiocores == '0':
            print "There are no audio cores, Setting default core (equal audio & video)"
            allocated = int(snmpobj.snmpget('caNumMpCores.0'))
            if allocated >= 4:
                snmpobj.snmpset('caNumVxmlCores.0', '0', 'u')
                snmpobj.snmpset('caNumHdEncCores.0', '0', 'u')
                snmpobj.snmpset('caNumVideoCores.0', str(allocated/2), 'u')
                self.sutreboot()
            else:
                print "SUT has less than 4 cores"
                logging.debug("SUT is having less than 4 MP cores. ")
        else:
            print "SUT has " + audiocores + " cores... "

    # Load should be running during this fun call
    def refactorcores(self, achievedports='1000', videoload = False, confload = False):

        loggerlocal.debug(
            "Evaluating whether core refactoring is necessary based on the achieved ports %s" %(achievedports))
        if int(achievedports) > 1000:
            loggerlocal.debug("Achieved ports are more thank 1000, core refactoring is in progress... ")
            print "Number of achieved ports are more than 1000, refactoring SUT cores"
            # Getting the SUT cores
            audiocores = snmpobj.getMSaudiocores()
            videocores = snmpobj.snmpget('caNumVideoCores.0')
            #hcvideocores = snmpobj.snmpget('caNumHdEncCores.0')

            # Getting the DSP Utilization
            '''
            audiodsp = snmpobj.snmpget('dspstatMaxAudioDspUtilizationModeled.2')
            videodsp = snmpobj.snmpget('dspstatMaxVideoDspUtilizationModeled.2')
            hdvideodsp = snmpobj.snmpget('dspstatMaxHcVideoDspUtilizationModeled.2')
            '''

            if not videoload and not confload:
                newaudiocore = str(int((round((1000/int(achievedports)) * int(audiocores), 0))))
                snmpobj.snmpset('caNumVideoCores.0', int(videocores)+(int(audiocores)-int(newaudiocore)), 'u')
            else:
                pass
            loggerlocal.debug("Core refactoring is completed")
            return True

        else:
            return False

    def setsyslog(self):

        loggerlocal.debug(" Setting SCRM severity to - Notice and others to - Warning")
        # Setting to Warning
        snmpobj.snmpset('syslogConProtSeverity.1', '16', 'u')
        snmpobj.snmpset('syslogSESeverity.1', '16', 'u')
        snmpobj.snmpset('syslogOAMPSeverity.1', '16', 'u')
        snmpobj.snmpset('syslogPlatformSeverity.1', '16', 'u')
        snmpobj.snmpset('syslogMSMLSeverity.1', '16', 'u')
        snmpobj.snmpset('syslogMpSeverity.1', '16', 'u')
        snmpobj.snmpset('syslogSpeechManagerSeverity.1', '16', 'u')
        # Setting SCRM to Notice
        snmpobj.snmpset('syslogSCRMSeverity.1', '32', 'u')

    def sutresetservice(self):

        print "Performing SUT service restart... "
        loggerlocal.debug("Making SUT OOS ")
        snmpobj.snmpset('comSetServiceMode.1.2', '2', 'i')
        time.sleep(3)
        snmpobj.snmpset('comSetServiceMode.1.2', '1', 'i')
        time.sleep(5)
        if snmpobj.snmpget('comSetServiceMode.1.2') == "inServiceMode":
            loggerlocal.debug("SUT is InService")
        else:
            loggerlocal.debug("SUT is still OSS, Please check ")

    def sutresetstats(self):

        print "Re-setting Stats and Stats Interval "
        snmpobj.snmpset('statInterval.0', '5', 'u')
        if snmpobj.snmpget('statInterval.0') == "5":
            loggerlocal.debug("statInterval is 5")
        else:
            loggerlocal.debug("***ERROR statInterval is not 5")
        snmpobj.snmpset('cardstatReset.1', '1', 'i')

    def sutreboot(self):

        loggerlocal.debug("Rebooting SUT ")
        print "SUT is going for reboot... "
        snmpobj.snmpset('nodeReboot.0', '1', 'i')
        reboot = True
        sleeptime = 300
        while reboot:
            time.sleep(sleeptime)
            if snmpobj.snmpget('comSetServiceMode.1.2') != "inServiceMode":
                loggerlocal.debug("Waiting for SUT to come UP")
                print "SUT is still not UP... waiting for 120 sec more"
                sleeptime = 120
            else:
                loggerlocal.debug("SUT is UP and Running... ")
                print "SUT is UP and Running"
                reboot = False

    def copytopscript(self):

        print "Copying TOP script"
        SSH_NEWKEY = r'(?i)are you sure you want to continue connecting \(yes/no\)\?'
        COMMAND_PROMPT = '[#] '
        child1 = pexpect.spawn("scp /root/DV_Load_Python_Files/loadtop.sh %s@%s:/root/. " % (self.mrfUserName, self.mrfIp))
        iii = child1.expect([pexpect.TIMEOUT, SSH_NEWKEY, '(?i)password', COMMAND_PROMPT, pexpect.EOF])
        if iii == 0:
            print "scp timeout"
        elif iii == 1:
            child1.sendline('yes')
            child1.expect([pexpect.TIMEOUT, SSH_NEWKEY, '(?i)password', COMMAND_PROMPT, pexpect.EOF])
            child1.sendline('%s' % (self.mrfPassword))
            # print("In scp 1....")
        elif iii == 2:
            child1.sendline('%s' % (self.mrfPassword))
            child1.expect(['#', pexpect.TIMEOUT, SSH_NEWKEY, '(?i)password', COMMAND_PROMPT, pexpect.EOF])
            # print("In scp 2....")
        elif iii == 3:
            pass

    def eval_local_pexpect(self, con):

        COMMAND_PROMPT = '[#] '
        SSH_NEWKEY = r'(?i)are you sure you want to continue connecting \(yes/no\)\?'
        i = con.expect([pexpect.TIMEOUT, COMMAND_PROMPT, SSH_NEWKEY, '(?i)password', pexpect.EOF], timeout=120)
        if i == 0:
            print "***ERROR pexpect timeout. "
            return False
        elif i == 1:
            # print "Received command prompt"
            pass
        elif i == 2:
            con.sendline('yes')
            first = self.eval_local_pexpect(con)
            con.sendline('%s' %(self.mrfPassword))
            first = self.eval_local_pexpect(con)
        elif i == 3:
            con.sendline('%s' %(self.mrfPassword))
            first = self.eval_local_pexpect(con)
        else:
            print "There is some issue in the pexpect, Please check"
            return False
        return True

    def syslogcheck(self):

        #listoferror = ['EN_MM_RS_OUT_OF_DSP_CPU', 'Error opening clip', 'ACK contains no SDP is un-expected', ': A:',
        #              ': C:', 'EN_SRM_RS_FILE_NOT_FOUND', 'EN_MM_RS_OUT_OF_BANDWIDTH', 'out-of-dsp resources'
        #               ]
        listoferror = ['Error opening clip', 'ACK contains no SDP is un-expected', ': A:',
                       ': C:', 'EN_SRM_RS_FILE_NOT_FOUND']
        listerrignore = ['EN_MM_RS_OUT_OF_DSP_CPU', 'EN_MM_RS_OUT_OF_BANDWIDTH', 'out-of-dsp resources']
        #user_err_ignore_list = ['EN_MM_RS_OUT_OF_DSP_CPU', 'EN_MM_RS_OUT_OF_BANDWIDTH', 'out-of-dsp resources']
        user_err_ignore_list = []
        user_err_ignore_list.extend(self.ignore_user_err)
        user_err_ignore_list = filter(str.strip, user_err_ignore_list)
        print user_err_ignore_list

        audiocores = snmpobj.getMSaudiocores()
        cal_audiocores = int(audiocores) * 3

        try:
            m = pexpect.spawn("ssh %s@%s" % (self.mrfUserName, self.mrfIp))
        except IOError:
            print "There is problem in doing SSH. "
        else:
            first = self.eval_local_pexpect(m)
            is_syslog_issue = False
            is_syslog_issue_ignore = False
            is_user_err_ignore = False
            print "Calculating Audio Load average ..."
            m.sendline(
                "cat /var/log/messages | grep -i \'audio load:\' | tail -%s | awk -F\'Audio Load:\' \'{print $2}\' | awk -F \'(\' \'{print $1}\' | awk \'{sum += $1} {print sum}\'  | tail -1 | awk \'{print $1/%s}\'" % (
                cal_audiocores, cal_audiocores))
            index2 = m.expect(['#', pexpect.EOF])
            avgCapDet = ''
            if index2 == 0:
                avgCapDet = m.before.split('\n')[-2]
                print "The average capacity of the load model calculated from syslog is : " + avgCapDet
                print m.before
            else:
                print "There is some issue in collecting average capacity, please check... "
                print m.before

            print "Checking syslog errors... "
            for i in range(len(listoferror)):


                m.sendline("grep '%s' /var/log/messages| wc -l" % (listoferror[i]))
                index1 = m.expect(['#'])
                if index1 == 0:
                    findvalue = m.before.split('\n')[-2]
                    findvalue = int(findvalue)
                    if findvalue == 0:
                        print "No " + listoferror[i] + " errors"
                        continue
                    else:
                        print "Yes There are error logs for " + listoferror[i]
                        m.sendline("grep '%s' /var/log/messages | awk -F'->' '{$1=\"\"; print $0}' |uniq >messages.err"
                                   %(listoferror[i]))
                        time.sleep(1)
                        index11 = m.expect(['#'])
                        if index11 == 0:
                            print "uniq messages processed"
                            pass
                        else:
                            print "There is some issue in processing the syslog"
                        #print "***ERROR in the execution"
                        is_syslog_issue = True
                        #if listoferror[i] in listerrignore:
                        #    is_syslog_issue_ignore = True
                else:
                    print "There is some issue in processing the syslog"

            for i in range(len(listerrignore)):
                m.sendline("grep '%s' /var/log/messages| wc -l" % (listerrignore[i]))
                index1 = m.expect(['#'])
                if index1 == 0:
                    findvalue = m.before.split('\n')[-2]
                    findvalue = int(findvalue)
                    if findvalue == 0:
                        print "No " + listerrignore[i] + " errors"
                        continue
                    else:
                        print "Yes There are error logs for " + listerrignore[i]
                        m.sendline("grep '%s' /var/log/messages | awk -F'->' '{$1=\"\"; print $0}' |uniq >>messages.err"
                                   %(listerrignore[i]))
                        time.sleep(1)
                        index11 = m.expect(['#'])
                        if index11 == 0:
                            print "uniq messages processed"
                            pass
                        else:
                            print "There is some issue in processing the syslog"
                        #print "***ERROR in the execution"
                        is_user_err_ignore = True
                else:
                    print "There is some issue in processing the syslog"

            for i in range(len(user_err_ignore_list)):
                m.sendline("grep '%s' /var/log/messages| wc -l" % (user_err_ignore_list[i]))
                index1 = m.expect(['#'])
                if index1 == 0:
                    findvalue = m.before.split('\n')[-2]
                    findvalue = int(findvalue)
                    if findvalue == 0:
                        print "No " + user_err_ignore_list[i] + " errors"
                        continue
                    else:
                        print "Yes There are error logs for " + user_err_ignore_list[i]
                        m.sendline("grep '%s' /var/log/messages | awk -F'->' '{$1=\"\"; print $0}' |uniq >>messages.err"
                                   %(user_err_ignore_list[i]))
                        time.sleep(1)
                        index11 = m.expect(['#'])
                        if index11 == 0:
                            print "uniq messages processed"
                            pass
                        else:
                            print "There is some issue in processing the syslog"
                        #print "***ERROR in the execution"
                        is_user_err_ignore = True
                else:
                    print "There is some issue in processing the syslog"

            print "syslog processing completed... "
            if is_syslog_issue:
                print "There is some issue in the syslog processing " + str(is_syslog_issue)
            return is_syslog_issue, avgCapDet, is_syslog_issue_ignore, is_user_err_ignore
