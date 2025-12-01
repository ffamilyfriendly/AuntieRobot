from db import insert_year
from shared import rollcalls


def run(args):
    year = args[0]
    if not year:
        print("You must select a year")
        return

    if not year in rollcalls:
        print("no such year exists")
        return

    for idx, v in enumerate(rollcalls[year]["posts"]):
        print(f"{idx}: {v}")


def help():
    return "get rollcalls from year. get_rollcalls <year>"
