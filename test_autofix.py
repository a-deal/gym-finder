#!/usr/bin/env python3


unused_var = "this will be removed"

# This file has various issues that should be auto-fixed:
# - Unused imports (json, time)
# - Unused variable (unused_var)
# - Old-style string formatting
# - Trailing whitespace
# - Missing final newline


def test_function():
    name = "test"
    # Old Python syntax that can be upgraded
    result = "Hello %s" % name
    return result


if __name__ == "__main__":
    test_function()
