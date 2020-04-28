#!/usr/bin/python3

import functools
import os

DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
adminRoles = {'admin', 'mod', 'discord mod'}

def debug(func):
    """Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})\n")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}\n")
        return value
    return wrapper_debug


def fetchFile(directory, filename):
	with open(DEFAULT_DIR+'/'+directory+'/'+filename+'.txt', 'r') as f:
		return f.read()

def is_admin(roles):
	for role in roles:
		if str(role).lower() in adminRoles:
			return True
	else: return False

def is_bot(roles):
	for role in roles:
		if str(role).lower() == 'bot':
			return True
	else: return False
