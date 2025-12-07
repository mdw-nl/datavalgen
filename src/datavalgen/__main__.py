"""
A very simple dispatcher for the datavalgen CLI.
"""

import sys

from datavalgen.cli.generate import main as generate_main
from datavalgen.cli.validate import main as validate_main


def main():
    if len(sys.argv) < 2:
        print("Available commands: validate, generate")
        sys.exit(1)

    cmd, *args = sys.argv[1:]

    if cmd == "validate":
        validate_main(args)
    elif cmd == "generate":
        generate_main(args)
    else:
        print("Available sub-commands: validate, generate")
        sys.exit(1)


if __name__ == "__main__":
    main()
