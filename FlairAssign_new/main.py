import json
import praw
import os
import math
import time
import curses
import sqlite3
import re
from curses.textpad import Textbox
from praw.models import MoreComments, Comment
import webbrowser

#   I suck at python but praw is better documented/maintained than snoowrap
#   so i guess i better learn python lol

dbCon = sqlite3.connect("data.db")

def ensureTables():
    cur = dbCon.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS posts(year, post, user, content, flag)")
    cur.execute("CREATE TABLE IF NOT EXISTS users(user PRIMARY KEY, old_flair, new_flair)")

def postChecked(post):
    cur = dbCon.cursor()
    res = cur.execute("SELECT post FROM posts WHERE post=?", (post,))
    return not ( res.fetchone() is None )

def insertUser(user, old_flair, new_flair):
    cur = dbCon.cursor()
    res = cur.execute("INSERT INTO users VALUES(?,?,?)", ( user, old_flair, new_flair ))
    dbCon.commit()

def getUser(user):
    cur = dbCon.cursor()
    res = cur.execute("SELECT * FROM users WHERE user = ?", ( user, ))
    return res.fetchone()

def getUsers(post_id):
    cur = dbCon.cursor()
    res = cur.execute("SELECT DISTINCT user FROM posts WHERE post=?", (post_id,))
    return res.fetchall()

def getUserPosts(username):
    cur = dbCon.cursor()
    res = cur.execute("SELECT * FROM posts WHERE user=?", (username, ))
    return res.fetchall()

def clearDatabase():
    cur = dbCon.cursor()
    cur.execute("DELETE FROM posts")
    dbCon.commit()

def handleComments(year, postid, comments):
    cur = dbCon.cursor()
    data = []

    for comment in comments:
        if isinstance(comment, Comment) and comment.author is not None:
            still_in_matches = ["still in", "reporting", "present", "here"]
            out_matches = [ "im out", "i lost" ]

            regex = re.compile('[^a-zA-Z ]')

            comment_body = regex.sub('', comment.body.lower())

            still_in = any([ x in comment_body for x in still_in_matches ])
            now_out = any([ x in comment_body for x in out_matches ])

            flag = 0 # default
            if still_in:
                flag = 1 # user is in :)
            if now_out:
                flag = 2 # user is out :(
            if still_in and now_out:
                flag = 3 # user is both??
            
            # flag 3 and 0 means something aint right

            data.append( ( year, postid, comment.author.name, comment_body[:300], flag ) )
        else:
            continue

    cur.executemany("INSERT INTO posts VALUES(?,?,?,?,?)", data)
    dbCon.commit()

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

def applyFlair( user: str, flair: str ):
    if not flair or not user:
        return False
    if getUser(user):
        return "already handled"
    
    currFlair = client.subreddit("nonutnovember").flair(redditor=user)
    oldFlair = ""
    for _flair in currFlair:
        oldFlair = _flair["flair_text"]
    
    # Try to check "worth" of old flair and compare to new
    # We dont want to give trebble by mistake to a fourfold
    # if worth of new flair is less than old flair try sending a dm to user explaining

    client.subreddit("nonutnovember").flair.set(user, text=flair)
    insertUser(user, oldFlair, flair)
    return True
    


# this is arguably the worst code i've ever written
def constructFlair( years: dict ):
    l = len(years)

    keys = list(years.keys())

    if l == 0:
        return None
    if l == 1:
        return "DiamondNoNutter {} :diamondnut18:".format(keys[0])
    if l == 2:
        return "DiamondNoNutter {} and {} :diamondnut18:".format(keys[0], keys[1])
    if l == 3:
        return "Diamond Treble :diamondnut18::diamondnut18::diamondnut18:"
    if l == 4:
        return "Diamond Fourfold :d::d::d::d:"

