import json
from shared import commands
rollcalls = json.load(open("./rollcalls.json"))


def main():
    do_run = True
    while do_run:
        user_input = input("cmd: ").strip().split()
        if not user_input:
            continue

        cmd = user_input[0]
        args = user_input[1:]

        if cmd not in commands:
            print(f"No such command '{cmd}'. Use 'help' for help")
            continue

        if cmd == "exit":
            do_run = False
            continue

        commands[cmd]["run"](args)


if __name__ == "__main__":
    main()
