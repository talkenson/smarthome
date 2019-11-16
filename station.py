import os, sys, time, json, random, time, datetime, curses
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import _thread
from threading import Timer
import atexit
import uuid
import pickle
import re

import icons


app = Flask(__name__)
CORS(app)
plugins = {}

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

history = []

tokens = {

}

motd = "Sander's home"

params = {
'door' : 'unlocked',
'light' : 'off',
'lock' : 'locked',
'air' : 'off'
}

letters = sum([
        [chr(s) for s in range(ord('a'), ord('z')+1)],
        [chr(s) for s in range(ord('0'), ord('9')+1)],
        [' ']
        ], [])
def getNum(c):
    for i in range(len(letters)):
        if c == letters[i]:
            return i


def saveAll():
    with open('tokens.pickle', 'wb') as f:
        pickle.dump(tokens, f)
    with open('history.pickle', 'wb') as f:
        pickle.dump(history, f)

atexit.register(saveAll)

def loadAll():
    global tokens, history
    if os.path.exists('tokens.pickle'):
        with open('tokens.pickle', 'rb') as f:
            tokens = pickle.load(f)
    if os.path.exists('history.pickle'):
        with open('history.pickle', 'rb') as f:
            history = pickle.load(f)

loadAll()


def execAdmin(com):
    global tokens, history
    comm = com.split()
    if comm[0] == 'op':
        if len(comm) > 1:
            if comm[1] in [tokens[token]['uname'] for token in tokens.keys()]:
                token = [token for token in tokens.keys() if tokens[token]['uname'] == comm[1]][0]
                tokens[token]['isAdmin'] = True
    if comm[0] == 'deop':
        if len(comm) > 1:
            if comm[1] in [tokens[token]['uname'] for token in tokens.keys()]:
                token = [token for token in tokens.keys() if tokens[token]['uname'] == comm[1]][0]
                tokens[token]['isAdmin'] = False
    if comm[0] == 'kick':
        if len(comm) > 1:
            if comm[1] in [tokens[token]['uname'] for token in tokens.keys()]:
                token = [token for token in tokens.keys() if tokens[token]['uname'] == comm[1]][0]
                del tokens[token]
    if comm[0] == 'test':
        history.append({'id':len(history), 'message': 'Testing! The user provided this event is admin.', 'uname': '[SERVER]'})
    if comm[0] == 'wipe':
        if len(comm) > 1:
            if comm[1] == 'tokens':
                history.append({'id':len(history), 'message': 'WARNING!!! YOUR ACCOUNT WILL BE DELETED IN 10 SECS', 'uname': '[DIE]'})
                time.sleep(10)
                tokens = {}
            if comm[1] == 'history':
                del history[:]
                for user in [tokens[token] for token in tokens.keys()]:
                    user['lastupdate'] = -1
                history.append({'id':len(history), 'message': 'WIPE! All messages was deleted from server, use your local copies', 'uname': '[WIPE]'})


@app.route('/reg/<string:uname>:<string:key>')
def reg(uname, key):
    global tokens, history
    # User exists
    if uname in [tokens[token]['uname'] for token in tokens.keys()]:
        if True in [True for token in tokens.keys() if tokens[token]['key'] == key and tokens[token]['uname'] == uname]:
            token = [token for token in tokens.keys() if tokens[token]['key'] == key and tokens[token]['uname'] == uname][0]

            new_token = str(uuid.uuid4())
            tokens[new_token] = tokens[token].copy()
            tokens[new_token]["lastactivity"] = int(time.time())
            tokens[new_token]["online"] = True

            #tokens.pop(token, None)
            if token in tokens:
                del tokens[token]

            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            return Response('{"status": "ok", "response": {"uname": "%s", "key": "%s", "token": "%s", "motd": "%s"}}' % (uname, key, new_token, motd), mimetype='application/json')
        else:
            return Response('{"status": "fail", "code": "401", "desc": "nickname already registered, use correct pass"}', mimetype='application/json')
    # New user
    if len(uname) > 2 and len(key) > 2 and len(uname) <= 10:
        for s in list(uname):
            if not s in letters:
                return Response('{"status": "fail", "code": "306", "desc": "uname is required to be defined only in [A-Za-z0-9\_\-\.]"}', mimetype='application/json')
        new_token = str(uuid.uuid4())
        tokens[new_token] = {'uname': uname, 'key': key, 'lastupdate': len(history)-1, "lastactivity": int(time.time()), "online": True}
        if len(tokens.keys()) == 1:
            tokens[new_token].update({'isAdmin': True})


        history.append({'id':len(history), 'message': '%s joined chat!' % uname, 'uname': '[SERVER]'})
        return Response('{"status": "ok", "response": {"uname": "%s", "key": "%s", "token": "%s", "motd": "%s"}}' % (uname, key, new_token, motd), mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "302", "desc": "uname or key isn\'t correct key = (len > 2), uname = (10 >= len > 2) "}', mimetype='application/json')


