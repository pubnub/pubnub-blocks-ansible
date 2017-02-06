#!/usr/bin/python
# coding: utf-8
from subprocess import Popen, PIPE
from collections import namedtuple
import sys

TextStyleStructure = namedtuple('TextStyleStructure', 'BOLD, UNDERLINE, END')
TextColorStructure = namedtuple('TextColorStruct', 'RED, GREEN, YELLOW, PURPLE, PINK, CYAN, GRAY, END')
TextColor = TextColorStructure(RED='\033[91m', GREEN='\033[92m', YELLOW='\033[93m', PURPLE='\033[94m',
                               PINK='\033[95m', CYAN='\033[96m', GRAY='\033[97m', END='\033[0m')
TextStyle = TextStyleStructure(BOLD='\033[1m', UNDERLINE='\033[4m', END='\033[0m')

# Retrieve version of Python on which script has been launched.
version = str(sys.version_info[0]) + "." + str(sys.version_info[1])


def run(command):
    """Run 'command' and wait for it's completion to get results.

    :type command:  str
    :param command: Reference on shell command which should be executed.
    """
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

    # Retrieve stdout and stderr content.
    data = process.communicate()
    if data[1]:
        print('{0}{1}{2}'.format(TextColor.RED, data[1], TextColor.END))
        exit(process.returncode)

    return data
