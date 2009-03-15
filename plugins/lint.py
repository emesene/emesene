#!/usr/bin/python
import sys
import os
from pylint import lint

def lint_plugin(whatever):
	if os.path.isfile(whatever):
		lint_file(whatever)
	else:
		lint_dir(whatever)

def lint_file(file):
	sys.path.append('..')
	lint.Run(['-f', '--rcfile=standard.rc', '--parseable'] + sys.argv[1:])


def lint_dir(dir):
	sys.path.append('..')
	sys.argv[1] = os.path.join(sys.argv[1], 'plugin.py')
	lint.Run(['-f', 'parseable', '--rcfile=plutin.pylint.rc'] + sys.argv[1:])


if __name__ == '__main__':
	print sys.argv
	lint_plugin(sys.argv[1])

