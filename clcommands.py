# Copyright (c) 2004-2006 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""provides helper functions to handle a command line tool providing more than
one command
e.g called as "tool command [options] args..." where <options> and <args> are
command'specific
"""

import sys
from os.path import basename

from logilab.common.configuration import Configuration


DEFAULT_COPYRIGHT = '''\
Copyright (c) 2004-2006 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
http://www.logilab.fr/ -- mailto:contact@logilab.fr'''


class BadCommandUsage(Exception):
    """Raised when an unknown command is used or when a command is not
    correctly used
    """


class Command(Configuration):
    """base class for command line commands"""
    arguments = ''
    name = ''
    
    def __init__(self, __doc__=None, version=None):
        if __doc__:
            usage = __doc__ % (self.name, self.arguments,
                               self.__doc__.replace('    ', ''))
        else:
            usage = self.__doc__.replace('    ', '')
        Configuration.__init__(self, usage=usage, version=version)
        
    def run(self, args):
        """run the command with its specific arguments"""
        raise NotImplementedError()


def pop_arg(args_list, expected_size_after=0, msg="Missing argument"):
    """helper function to get and check command line arguments"""
    try:
        value = args_list.pop(0)
    except IndexError:
        raise BadCommandUsage(msg)
    if len(args_list) > expected_size_after:
        raise BadCommandUsage('Too much arguments')
    return value


_COMMANDS = {}

def register_commands(commands):
    """register existing commands"""
    for command_klass in commands:
        _COMMANDS[command_klass.name] = command_klass


def main_usage(status=0, __doc__=None, copyright=DEFAULT_COPYRIGHT):
    """display usage for the main program (ie when no command supplied)
    and exit
    """
    commands = _COMMANDS.keys()
    commands.sort()
    doc = __doc__ % ('<command>', '<command arguments>',
                     '''\
Type "%%prog <command> --help" for more information about a specific
command. Available commands are :\n  * %s.
''' % '\n  * '.join(commands))
    doc = doc.replace('%prog', basename(sys.argv[0]))
    print 'usage:', doc
    print copyright
    sys.exit(status)


def cmd_run(cmdname, *args):
    try:
        command = _COMMANDS[cmdname](__doc__='%%prog %s %s\n\n%s')
    except KeyError:
        raise BadCommandUsage('no %s command' % cmdname)
    args = command.load_command_line_configuration(args)
    try:
        command.run(args)
    except KeyboardInterrupt:
        print 'interrupted'
    except BadCommandUsage, err:
        print 'ERROR: ', err
        print command.help()

        
def main_run(args, doc):
    """command line tool"""
    try:
        arg = args.pop(0)
    except IndexError:
        main_usage(status=1, __doc__=doc)
    if arg in ('-h', '--help'):
        main_usage(__doc__=doc)
    try:
        cmd_run(arg, *args)
    except BadCommandUsage, err:
        print 'ERROR: ', err
        main_usage(1, doc)
