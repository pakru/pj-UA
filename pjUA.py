import sys, logging
import pjsua as pj
import _pjsua as _pj
import time
import threading
import binascii
from pjSIP_py import lib


def log_cb(level, str, len):
    print(str, end='\n')


class SubscriberUA(object):
    def __init__(self,domain,username,passwd,sipProxy,displayName,uaIP,regExpiresTimeout=200,req100rel=False,autoAnswer=True):
        global lib
        logging.info('Creating of pjsip subcriber UA: ' + username + '@'+domain)
        self.uaCurrentCallInfo = pj.CallInfo
        self.uaCurrentCall = pj.Call
        self.uaAccountInfo = pj.AccountInfo
        self.uaAutoAnswerBehavior=autoAnswer
        self.failureFlag = False
        self.expectedState = None

        self.AccConfig = pj.AccountConfig(domain=domain, username=username, password=passwd, display=displayName, proxy='sip:'+sipProxy)
        self.AccConfig.reg_timeout = regExpiresTimeout
        self.AccConfig.require_100rel = req100rel

        #print('Creating account...')
        self.acc = lib.create_account(self.AccConfig)

        #print('Creating callback account...')    
        self.acc_cb = MyAccountCallback(account=self.acc, accInstance=self)

        #print('Setting callback account')
        self.acc.set_callback(self.acc_cb)

        #print('Registering for registration...')
        self.acc_cb.wait()

        #print('\n')
        #print('Registration status=', self.acc.info().reg_status, "(" + self.acc.info().reg_reason + ")")
        print(str(self.uaAccountInfo.uri)+': Registration status=', self.uaAccountInfo.reg_status, "(" + self.uaAccountInfo.reg_reason + ")")
        logging.info(str(self.uaAccountInfo.uri)+': Registration status=', str(self.uaAccountInfo.reg_status), "(" + str(self.uaAccountInfo.reg_reason) + ")")

        self.soundsPath = sys.path[-1] + '/pjSIP_py/pjsounds/'
        #print('Sounds path: ' + self.soundsPath)
        self.playerID=lib.create_player(filename=self.soundsPath + 'demo-instruct-low.wav', loop=True)
        self.playerSlot=lib.player_get_slot(self.playerID)
        #self.playerSlot=0

    def resetFailure(self):
        self.failureFlag = False

    def setFailure(self):
        self.failureFlag = True

    def log_cb(level, str, len):
        print(str, end='\n')

    def updateAccountData(self):
        self.uaAccountInfo = self.acc.info()

    def sendInbandDTMF(self, dtmfDigit, duration=0.2):
        #self.uaCurrentCall.dial_dtmf(digits=str(dtmfDigit))
        #self.dtmfSoundsPath = './pjsounds/dtmf/long/'
        logging.info(str(self.uaAccountInfo.uri)+': Send inband DTMF: '+ dtmfDigit)
        self.dtmfSoundsPath = sys.path[-1] + '/pjSIP_py/pjsounds/dtmf/long/'
        if dtmfDigit in '1':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '1.wav'
        elif dtmfDigit in '2':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '2.wav'
        elif dtmfDigit in '3':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '3.wav'
        elif dtmfDigit in '4':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '4.wav'
        elif dtmfDigit in '5':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '5.wav'
        elif dtmfDigit in '6':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '6.wav'
        elif dtmfDigit in '7':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '7.wav'
        elif dtmfDigit in '8':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '8.wav'
        elif dtmfDigit in '9':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '9.wav'
        elif dtmfDigit in '0':
            self.dtmfSoundfilename = self.dtmfSoundsPath + '0.wav'
        elif dtmfDigit in '*':
            self.dtmfSoundfilename = self.dtmfSoundsPath + 'star.wav'
        elif dtmfDigit in '#':
            self.dtmfSoundfilename = self.dtmfSoundsPath + 'hash.wav'
        else:
            print('Wrong number')
            return False

        #print('Creating dtmf player')
        self.dtmfPl=lib.create_player(filename=self.dtmfSoundfilename, loop=True)
        #print('Getting slot of dtmf player')
        self.dtmfSl=lib.player_get_slot(self.dtmfPl)
        #print('Making conf connect')
        lib.conf_connect(self.dtmfSl, self.uaCurrentCallInfo.conf_slot)
        #print('Sleeping 0.2')
        time.sleep(duration)
        #print('Return back slot')
        #lib.conf_connect(self.playerSlot, self.uaCurrentCallInfo.conf_slot)
        #print('Destroying player')
        lib.player_destroy(self.dtmfPl)              

    def makeCall(self,phoneURI):
        self.dstURI = 'sip:' + phoneURI
        logging.info(str(self.uaAccountInfo.uri) +': calling to: '+ self.dstURI)
        self.acc.make_call(dst_uri=self.dstURI,cb=MyCallCallback(accCallInstance=self))

    def getCurrentUAState(self):
        pass

    def ctr(self,dstURI):
        self.url = dstURI
        self.g_current_call = self.uaCurrentCall._id
        self.msg_data = _pj.msg_data_init()
        self.status = _pj.call_xfer(self.g_current_call, self.url, self.msg_data)
        if self.status != 0:
            print('Some error')
            #pj.perror(THIS_FILE, "Error transferring call ", status)

    def ctr_request(self,dstURI,currentCall):
        print(str(self.uaAccountInfo.uri)+': making my ugly transfering...')
        logging.info(str(self.uaAccountInfo.uri)+': making unattend transfer to ' + dstURI)
        self.hdrs = []
        self.hdrs.append(('Refer-To','<sip:'+ dstURI +'>'))
        self.hdrs.append(('Referred-By',str(self.uaAccountInfo.uri)))
        self.hdrs.append(('Event','refer'))
        #self.accCallInstance.uaCurrentCall.transfer(dest_uri='sip:1510@192.168.118.38:5092;user=phone',hdr_list=hdrs)
        try:
            currentCall.send_request(method='REFER', hdr_list=self.hdrs)
        except Exception as e:
            print('Failed to transfer due to exception: ' + str(e))
            logging.error('Failed to transfer due to exception: ' + str(e))
            return False
        return True
        #print('Hangup')
        #self.uaCurrentCall.hangup(code=200, reason='Release')


    def getRegStatus(self):
        #print('Registration complete, status=' + str(self.acc.info().reg_status),  ' reason: ' + str(self.acc.info().reg_reason))
        return int(self.acc.info().reg_status)

    def getRegReason(self):
        return str(self.acc.info().reg_reason)

