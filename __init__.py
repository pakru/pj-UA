import sys
import pjsua as pj
import time
import threading
import os
import atexit

print('Creating lib instance...')
lib = pj.Lib()

def log_cb(level, str, len):
    print(str, end='\n')

def pjLibDestroy():
    global lib
    print('Destroying lib...')
    lib.hangup_all
    lib.destroy
    lib = None
    print('Destroyed')

atexit.register(pjLibDestroy)

print('Making configuration...')
logingConfiguration = pj.LogConfig()
logingConfiguration.console_level=6
logingConfiguration.level=6
logingConfiguration.filename='/tmp/pj.log'
#logingConfiguration.callback=log_cb

pjUAconfig = pj.UAConfig()
pjUAconfig.max_calls = 20
pjUAconfig.user_agent = 'Yealink SIP-T29G 46.80.0.125'
#pjUAconfig.user_agent = 'Tadiran SIP-T328P 2.72.19.4 00:15:65:50:81:1b'
listenAddr = str(os.environ.get('TC_EXT_TRUNK_IP'))
#listenAddr = '192.168.118.12'
           
print('Init lib pj...')
try:    
    lib.init(ua_cfg=pjUAconfig,log_cfg = logingConfiguration)
except pj.Error as e:
    print ('Lib pjsua init exception: ' + str(e))
    #pjLibDestroy()
    sys.exit(1)

#host = '192.168.118.12'
print('Init transport')
try:    
    transport = lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(bound_addr=listenAddr))
except pj.Error as e:
    print ('Lib pjsua transport exception: ' + str(e))
    #pjLibDestroy()
    sys.exit(1)

print('Starting lib...')
try: 
    lib.start()
except pj.Error as e:
    print ('Lib pjsua start exception: ' + str(e))
    #pjLibDestroy()
    sys.exit(1)

print('Disabling sound devices...')
lib.set_null_snd_dev()