def encode(phrase):
    ts = int(time.time()*100)
    key0 = 'chinavalidol'
    key1 = ''
    for n, s in enumerate(str(ts)[::-1]):
        key1 += letters[(getNum(s) + getNum(key0[n % len(key0)])) % len(letters)]
    ans = ''
    for n, s in enumerate(phrase):
        ans += letters[(getNum(s) + getNum(key1[n % len(key1)])) % len(letters)]

    return(str(ts) + ans)

def decode(cip):
    ts, cip = cip[:12], cip[12:]
    key0 = 'chinavalidol'
    key1 = ''
    for n, s in enumerate(str(ts)[::-1]):
        key1 += letters[(getNum(s) + getNum(key0[n % len(key0)])) % len(letters)]
    ans = ''
    for n, s in enumerate(cip):
        ans += letters[(getNum(s) - getNum(key1[n % len(key1)])) % len(letters)]
    return(ans)

@app.route('/send', methods=['POST'])
def send():
    global tokens, history, params
    ## if data is encrypted - decrypt it There
    ## There
    data = request.json
    if 'message' in data.keys() and 'token' in data.keys():
        uname = ''
        try:
            uname = tokens[data['token']]['uname']
        except KeyError:
            return Response('{"status": "fail", "code": "402", "desc": "no valid token presented"}', mimetype='application/json')

        token = data['token']
        tokens[token]['lastactivity'] = int(time.time())
        if tokens[token]['online'] == False:
            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            tokens[token]['online'] = True

        # send if was offline, then came online

        if 'isAdmin' in tokens[token].keys() and tokens[token]['isAdmin'] == True and data['message'][:1] == '/':
            adm_r = execAdmin(data['message'][1:])
            return Response(json.dumps({'status': 'ok', 'response': {'type':'admin'}}), mimetype='application/json')

        raw_msg = {'id':len(history), 'message': data['message'], 'uname': uname}

        if 'direct' in data.keys():
            raw_msg['direct'] = data['direct']

        text = decode(data['message'])



        if len(re.findall('(lights*)|(lamps*)', text)) > 0:
            if len(re.findall('(on)|(enable)', text)) > 0:
                params['light'] = 'on'
                raw_msg = {'id':len(history), 'message': 'Lights on!', 'uname': '[HOME]'}
            elif len(re.findall('(off)|(disable)', text)) > 0:
                params['light'] = 'off'
                raw_msg = {'id':len(history), 'message': 'Lights off!', 'uname': '[HOME]'}
            renewLightBox()
        elif len(re.findall('door', text)) > 0:
            if len(re.findall('(open)|(unlock)', text)) > 0:
                params['door'] = 'unlocked'
                raw_msg = {'id':len(history), 'message': 'Door opened!', 'uname': '[HOME]'}
            elif len(re.findall('(close)|(lock)', text)) > 0:
                params['door'] = 'locked'
                raw_msg = {'id':len(history), 'message': 'Door closed!', 'uname': '[HOME]'}
            renewDoorBox()
        elif len(re.findall('(locks*)|(sig)', text)) > 0:
            if len(re.findall('(on)|(close)', text)) > 0:
                params['lock'] = 'locked'
                raw_msg = {'id':len(history), 'message': 'Locked!', 'uname': '[HOME]'}
            elif len(re.findall('(off)|(open)', text)) > 0:
                params['lock'] = 'unlocked'
                raw_msg = {'id':len(history), 'message': 'Unlocked!', 'uname': '[HOME]'}
            renewLockBox()
        elif len(re.findall('(air)|(winds*)', text)) > 0:
            if len(re.findall('(heat)|(hot)', text)) > 0:
                params['air'] = 'heat'
                raw_msg = {'id':len(history), 'message': 'Air heating!', 'uname': '[HOME]'}
            elif len(re.findall('(cool)|(cold)', text)) > 0:
                params['air'] = 'cool'
                raw_msg = {'id':len(history), 'message': 'Air cooling!', 'uname': '[HOME]'}
            elif len(re.findall('(off)|(disable)', text)) > 0:
                params['air'] = 'none'
                raw_msg = {'id':len(history), 'message': 'Ventilation disabled!', 'uname': '[HOME]'}
            renewHeatBox()
        else:
            #print('unknown command')
            raw_msg = {'id':len(history), 'message': 'unknown!', 'uname': '[HOME]'}

        #print(params)
        #print(' ENCODED = ',data['message'])

        history.append(raw_msg)
        return Response(json.dumps({'status': 'ok', 'response': {}}), mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "501", "desc": "forbidden, because you don\'t provided [message, token]"}', mimetype='application/json')