def checkUser( username ):
    # year, post, user, content, flag
    posts = getUserPosts(username)

    def takeYear(elem):
        return int(elem[0])
    posts.sort(key=takeYear)
    years = { }


    for row in posts:
        year = row[0]
        post_flag = row[4]
        if not years.get(year):
            years[year] = { "timesIn": 0, "timesOut": 0, "timesWeird": 0, "answeredLastPost": False }
        
        yr_rollcalls = rollcalls[year]

        if row[1] == yr_rollcalls["posts"][-1]:
            years[year]["answeredLastPost"] = True


        match post_flag:
            case 1:
                years[year]["timesIn"] = years[year]["timesIn"] + 1
            case 2:
                years[year]["timesOut"] = years[year]["timesOut"] + 1
            case _:
                years[year]["timesWeird"] = years[year]["timesWeird"] + 1

    years_flairs = { }

    for year, res in years.items():
        yr_rollcalls = rollcalls[year]

        if (res["timesIn"] + res["timesWeird"]) < yr_rollcalls["required"]:
            continue; # less than required = bonk. We also only check results that are weird or indicated as still in
    
        if res["timesOut"] != 0 and not res["answeredLastPost"]:
            continue; # if indicated out and did not answer last post, bonk
    
        if res["timesOut"] > 3:
            continue; # user indicated out 3 times. The reason this is not at 1 is that I dont trust my very simple labler

        years_flairs[year] = True

    print(years)
    print(years_flairs)
    print(constructFlair(years_flairs))
    return constructFlair(years_flairs)

def checkPost( year, post_id ):
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
        time.sleep(0.3)
        postProgress("Loading comments of {}".format(post_id), len(rawComments), post.num_comments)
        contents = filter(more.comments())
        rawComments.extend(contents[0])
        moreComments.extend(contents[1])
        loadAll()
    loadAll()
    
    handleComments(year, post_id, rawComments)


        

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
            dayArr.append( { "title": "{}day {}".format("✓ " if postChecked(rollcalls[year]["posts"][day]) else "✗ ",day + 1), "type": EmbedInputTypes.TOGGLE } )
        return dayArr


    answer = embed("{}: {} rollcalls".format(year, len(rollcalls[year]["posts"])), getDays())
    
    posts = []

    for key, value in answer.items():
        if not value:
            continue
        day = int("".join(i for i in key if i in "0123456789")) - 1
        posts.append(rollcalls[year]["posts"][day])

    if len(posts) >= 1:
        for post in posts:
            checkPost(year, post)
    else:
        setStatusString("no post(s) selected", status.ERROR)

def applyAllFlairs():
    users = getUsers(rollcalls["2022"]["posts"][-1])
    setStatusString("got {} users".format(len(users)), status.OK)
    # code here. 

def main():
    ensureTables()

    setStatusString("Logging in...", status.INFO)
    #setStatusString("Logged in as {}!".format(client.user.me()), status.OK)

    def deleteDataAction():
        d = embed("Clear Database", 
            [
                { "value": "type \"CONFIRM\" to proceed", "type": EmbedInputTypes.LABLE },
                { "title": "answer", "type": EmbedInputTypes.TEXTINPUT }
            ]
        )

        if d["answer"] and d["answer"] == "CONFIRM":
            clearDatabase()
            setStatusString("Database cleared.", status.OK)
        else:
            setStatusString("Action aborted.", status.INFO)
        
        

    
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
        res = getUserPosts(user)
        if not res:
            return setStatusString("No info found for user u/{}".format(user), status.ERROR)
        else:
            yearList = {}
            embedItems = []
            for row in res:
                print(row)
                aids = yearList.get(row[0])
                if aids:
                    yearList[row[0]] = aids + 1
                else:
                    yearList[row[0]] = 1

            for year, posts in yearList.items():
                embedItems.append( { "value": "{}: {} posts".format(year, posts), "type": EmbedInputTypes.LABLE } )
                
            embed("u/{}".format(user), embedItems)
            flair_s = checkUser(user)
            if flair_s:
                setStatusString("Giving {} {}".format(user, flair_s), status.INFO)
                applyFlair(user, flair_s)

    def fetchRollcalls():
        setStatusString("searching...", status.INFO)
        res = client.subreddit("nonutnovember").search(query="flair:Official+Roll-Call", time_filter="all")
        f = open("rollcalls.csv", "w")
        for post in res:
            if not post:
                continue;
            f.write("{},{},{}\n".format(post.created_utc, post.name, post.id, post.permalink, post.author.name if post.author is not None else "u/deleted"))
        f.close()


        

    menuSystem( [ 
        [ "Check Flairs", checkFlairList() ],
        [ "Flair Actions", [ { "title": "Apply Flairs", "run": applyAllFlairs }, { "title": "Check User", "run": test } ] ],
        [ "Misc", [ { "title": "Clear Database", "run": deleteDataAction }, { "title": "View Source Code", "run": lambda: webbrowser.open("https://github.com/ffamilyfriendly/AuntieRobot/tree/main/FlairAssign_new") }, { "title": "fetch rollcalls", "run": fetchRollcalls } ] ]
     ] )
    #getYear(2022)

main()