"""Helper functions"""

import json
import sys


def read_config(filename):
    try:
        with open(filename) as f:
            config = json.load(f)
    except ValueError as e:
        print("Parse Error (file: \'%s\'): %s".format(filename, e))
        sys.exit()
    except IOError as e:
        print("Error reading configuration: %s".format(e))
        sys.exit()

    return config