@app.route('/updates', methods=['GET'])
@app.route('/send', methods=['GET'])
def err_usePost():
    return Response('{"status": "fail", "code": "500", "desc": "use POST request instead of GET"}', mimetype='application/json')

@app.route('/updates', methods=['POST'])
def updates():
    global tokens, history
    ## if data is encrypted - decrypt it There
    ## There
    # was
    # data = json.loads(request.data)
    data = request.json
    if 'token' in data.keys():
        uname = ''
        try:
            uname = tokens[data['token']]['uname']
        except KeyError:
            return Response('{"status": "fail", "code": "402", "desc": "no valid token presented"}', mimetype='application/json')
        # ok!
        #lbd = sorted(players, key=lambda k: k['ts'], reverse=True)
        token = data['token']
        tokens[token]['lastactivity'] = int(time.time())
        if tokens[token]['online'] == False:
            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            tokens[token]['online'] = True

        count = 0
        start = time.time()
        doResp = True
        while count == 0:
            end = time.time()
            if (end - start) > 22.0:
                break

            # Renew this func. When token is renewed, you need to get new tokens
            try:
                msg_list = [message for message in history if message['id'] > tokens[data['token']]['lastupdate']]
            except KeyError:
                return Response('{"status": "fail", "code": "502", "desc": "your token expired"}', mimetype='application/json')


            count = len(msg_list)
            time.sleep(0.5)

        _ts = -1
        if len(msg_list) > 0:
            _ts = msg_list[-1]['id']

        if _ts > -1:
            tokens[data['token']]['lastupdate'] = _ts

        response = json.dumps({'status': 'ok', 'total': len(msg_list), 'response': msg_list})
        return Response(response, mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "501", "desc": "forbidden, because you don\'t provided [key, token]"}', mimetype='application/json')


@app.route('/online', methods=['POST'])
def online_list():
    global tokens, history
    data = request.json
    if 'token' in data.keys():
        uname = ''
        try:
            uname = tokens[data['token']]['uname']
        except KeyError:
            return Response('{"status": "fail", "code": "402", "desc": "no valid token presented"}', mimetype='application/json')
        # ok!
        #lbd = sorted(players, key=lambda k: k['ts'], reverse=True)
        token = data['token']
        tokens[token]['lastactivity'] = int(time.time())
        if tokens[token]['online'] == False:
            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            tokens[token]['online'] = True

        fri_list = [{"uname": user['uname'], "online": user['online']} for user in [tokens[token] for token in tokens.keys() if not token == data['token']]]
        fri_list = sorted(fri_list, key=lambda k: k['online'], reverse=True)

        response = json.dumps({'status': 'ok', 'total': len(fri_list),'response': fri_list})
        return Response(response, mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "501", "desc": "forbidden, because you don\'t provided [token]"}', mimetype='application/json')



