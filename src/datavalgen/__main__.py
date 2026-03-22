"""
A very simple dispatcher for the datavalgen CLI.
"""

import os
import sys

from datavalgen.cli.generate import main as generate_main
from datavalgen.cli.validate import main as validate_main
from run_context import dispatch


def main():
    # If a run context file is available, we use that. Keeping in mind that
    # only a small (privacy-preserving) subset of the methods are offered when
    # run that way. This is intentional as for us RUN_CONTEXT means we are
    # being run in a FL platform/node
    if os.environ.get("RUN_CONTEXT_FILE"):
        try:
            dispatch()
        except (ValueError, RuntimeError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)

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
