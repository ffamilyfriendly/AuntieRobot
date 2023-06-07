import json
import praw
import os
import math
import time
import curses
from curses.textpad import Textbox
from praw.models import MoreComments, Comment
import webbrowser

#   I suck at python but praw is better documented/maintained than snoowrap
#   so i guess i better learn python lol

config = json.load(open("./FlairAssign_new/config.json"))
rollcalls = json.load(open("./FlairAssign_new/rollcalls.json"))
stdscr = curses.initscr()
stdscr.keypad(True)
statusString = "Loading AuntieRobot..."


client = praw.Reddit(
        client_id= config["clientID"],
        client_secret= config["clientSecret"],
        password= config["password"],
        username= config["username"],
        user_agent= "AuntieRobot (AutoFlair)"
    )



# Misc curses inits
curses.curs_set(0)
curses.noecho()
curses.cbreak()

# Init colours
if curses.has_colors():
    curses.start_color()

curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_GREEN)
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)
curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)
curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)
curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)

class _status:
    OK = 1
    INFO = 2
    ERROR = 3
    WARNING = 4,
    TITLE = 5,
    SELECTED = 6
status = _status()

#def progBar(value: int, min: int = 0, max: int = 100, display: str = "#"):

class _EmbedInputTypes:
    TEXTINPUT = 1
    TOGGLE = 2
    LABLE = 3
    SLIDER = 4
EmbedInputTypes = _EmbedInputTypes()

def postProgress(title: str = "title", prog: int = 0, tot: int = 1):
    win = curses.newwin(int(curses.LINES / 4), int(curses.COLS / 2), 3, int(curses.COLS / 4))
    HEIGHT = int(curses.LINES / 4)
    WIDTH = int(curses.COLS / 2)

    def draw():
        win.clear()
        

        percent = prog / tot
        charAmount = math.ceil((percent * WIDTH))
        disp = "{}>{}".format("=" * (charAmount - 1), " " * (WIDTH - charAmount))

        win.addstr(HEIGHT - 4, 1, "{}/{} ({}%)".format(prog, tot, round(percent * 100, 1)), curses.color_pair(status.INFO))
        win.addstr(HEIGHT - 2, 0, disp, curses.color_pair(status.SELECTED))
        win.border()
        win.addstr(0, 2, title, curses.color_pair(status.SELECTED))
        win.refresh()
    draw()

