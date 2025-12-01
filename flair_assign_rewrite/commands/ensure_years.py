from db import insert_year
from shared import rollcalls


def run(*args):
    print("Ensuring years:")
    for property in rollcalls.keys():
        required_replies = rollcalls[property]["required"]
        print(property, ":", required_replies, "replies required")
        insert_year(property, required_replies)


def help():
    return "Ensure all years are added into database"
