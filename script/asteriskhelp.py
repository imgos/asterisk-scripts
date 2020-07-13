"""Helper functions"""

import json
import sys


def read_config(filename):
    try:
        with open(filename) as f:
            config = json.load(f)
    except ValueError as e:
        print(f"Parse Error (file: '{filename}'): {e}")
        sys.exit()
    except IOError as e:
        print(f"Error reading configuration: {e}")
        sys.exit()

    return config
