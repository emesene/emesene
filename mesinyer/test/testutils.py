'''utilities for unit tests'''
import os
import string
import random

def random_string(length=8, with_spaces=True, with_new_lines=False,
        with_tabs=False):
    letters = string.letters

    if with_spaces:
        letters += ' '

    if with_new_lines:
        letters += '\n'

    if with_tabs:
        letters += '\t'

    return ''.join([random.choice(letters) for x in xrange(length)])

def random_binary_data(length):
    numbers = range(255)
    return ''.join([chr(random.choice(numbers)) for x in xrange(length)])

def create_binary_file(path, name_length=8, content_length=4096):
    '''create a file containing random binary data, save it and return the
    path
    '''
    name = random_string(name_length)
    file_path = os.path.join(path, name)
    content = random_binary_data(content_length)
    handle = file(file_path, 'w')
    handle.write(content)
    handle.close()
    return file_path
