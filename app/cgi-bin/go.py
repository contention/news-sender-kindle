#!/usr/bin/python3

import cgi
import cgitb
import os
import build
cgitb.enable()

print('Content-Type: text/html')
print('')

arguments = cgi.FieldStorage()

if 'password' in arguments:
    if arguments['password'].value != os.environ['SERVER_PASSWORD']:
        print('Password is incorrect')
        exit()
    else:
        print('Password is correct!')
        build.build()
else:
    print('No password provided')
    exit()