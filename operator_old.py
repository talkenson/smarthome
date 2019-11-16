import time, json, random, curses
import requests as req

pref = {
'server': '217.71.129.139:4195',
'key': 'DEF',
'uname': 'DEF',
'ts': '-1',
'token': 'DEF'
}

uname = input('Please, state your nickname below:\n -> ')
pref['uname'] = uname
key = input('Please, type a random [A-Za-z0-9] key below:\n -> ')
pref['key'] = key
server = input('Please, enter server address below (now = %s) (Hit Enter to save):\n -> ' % pref['server'])
if not server == "":
    pref['server'] = server

print('There\'s your preferences:')
print(pref)

print('\nTrying to connect to server...')
r = req.get('http://%s/reg/%s:%s' % (pref['server'], pref['uname'], pref['key'])).json()
if r['status'] == "ok":
    pref['token'] = r['response']['token']
    print("Successfully connected!")
elif r['status'] == "fail":
    print("#%s - %s" % (r['code'], r['desc']))
    exit(0)

creds = {'key': pref['key'], 'token': pref['token']}

while True:
    try:
        r = req.post('http://%s/updates' % pref['server'], json=creds).json()
    except req.exceptions.RequestException:
        continue

    if not r['status'] == 'ok':
        print('Something went wrong, repeating...')

    if r['total'] > 0:
        for msg in r['response']:
            if not msg['uname'] == pref['uname']:
                print('%s: %s' % (msg['uname'], msg['message']), end='\n')
    text = input('%s (You): ' % pref['uname'])
    if text == '':
        pass
        #print ("\r\b")
    else:
        # 192.168.1.39:12500
        ndata = {}
        ndata.update({'message': text})
        ndata.update(creds)
        m = req.post('http://%s/send' % pref['server'], json=ndata).json()

    #if int((datetime.now() - tick).total_seconds()) > 300:
    #    tick = datetime.now()
    #    save_prefs()

    time.sleep(0.01)