def embed(title: str = "embed", elements = []):
    win = curses.newwin(int(curses.LINES / 2), int(curses.COLS / 2), int(curses.LINES / 4), int(curses.COLS / 4) )
    win.keypad(True)
    HEIGHT = int(curses.LINES / 2)
    WIDTH = int(curses.COLS / 2)

    cursor = 0
    val = { }

    inputMode = True

    def draw():
        KEYBINDS = "^x: exit | ↑ prev item | ↓ next item"
        win.clear()
        win.border()
        win.addstr(HEIGHT - 2, WIDTH - (len(KEYBINDS) + 2), KEYBINDS)
        win.addstr(0, 2, title, curses.color_pair(status.SELECTED))

        MAXHEIGHT = HEIGHT - 2

        MAXITEMS = math.floor(MAXHEIGHT/2) - 1

        for index, element in enumerate(elements):

            if cursor > MAXITEMS:
                if index > cursor or index < cursor - MAXITEMS:
                    continue

                offset =  cursor - index
                h = 1 + ((MAXITEMS - offset) * 2) 
            else:
                h = 1 + (index * 2)

            if h > MAXHEIGHT or h < 0:
                continue

            eType = element["type"]
            selected = index == cursor
            style = curses.color_pair(status.SELECTED) if selected else curses.A_BOLD

            if eType == EmbedInputTypes.LABLE:
                win.addstr(h, 1, element["value"] if "value" in element else "<text>", style)
            elif eType == EmbedInputTypes.TEXTINPUT:
                win.addstr(h, 1, "{}:".format(element["title"]), style)
                win.addstr(" " + val[element["title"]] if element["title"] in val else "")
            elif eType == EmbedInputTypes.TOGGLE:
                toggled = element["value"] if "value" in element else (val[element["title"]] if element["title"] in val else False)
                win.addstr(h, 1, "{}:".format(element["title"]), style)
                win.addstr(" ")
                win.addstr(" True " if toggled else " False ", curses.color_pair(status.OK) if toggled else curses.color_pair(status.ERROR))
            elif eType == EmbedInputTypes.SLIDER:
                prog = float(element["value"] if "value" in element else (val[element["title"]] if element["title"] in val else 0.0))
                win.addstr(h, 1, "{}:".format(element["title"]), style)
                win.addstr(" ")
                win.addstr("[{}{}]".format("#"*math.floor(prog*2), " "*math.floor(20-prog*2)), curses.A_BOLD)
                win.addstr(" {}%".format(prog * 10))

        win.refresh()


    draw()

    while inputMode:
        v = win.getch()

        if v == 259:
            cursor = max(0, cursor - 1)
        elif v == 258:
            cursor = min(cursor + 1, len(elements))
        elif v == 24:
            inputMode = False
        else:
            sElement = elements[cursor]

            if sElement["type"] == EmbedInputTypes.TEXTINPUT:
                if not sElement["title"] in val:
                    val[sElement["title"]] = ""

                if v == 8:
                    val[sElement["title"]] = val[sElement["title"]][:-1]
                elif v == 10:
                    val[sElement["title"]] += "\\n"
                else:
                    val[sElement["title"]] += chr(v)
            elif sElement["type"] == EmbedInputTypes.TOGGLE:
                if not sElement["title"] in val:
                    val[sElement["title"]] = sElement["val"] if "val" in sElement else False

                if v == 10:
                    val[sElement["title"]] = not val[sElement["title"]]
            elif sElement["type"] == EmbedInputTypes.SLIDER:
                if sElement["title"] not in val:
                    val[sElement["title"]] = sElement["val"] if "val" in sElement else 0.0
                # H: 261 V: 260
                value = val[sElement["title"]]
                if v == 261:
                    val[sElement["title"]] = min(value + 0.5, 10)
                elif v == 260:
                    val[sElement["title"]] = max(value - 0.5, 0)
                
                
        draw()
    
    win.erase()
    stdscr.clear()
    stdscr.refresh()

    return val


def center( text: str ):
    startingXPos = int ( (curses.COLS - len(text))/2 )
    return startingXPos

def pad( text: str ):
    return " {} ".format(text)

def setStatusString( statusText: str, statusType: status ):
    stdscr.clear()
    s = pad(statusText)
    stdscr.addstr(3, center(s), s, curses.color_pair(statusType))
    stdscr.refresh()


def getYear(year):

    def progBar():
        progbar = ""
        setStatusString(progBar, status.INFO)

    rv = { }

    y = rollcalls[ str(year) ]
    index = 0

    for i in y["posts"]:
        index += 1
        setStatusString("{}: Getting post for day {}...".format(year, index), status.INFO)
        rollcall = client.submission(i)
        setStatusString("{}: Post ({}) for day {} has {} comments. Fetching comments".format(year, i, index, rollcall.num_comments), status.OK)
        rollcall.comments.replace_more(limit=None)
        comments = rollcall.comments.list()

        for comment in comments:
            if hasattr(comment.author, "lower") and comment.author.lower() == "auntierob":
                print(comment)


    return rv

def checkYear(year):
    getYear(year)

commands = [ ]
selectedCommand = 0

def menuSystem( menuItems ):
    global commands
    global selectedCommand
    BASE = 4
    if len(commands) != 0:
        commands = []

    index = 0
    for i in menuItems:
        index += 2
        MainTitle = i[0]
        stdscr.addstr(BASE + index, center(MainTitle), MainTitle, curses.A_BOLD + curses.A_UNDERLINE + curses.color_pair(5))
        for y in i[1]:
            commands.append(y)
            index += 1
            title = pad(y["title"])
            if len(commands) == selectedCommand:
                stdscr.addstr(BASE + index, center(title), title, curses.A_BOLD + curses.color_pair(status.SELECTED))
            else:
                stdscr.addstr(BASE + index, center(title), title, curses.A_BOLD)
    
    stdscr.addstr(0, 0, "cmds: {} | selected: {}".format(len(commands), selectedCommand), curses.A_BOLD)

    stdscr.refresh()
    k = stdscr.getch()
    if k == 258:
        selectedCommand = min(len(commands), selectedCommand + 1)
        menuSystem( menuItems )
    if k == 259:
        selectedCommand = max(0, selectedCommand - 1)
        menuSystem( menuItems )
    if k == 10:
        cmd = commands[selectedCommand-1]
        if cmd is not None and callable(cmd["run"]):
            parameters = []

            if("parameters" in cmd):
                parameters = cmd["parameters"]

            cmd["run"](*parameters)
        else:
            setStatusString("command \"{}\" has no callable function".format(cmd["title"]), status.ERROR)
    
    menuSystem( menuItems )

