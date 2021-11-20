from time import strftime, localtime
from objects import bcolors
from os import system

def getTimestamp():
	return strftime("%H:%M:%S", localtime())

def printHeader():
    system("clear")
    print(f'{bcolors.CYAN}')
    print(f' ██████   ██████   ██████  ███████                ██████  ███████ ██    ██')
    print(f'      ██ ██  ████ ██  ████      ██               ██    ██ ██      ██    ██')
    print(f'  █████  ██ ██ ██ ██ ██ ██     ██      █████     ██    ██ ███████ ██    ██')
    print(f' ██      ████  ██ ████  ██    ██                 ██    ██      ██ ██    ██')
    print(f' ███████  ██████   ██████     ██                  ██████  ███████  ██████{bcolors.ENDC}\n')

def logInfo(msg):
    print(f'[{bcolors.GREEN}INFO{bcolors.ENDC}] | {getTimestamp()} | {msg}')

def logFail(msg):
    print(f'[{bcolors.FAIL}FAIL{bcolors.ENDC}] | {getTimestamp()} | {msg}')

def logError(msg):
    print(f'[{bcolors.WARNING}ERROR{bcolors.ENDC}] | {getTimestamp()} | {msg}')