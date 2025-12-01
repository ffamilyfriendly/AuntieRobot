from shared import commands


def run(*args):
    for cmd_name, cmd in commands.items():
        print(f"{cmd_name}: {cmd['help']()}")


def help():
    return "the command you are using"
