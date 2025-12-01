import json
import importlib
import os

rollcalls = json.load(open("./rollcalls.json"))

# Dynamically load all commands from the `commands` directory
commands = {}

# Load all Python files in the `commands` directory
for filename in os.listdir("./commands"):
    if filename.endswith(".py") and not filename.startswith("_"):
        module_name = filename[:-3]  # Remove `.py`
        module = importlib.import_module(f"commands.{module_name}")
        commands[module_name] = {
            "run": module.run,
            "help": module.help
        }
