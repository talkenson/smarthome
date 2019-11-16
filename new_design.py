import time, json, random, curses, os
import requests as req
import curses
import _thread
import atexit
import pickle
import RSA
import win10toast
from playsound import playsound


toaster = win10toast.ToastNotifier()

pref = {
'server': 'localhost:12500',
'key': 'DEF',
'uname': 'DEF',
'ts': '-1',
'token': 'DEF'
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
#print(letters)

_mode = 'textTyping'

_selFCell = 0
_selDialog = 'Main Chat'
## Modes are 1_ textTyping 2_ friendSelect

__exit = False

history = {}
friends = []

boxes = {

}





def saveAll():
    with open('messages.pickle', 'wb') as f:
        pickle.dump(history, f)

atexit.register(saveAll)

def loadAll():
    global history
    if os.path.exists('messages.pickle'):
        with open('messages.pickle', 'rb') as f:
            history = pickle.load(f)

loadAll()

def rememberMessage(id, uname, message, dialog=''):
    global history
    cid = '%s:%s/%s' % (pref['server'], pref['uname'], dialog)
    '''
    toaster.show_toast("Debug",
        "Saving to %s" % cid,
        icon_path=None, duration=5, threaded=True)
    '''
    history[cid].append({"id": id, "message": message, "uname": uname})

def rememberFriendState(uname, online):
    global friends
    friends.append({"uname": uname, "online": online})

curs_y, curs_x = 0, 0

os.system('cls')
print('\t\tPyChat Client\
\n\tPlease, stretch your screen size to set this dots on side of terminal\
\n\t(125 x 30, width and height)\
\n\tBefore you tap Enter after typing server-address')
print(''.join([' ' for _ in range(124)]) + '#\n\n\n')

uname = input('\tPlease, state your nickname below:\n\t -> ')
pref['uname'] = uname
key = input('\tPlease, type a random [A-Za-z0-9] key below:\n\t -> ')
pref['key'] = key
server = input('\tPlease, enter server address below (now = %s) (Hit Enter to save):\n\t -> ' % pref['server'])
if not server == "":
    pref['server'] = server

print("\n\tTrying to connect to server...")

motd = ''
r = req.get('http://%s/reg/%s:%s' % (pref['server'], pref['uname'], pref['key'])).json()
if r['status'] == "ok":
    pref['token'] = r['response']['token']
    motd = r['response']['motd'].strip()
    print("\tSuccessfully connected!")
elif r['status'] == "fail":
    print("\t#%s - %s" % (r['code'], r['desc']))
    exit(0)


creds = {'key': pref['key'], 'token': pref['token']}

print("\tSecret key generation...")

# Generating key
try:
    #__key = RSA.get_key(2**1024, 2**1025 - 1, 50, 2**512, 2**1024)
    print("\tKey generated, searching for online")
except BaseException:
    print("\tError in key generation")

'''
try:
    r = req.post('http://%s/online' % pref['server'], json=creds, timeout=15).json()
except req.exceptions.RequestException:
    time.sleep(5)
    continue


if r['total'] > 0:
    pass
    ## There's something online

'''



myscr = curses.initscr()
curses.noecho()
win_h, win_w = myscr.getmaxyx()
curses.curs_set(0)

boxes['fri_box'] = curses.newwin(win_h - 3, 16, 1, win_w - 18)
boxes['text_box'] = curses.newwin(3, win_w - 21, win_h - 5, 2)
boxes['msg_box'] = curses.newwin(win_h - 6, win_w - 21, 1, 2)


def notif_message():
    try:
        playsound('sounds/notif_message.mp3')
    except BaseException:
        pass

def notif_new_joined():
    try:
        playsound('sounds/notif_new_joined.wav')
    except BaseException:
        pass

def renewMainBox():
    myscr.clear()
    myscr.border(0)
    myscr.addstr(0, win_w//2 - len(motd)//2, ' %s ' % motd)
    myscr.addstr(win_h-2, 3,":q QUIT\t:h HELP\t:f DILG\t:t TTMD")

renewMainBox()
#notif_new_joined()
myscr.refresh()

def renewMessageBox(box):
    global history, _selDialog
    box_h, box_w = box.getmaxyx()
    box.clear()
    box.border(0)

    dianame = _selDialog
    if dianame == '':
        dianame = 'Main Chat'
    box.addstr(0, 3,' %s\'s message history ' % dianame)

    if dianame == 'Main Chat':
        dianame = ''

    cid = '%s:%s/%s' % (pref['server'], pref['uname'], dianame)
    if not cid in history.keys():
        history[cid] = []
    '''
    toaster.show_toast("Debug",
        "Loading from %s" % (cid),
        icon_path=None, duration=5, threaded=True)
    '''


    #########
    max_m = box_h-2
    msgs = history[cid][-max_m:]
    #box.addstr(box_h-1, box_w - 12,' (%s;%s) ' % (curs_y, curs_x))
    for count, msg in enumerate(msgs):
        if len(msg['message']) > box_w - 14:
            l_msg = msg['message'][:box_w - 17] + '...'
        else:
            l_msg = msg['message'][:box_w - 14]
        uname = msg['uname'].ljust(10, ' ')
        box.addstr(1 + count, 1,'%s: %s' % (uname, l_msg))
    ##########
    #box.refresh()

def renewTextBox(box):
    box_h, box_w = box.getmaxyx()
    box.clear()
    box.border(0)
    box.addstr(0, 3," Type your message ")
    box.addstr(0, box_w-12," (Enter) ")
    box.addstr(1, 2,">")
    #box.refresh()

def renewFriendBox(box):
    global _selFCell

    box_h, box_w = box.getmaxyx()
    box.clear()
    box.border(0)
    box.addstr(0,3,' Dialogs ')
    max_f = box_h-2
    if _selFCell >= min(max_f, len(friends)-1):
        _selFCell = min(max_f, len(friends)-1)
    if _selFCell < 0:
        _selFCell = 0

    frnds = friends[:max_f]
    for count, frn in enumerate(frnds):
        status = '•' if frn['online'] else 'X'
        if count == _selFCell and _mode == 'friendSelect':
            status = '>'
        if frn['uname'] == _selDialog:
            status += ' >'
        box.addstr(1 + count, 1,'%s %s' % (status, frn['uname']))

    #box.refresh()

def posUp(line, pos, inc):
    if pos + inc > line and (pos + inc) >= 0:
        return line
    elif pos + inc <= line and (pos + inc) >= 0:
        return (pos + inc)
    elif pos + inc <= line and (pos + inc) < 0:
        return 0

'''

toaster.show_toast("Debug",
    "%s" % (time.time() - ts),
    icon_path=None, duration=5, threaded=True)


'''

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

def textarea():
    global __exit, boxes, myscr, win_h, win_w, curses
    global _mode, _selFCell, _selDialog, friends
    text_box = boxes['text_box']
    text = ''
    pos = 0
    while True:
        text_box = boxes['text_box']
        text_box.keypad(True)
        th, tw = text_box.getmaxyx()
        renewTextBox(text_box) # prints text here
        text_box.addstr(1, 4,"%s|%s" % (text[:pos].lstrip('\n'), text[pos:].rstrip('\n')))
        text_box.refresh()
        ch = text_box.getch()
        #text_box.addstr(0, 25," %s " % int(ch))
        '''
        toaster.show_toast("Debug",
            "%s %s" % (_selFCell, _selDialog),
            icon_path=None, duration=3, threaded=True)
            '''
        if ch == ord('\n'):
            if _mode == 'textTyping':
                text = text.strip()
                if not text == '':
                    ndata = {}

                    dialog_uname = [friend for count, friend in enumerate(friends) if count == _selFCell][0]['uname']
                    if not dialog_uname == 'Main Chat':
                        ndata.update({'direct': dialog_uname})
                    mesg = encode(text)
                    ndata.update({'message': mesg})
                    ndata.update(creds)
                    m = req.post('http://%s/send' % pref['server'], json=ndata).json()
                    text = ''
                continue
            elif _mode == 'friendSelect':

                dialog_uname = [friend for count, friend in enumerate(friends) if count == _selFCell][0]['uname']
                if dialog_uname == 'Main Chat':
                    dialog_uname = ''
                _selDialog = dialog_uname

                renewMessageBox(boxes['msg_box'])
                renewFriendBox(boxes['fri_box'])
                boxes['fri_box'].refresh()
                boxes['msg_box'].refresh()

        elif ch == ord('\b') and pos > 0 and _mode == 'textTyping':
            text = text[:pos-1] + text[pos:]
            pos = posUp(len(text), pos, -1)
        elif ch == curses.KEY_DC and pos < len(text) and _mode == 'textTyping':
            text = text[:pos] + text[pos+1:]
        elif ch == curses.KEY_HOME and _mode == 'textTyping':
            pos = 0
        elif ch == curses.KEY_END and _mode == 'textTyping':
            pos = len(text)
        elif ch == curses.KEY_LEFT and _mode == 'textTyping': # 75
            pos = posUp(len(text), pos, -1)
            continue
        elif ch == curses.KEY_RIGHT and _mode == 'textTyping': # 77
            pos = posUp(len(text), pos, 1)
            continue
        elif ch == curses.KEY_UP:
            if _mode == 'friendSelect':
                _selFCell -= 1
                renewFriendBox(boxes['fri_box'])
                continue
        elif ch == curses.KEY_DOWN:
            if _mode == 'friendSelect':
                _selFCell += 1
                renewFriendBox(boxes['fri_box'])
                continue
        elif ch == ord('\r') or ch == ord('\n'):
            text = text[:-1]
            continue
        elif ch == curses.KEY_RESIZE:
            myscr = curses.initscr()
            myscr.clear()
            curses.curs_set(0)

            win_h, win_w = myscr.getmaxyx()

            boxes['fri_box'] = curses.newwin(win_h - 3, 16, 1, win_w - 18)
            boxes['text_box'] = curses.newwin(3, win_w - 21, win_h - 5, 2)
            boxes['msg_box'] = curses.newwin(win_h - 6, win_w - 21, 1, 2)
            renewTextBox(boxes['text_box'])
            renewMessageBox(boxes['msg_box'])
            renewFriendBox(boxes['fri_box'])

            renewMainBox()
            myscr.refresh()


            for box in [boxes[bname] for bname in boxes.keys()]:
                box.refresh()

        elif ch == ord(':'):
            act = text_box.getch()
            if act == ord('q'):
                myscr.clear()
                curses.endwin()
                print('\n Goodbye!')
                __exit = True
                time.sleep(2)
            elif act == ord('f'):
                _mode = 'friendSelect'
                renewFriendBox(boxes['fri_box'])
                boxes['fri_box'].refresh()
            elif act == ord('t'):
                _mode = 'textTyping'
            elif act == ord('h'):
                help_box = curses.newwin(win_h - 6, win_w - 21, 1, 2)
                help_box.border(0)
                help_box.addstr(0, 3," Help ")
                help_box.addstr(2, 2," :f - To Select Dialog (Use arrows to switch up and down)")
                help_box.addstr(3, 2," :t - To Return to Text Typing Mode after Dialog Selection")
                help_box.addstr(5, 2," :h - To Get Help")
                help_box.addstr(6, 2," :q - To Quit")
                help_box.addstr(win_h - 11, 2,"(To Exit this window you need to type :t)")
                help_box.addstr(win_h - 9, 2,"\tCREATORS:\tVitaly Shatalov (vetka921), Anton Kazancev (toxakaz)")
                help_box.refresh()
                text_box.getch()
                myscr.refresh()
            elif chr(act) in letters and len(text) < tw-8:
                text = text[:pos] + ':' + chr(act) + text[pos:]
                pos += 2
            continue
        else:
            if chr(ch) in letters and len(text) < tw-7 and _mode == 'textTyping':
                text = text[:pos] + chr(ch) + text[pos:]
                pos += 1


def online():
    global curses, friends, _mode

    fri_box = boxes['fri_box']
    renewFriendBox(fri_box)
    timestamp = int(time.time())
    fri_box.addstr(2,2,'Loading...')
    fri_box.refresh()
    while True:
        fri_box = boxes['fri_box']
        #if not _mode == 'friendSelect':
        #    time.sleep(1)
        #h, w = fri_box.getmaxyx()
        renewFriendBox(boxes['fri_box'])
        if (time.time() - timestamp) >= 3:
            timestamp = int(time.time())
            try:
                r = req.post('http://%s/online' % pref['server'], json=creds, timeout=25).json()
            except req.exceptions.RequestException:
                continue

            if not r['status'] == 'ok':
                fri_box.addstr(2,2,'Not Valid')
                fri_box.refresh()
                break

            if r['total'] > 0:
                friends = []
                rememberFriendState('Main Chat', True)
                for fr in r['response']:
                    rememberFriendState(fr['uname'],fr['online'])
                renewFriendBox(fri_box)
        boxes['fri_box'].refresh()





def gupd():
    global curses, history
    msg_box = boxes['msg_box']
    while True:
        try:
            r = req.post('http://%s/updates' % pref['server'], json=creds, timeout=25).json()
        except req.exceptions.RequestException:
            continue

        msg_box = boxes['msg_box']
        h, w = boxes['msg_box'].getmaxyx()
        renewMessageBox(boxes['msg_box'])
        boxes['msg_box'].refresh()

        if not r['status'] == 'ok':
            #cid = '%s:%s/%s' % (pref['server'], pref['uname'], _selDialog)
            #del history[cid]
            rememberMessage(1,'[CLIENT]', 'There\'s an error occured:','')
            rememberMessage(2,'[CLIENT]', '#%s - %s' % (r['code'], r['desc']),'')
            renewMessageBox(msg_box)
            msg_box.refresh()
            break

        if r['total'] > 0:
            for msg in r['response']:
                if 'direct' in msg.keys():
                    if (msg['direct'] == uname or msg['uname'] == uname):
                        if msg['direct'] == uname:
                            to_addr = msg['uname']
                            notif_message()
                        else:
                            to_addr = msg['direct']
                        cid = '%s:%s/%s' % (pref['server'], pref['uname'], to_addr)
                        if not cid in history.keys():
                            history[cid] = []
                        rememberMessage(msg['id'], msg['uname'], msg['message'], to_addr)

                        '''
                        toaster.show_toast("Получено личное сообщение",
                            "От %s: %s" % (msg['uname'],msg['message']),
                            icon_path=None, duration=5, threaded=True)
                        '''
                    else:
                        ## ignore, that's not our message
                        pass
                else:
                    cid = '%s:%s/%s' % (pref['server'], pref['uname'], '')
                    if not cid in history.keys():
                        history[cid] = []
                    rememberMessage(msg['id'], msg['uname'], msg['message'], '')
                    if ('@' + uname) in msg['message']:
                        toaster.show_toast("Упоминание в PyChat",
                            "%s: %s" % (msg['uname'],msg['message']),
                            icon_path=None, duration=5, threaded=True)
            renewMessageBox(msg_box)
            msg_box.refresh()
        #time.sleep(0.1)


if __name__ == '__main__':
    _thread.start_new_thread(gupd, ())
    _thread.start_new_thread(textarea, ())
    _thread.start_new_thread(online, ())
    while __exit == False:
        pass
    _thread.exit()