class MyCallCallback(pj.CallCallback):
    def __init__(self, accCallInstance, call=None):
        pj.CallCallback.__init__(self, call)
        self.accCallInstance = accCallInstance

    # Notification when call state has changed
    def on_state(self):
        self.accCallInstance.uaCurrentCallInfo = self.call.info()
        self.accCallInstance.uaCurrentCall = self.call
        print(str(self.accCallInstance.uaAccountInfo.uri), end=': ')
        print('Call is ', self.call.info().state_text, end='; ')
        print('last code =', self.call.info().last_code, end='; ')
        print('(' + self.call.info().last_reason + ')', end = '; ')
        print('role =', self.call.info().role, end='; ')
        print('from =', self.call.info().remote_uri)
        logging.info(str(self.accCallInstance.uaAccountInfo.uri) + ': ' + 'Call is ' + self.call.info().state_text + '; ' +
                     'last code =' + str(self.call.info().last_code) + '; ' + '(' + str(self.call.info().last_reason) + '); ' +
                     'from =' + self.call.info().remote_uri)
        
    def on_dtmf_digit(self, digits):
        #self.call.dial_dtmf(digits=str(digits))
        '''
        #self.call.dial_dtmf(digits=sym)
        sym = b'\x31\x31\x31\x31\x31'
        #sym = hex(30)
        print('binascii: ' + str(sym))
        self.call.dial_dtmf(digits=sym)
        sym = b'\x35'
        #sym = hex(30)
        print('binascii: ' + str(sym))
        self.call.dial_dtmf(digits=sym)
        sym = b'\x37'
        #sym = hex(30)
        print('binascii: ' + str(sym))
        self.call.dial_dtmf(digits=sym)
        sym = b'\x32'
        #sym = hex(30)
        print('binascii: ' + str(sym))
        self.call.dial_dtmf(digits=sym)
        '''
        print('Recieved DTMF digit: '+ digits)
        #print('And dialing...')
        

    # Notification when call's media state has changed.
    def on_media_state(self):
        #global lib
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            
            # Connect the call to sound device
            self.call_slot = self.call.info().conf_slot
            lib.conf_connect(self.call_slot, 0)
            lib.conf_connect(self.accCallInstance.playerSlot, self.call_slot)
            print(str(self.accCallInstance.uaAccountInfo.uri) +': I can talk!')
            #sym = binascii.a2b_uu('^')
            '''
            for i in range(30,100):
                k = hex(i)
                print('k = ' + str(k))
                try:
                    self.call.dial_dtmf(digits=k)
                except Exception as e:
                    print('Exception')
            '''
            #sym = b'\x40'
            #print('binascii: ' + str(sym))
            #self.call.dial_dtmf(digits=sym)


class MyAccountCallback(pj.AccountCallback):
    sem = None
    def __init__(self, account, accInstance):
        self.accInstance = accInstance
        pj.AccountCallback.__init__(self, account)

    def wait(self):
        self.sem = threading.Semaphore(0)
        self.sem.acquire()

    def on_reg_state(self):
        self.accInstance.uaAccountInfo = self.account.info()
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()

    def on_incoming_call(self, call):
        #global SubscriberUA.uaCurrentCallInfo
        print(str(self.accInstance.uaAccountInfo.uri), end=': ')
        print('We`ve got incoming call from: '+ str(call.info().remote_uri))
        logging.info(str(self.accInstance.uaAccountInfo.uri) + ': recieved incoming call from: ' + str(call.info().remote_uri))
        #SubscriberUA.uaCurrentCallInfo = call.info()
        self.myCallCb = MyCallCallback(accCallInstance=self.accInstance)
        call.set_callback(self.myCallCb)
        call.answer(code=180, reason='Ringing')
        #time.sleep(1)
        if self.accInstance.uaAutoAnswerBehavior:
            call.answer(code=200, reason='Answering')

