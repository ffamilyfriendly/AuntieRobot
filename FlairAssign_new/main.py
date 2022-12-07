import json
import praw
import os
import math
import curses
from curses.textpad import Textbox, rectangle
from enum import Enum
import copy

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
    rv = { }

    y = rollcalls[ str(year) ]
    index = 0

    for i in y["posts"]:
        index += 1
        rollcall = client.submission(i)
        rollcall.comments.replace_more(limit=None)
        comments = rollcall.comments.list()

        print("Day {}: {} comments!".format(index, len(comments)))

        for comment in comments:
            if hasattr(comment.author, "lower") and comment.author.lower() == "auntierob":
                print(comment)


    return rv

def checkYear(year):
    setStatusString(year, status.INFO)

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

            if(cmd["parameters"]):
                parameters = cmd["parameters"]

            cmd["run"](*parameters)
        else:
            setStatusString("command \"{}\" has no callable function".format(cmd["title"]), status.ERROR)
    
    menuSystem( menuItems )


def main():

    setStatusString("Logging in...", status.INFO)

    setStatusString("Logged in as {}!".format(client.user.me()), status.OK)

    
    def checkFlairList():
        rv = [ ]
        for i in rollcalls:
            rv.append( { "title": "check {} ({} rollcalls)".format(i, len(rollcalls[i]["posts"])), "run": checkYear, "parameters": [ i ] } )
        return rv

    menuSystem( [ 
        [ "Check Flairs", checkFlairList() ],
        [ "Flair Actions", [ { "title": "Apply Flairs", "run": "" }, { "title": "Check User", "run": "" } ] ],
        [ "Database Actions", [ { "title": "Clear Database", "run": "" } ] ]
     ] )
    #getYear(2022)

main()