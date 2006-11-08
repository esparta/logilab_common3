# Copyright (c) 2005-2006 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""Deprecation utilities"""

from warnings import warn
from logilab.common.modutils import load_module_from_name

class deprecated(type):
    """metaclass to print a warning on instantiation of a deprecated class"""
    
    def __call__(cls, *args, **kwargs):
        msg = getattr(cls, "__deprecation_warning__",
                      "%s is deprecated" % cls.__name__)
        warn(msg, DeprecationWarning, stacklevel=2)
        return type.__call__(cls, *args, **kwargs)


def class_renamed(old_name, new_class, message=None):
    """automatically creates a class which fires a DeprecationWarning
    when instantiated.
    
    >>> Set = class_renamed('Set', set, 'Set is now replaced by set')
    >>> s = Set()
    sample.py:57: DeprecationWarning: Set is now replaced by set
      s = Set()
    >>>
    """
    clsdict = {}
    if message is not None:
        clsdict['__deprecation_warning__'] = message
    try:
        # new-style class
        return deprecated(old_name, (new_class,), clsdict)
    except (NameError, TypeError):
        # old-style class
        class DeprecatedClass(new_class):
            """FIXME: There might be a better way to handle old/new-style class
            """
            def __init__(self, *args, **kwargs):
                warn(message, DeprecationWarning, stacklevel=2)
                new_class.__init__(self, *args, **kwargs)
        return DeprecatedClass


def deprecated_function(new_func, message=None):
    """creates a function which fires a DeprecationWarning when used

    For example, if <bar> is deprecated in favour of <foo> :
    >>> bar = deprecated_function(foo, 'bar is deprecated')
    >>> bar()
    sample.py:57: DeprecationWarning: bar is deprecated
      bar()
    >>>
    """
    if message is None:
        message = "this function is deprecated, use %s instead" % (
            new_func.func_name)
    def deprecated(*args, **kwargs):
        warn(message, DeprecationWarning, stacklevel=2)
        return new_func(*args, **kwargs)
    return deprecated

def moved(modpath, objname):
    def callnew(*args, **kwargs):
        message = "this object has been moved, it's now %s.%s" % (
            modpath, objname)
        warn(message, DeprecationWarning, stacklevel=2)
        m = load_module_from_name(modpath)
        return getattr(m, objname)(*args, **kwargs)
    return callnew