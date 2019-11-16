import curses, time

cons = curses.initscr()
cons.keypad(True)
cons.border(0)
cons.refresh()
c = cons.getkey()
while True:
    if cons.getch() == curses.KEY_RESIZE:
        cons = curses.initscr()
        cons.clear()
        cons.border(0)
        cons.refresh()

time.sleep(1000)