def checkPost( post_id ):
    post = client.submission(id=post_id)

    c = post.comments

    def filter(l):
        raw_Comments = [a for a in l if not isinstance(a, MoreComments)]
        more_Comments = [a for a in l if isinstance(a, MoreComments)]
        return ( raw_Comments, more_Comments )

    r = filter(c)

    rawComments = r[0]
    moreComments = r[1]

    def loadAll():
        if len(moreComments) == 0:
            return
        more = moreComments.pop(0)
        if not more or not isinstance(more, MoreComments):
            return
        time.sleep(1)
        postProgress("Loading comments of {}".format(post_id), len(rawComments), post.num_comments)
        contents = filter(more.comments())
        rawComments.extend(contents[0])
        moreComments.extend(contents[1])
        loadAll()
    loadAll()
    
    f = open("./uc.txt", "w", encoding="utf-8")
    
    for comment in rawComments:
        if not isinstance(comment, Comment):
            print("NOT INSTANCE OF COMMENT")
            continue;
        else:
            if comment.author is not None:
                f.write("{}: {}\n".format(comment.author.name, comment.body[:20]))
    f.close()


        

    #i = 0
    #def checkForrest( forrest ):
    #    for comment in forrest:
    #        time.sleep(0.1)
    #        if isinstance(comment, MoreComments):
    #            checkForrest(comment.comments())
    #        else:
    #            postProgress("Checking {} ({})".format(post_id, post.num_comments), i, post.num_comments)
    #checkForrest(post.comments)

def yearSelectMode(year):
    # { "title": "day1", "type": EmbedInputTypes.TOGGLE }
    def getDays():
        dayArr = [ { "value": "Select what days you want to check\n (1 at a time recomended)", "type": EmbedInputTypes.LABLE } ]
        for day in range(len(rollcalls[year]["posts"])):
            dayArr.append( { "title": "day {}".format(day + 1), "type": EmbedInputTypes.TOGGLE } )
        return dayArr


    answer = embed("{}: {} rollcalls".format(year, len(rollcalls[year]["posts"])), getDays())
    
    posts = []

    for key, value in answer.items():
        if not value:
            continue
        day = int("".join(i for i in key if i in "0123456789")) - 1
        posts.append(rollcalls[year]["posts"][day])

    if len(posts) >= 1:
        checkPost(posts[0])
    else:
        setStatusString("no post(s) selected", status.ERROR)

def main():

    setStatusString("Logging in...", status.INFO)
    #setStatusString("Logged in as {}!".format(client.user.me()), status.OK)

    def testtwo():
        for i in range(0,100):
            postProgress("tet", i, 100)
            time.sleep(.5)
        
        

    
    def checkFlairList():
        rv = [ ]
        for i in rollcalls:
            rv.append( { "title": "check {} ({} rollcalls)".format(i, len(rollcalls[i]["posts"])), "run": yearSelectMode, "parameters": [ i ] } )
        return rv

    def test():
        d = embed("Check User",
            [ 
                { "value": "Select a user (u/ not needed)", "type": EmbedInputTypes.LABLE },
                { "title": "Username", "type": EmbedInputTypes.TEXTINPUT }
            ]
        )

        user = d["Username"] if "Username" in d else None

        if not user:
            setStatusString("No user selected.", status.ERROR)
            return
        setStatusString("Gathering data pertaining to u/{}".format(user), status.INFO)
        

    menuSystem( [ 
        [ "Check Flairs", checkFlairList() ],
        [ "Flair Actions", [ { "title": "Apply Flairs", "run": "" }, { "title": "Check User", "run": test } ] ],
        [ "Misc", [ { "title": "Clear Database", "run": testtwo }, { "title": "View Source Code", "run": lambda: webbrowser.open("https://github.com/ffamilyfriendly/AuntieRobot/tree/main/FlairAssign_new") } ] ]
     ] )
    #getYear(2022)

main()