@app.route('/messages')
def msglist():
    return Response(json.dumps(history), mimetype='application/json')

@app.route('/tokens')
def toklist():
    return Response(json.dumps(tokens), mimetype='application/json')

boxes = {}



myscr = curses.initscr()
curses.noecho()
win_h, win_w = myscr.getmaxyx()
curses.curs_set(0)

'''
###########################
# |----|  |-----|
# |door|  |lock |
# |----|  |-----|
#
# |----|  |-----|
# |ligt|  |winds|
# |----|  |-----|
###########################

'''
boxes['door_box'] = curses.newwin(25, 50, 1, 2)
boxes['lock_box'] = curses.newwin(25, 50, 1, 54)
boxes['light_box'] = curses.newwin(31, 50, 27, 2)
boxes['heat_box'] = curses.newwin(25, 50, 27, 54)

def renewMainBox():
    myscr.clear()
    myscr.border(0)
    myscr.addstr(0, win_w//2 - len(motd)//2, ' %s ' % motd)
    myscr.addstr(win_h-2, 3, "Security Module by TNN//null community.")

renewMainBox()
myscr.refresh()

def renewLockBox(box=None):
    global boxes, params
    if box is None:
        box = boxes['lock_box']
    box_h, box_w = box.getmaxyx()
    box.clear()
    box.border(0)
    box.addstr(0, 3," Main lock ")
    line = 0
    if params['lock'] == 'locked':
        for s in icons.lock_locked.split('\n'):
            line += 1
            box.addstr(line, 1, s)
    else:
        for s in icons.lock_unlocked.split('\n'):
            line += 1
            box.addstr(line, 1, s)
    for s in icons.lock_bottom.split('\n'):
        line += 1
        box.addstr(line, 1, s)

    box.refresh()

def renewDoorBox(box=None):
    global boxes, params
    if box is None:
        box = boxes['door_box']
    box_h, box_w = box.getmaxyx()
    box.clear()
    box.border(0)
    box.addstr(0, 3," Door Lock ")
    line = 0
    if params['door'] == 'locked':
        for s in icons.lock_locked.split('\n'):
            line += 1
            box.addstr(line, 1, s)
    else:
        for s in icons.lock_unlocked.split('\n'):
            line += 1
            box.addstr(line, 1, s)


    for s in icons.lock_bottom.split('\n'):
        line += 1
        box.addstr(line, 1, s)

    box.refresh()


def renewLightBox(box=None):
    global boxes, params
    if box is None:
        box = boxes['light_box']
    box_h, box_w = box.getmaxyx()
    box.clear()
    box.border(0)
    box.addstr(0, 3," Lights ")
    line = 0
    if params['light'] == 'on':
        for s in icons.light_on.split('\n'):
            line += 1
            box.addstr(line, 1, s)
    else:
        for s in icons.light_off.split('\n'):
            line += 1
            box.addstr(line, 1, s)

    box.refresh()

def renewHeatBox(box=None):
    global boxes, params
    if box is None:
        box = boxes['heat_box']
    box_h, box_w = box.getmaxyx()
    box.clear()
    box.border(0)
    box.addstr(0, 3," Air ")
    line = 0
    if params['air'] == 'heat':
        for s in icons.heat.split('\n'):
            line += 1
            box.addstr(line, 1, s)
    elif params['air'] == 'cool':
        for s in icons.cool.split('\n'):
            line += 1
            box.addstr(line, 1, s)
    else:
        for _ in range(23):
            line += 1
            box.addstr(line, 1, ''.join(['.' for _ in range(48)]))
    box.refresh()



def gupd():
    global tokens, history
    renewLockBox()
    renewHeatBox()
    renewDoorBox()
    renewLightBox()
    '''
    while True:
        renewLockBox()
        renewDoorBox()
        renewLightBox()
        renewHeatBox()
        time.sleep(1)
    '''


if __name__ == '__main__':

    _thread.start_new_thread(gupd, ())
    app.run('0.0.0.0', port=12500, debug=False, threaded=True)
