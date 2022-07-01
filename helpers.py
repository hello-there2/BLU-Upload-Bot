# Helper functions

# Imports
from sys import platform
import os


def is_windows():
    return platform == "Windows" or platform in ["win32", "win64"]


def cls():
    if is_windows():
        os.system("cls")
    else:
        os.system("clear")


def check_string_boolean(string):
    string = string.lower()
    return string in ["1", "y", "yes", "t", "true"]


def TrueXor(*args):
    return sum(bool(x) for x in args) == 1
