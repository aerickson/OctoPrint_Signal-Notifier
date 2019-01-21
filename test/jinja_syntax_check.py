#!/usr/bin/env python

# based on https://stackoverflow.com/questions/37939131/how-to-validate-jinja-syntax-without-variable-interpolation

import sys
import os
from jinja2 import Environment

mytemplates = 'octoprint_signalnotifier/templates'

env = Environment()
templates = []
for root, dirs, files in os.walk(mytemplates):
        for f in files:
                if f.endswith('.jinja2'):
                        templates.append(os.path.join(root,f))

print("Inspecting the following jinja2 files: ")
for template in templates:
    with open(template) as t:
        print(template)
        env.parse(t.read())

print("SUCCESS")