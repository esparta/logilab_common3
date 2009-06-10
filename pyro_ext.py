"""Python Remote Object utilities

:organization: Logilab
:copyright: 2009 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
"""
__docformat__ = "restructuredtext en"

import logging

from Pyro import core, naming, errors, util, config

_LOGGER = logging.getLogger('pyro')
_MARKER = object()

def ns_group_and_id(idstr, defaultnsgroup=_MARKER):
    try:
        nsgroup, nsid = idstr.rsplit('.', 1)
    except ValueError:
        if defaultnsgroup is _MARKER:
            nsgroup = config.PYRO_NS_DEFAULTGROUP
        else:
            nsgroup = defaultnsgroup
        nsid = idstr
    if nsgroup is not None and not nsgroup.startswith(':'):
        nsgroup = ':' + nsgroup
    return nsgroup, nsid

def host_and_port(hoststr):
    if not hoststr:
        return None, None
    try:
        hoststr, port = hoststr.split(':')
    except ValueError:
        port = None
    else:
        port = int(port)
    return hoststr, port

_DAEMONS = {}
def _get_daemon(daemonhost, start=True):
    if not daemonhost in _DAEMONS:
        if not start:
            raise Exception('no daemon for %s' % daemonhost)
        if not _DAEMONS:
            core.initServer(banner=0)
        host, port = host_and_port(daemonhost)
        daemon = core.Daemon(host=host, port=port)
        _DAEMONS[daemonhost] = daemon
    return _DAEMONS[daemonhost]


def locate_ns(nshost):
    """locate and return the pyro name server to the daemon"""
    core.initClient(banner=False)
    return naming.NameServerLocator().getNS(*host_and_port(nshost))


def register_object(object, nsid, defaultnsgroup=_MARKER,
                    daemonhost=None, nshost=None):
    """expose the object as a pyro object and register it in the name-server

    return the pyro daemon object
    """
    nsgroup, nsid = ns_group_and_id(nsid, defaultnsgroup)
    daemon = _get_daemon(daemonhost)
    nsd = locate_ns(nshost)
    # make sure our namespace group exists
    try:
        nsd.createGroup(nsgroup)
    except errors.NamingError:
        pass
    daemon.useNameServer(nsd)
    # use Delegation approach
    impl = core.ObjBase()
    impl.delegateTo(object)
    daemon.connect(impl, '%s.%s' % (nsgroup, nsid))
    _LOGGER.info('registered %s a pyro object using group %s and id %s',
                 object, nsgroup, nsid)
    return daemon


def ns_unregister(nsid, defaultnsgroup=_MARKER, nshost=None):
    """unregister the object with the given nsid from the pyro name server"""
    nsgroup, nsid = ns_group_and_id(nsid, defaultnsgroup)
    try:
        nsd = locate_ns(nshost)
    except errors.PyroError, ex:
        # name server not responding
        _LOGGER.error('can\'t locate pyro name server: %s', ex)
    else:
        try:
            nsd.unregister('%s.%s' % (nsgroup, nsid))
            _LOGGER.info('%s unregistered from pyro name server', nsid)
        except errors.NamingError:
            _LOGGER.warning('%s not registered in pyro name server', nsid)


def ns_get_proxy(nsid, defaultnsgroup=_MARKER, nshost=None):
    nsgroup, nsid = ns_group_and_id(nsid, defaultnsgroup)
    # resolve the Pyro object
    try:
        nsd = locate_ns(nshost)
        pyrouri = nsd.resolve('%s.%s' % (nsgroup, nsid))
    except errors.ProtocolError, ex:
        raise Exception('Could not connect to the Pyro name server (host: %s)'
                        % nshost)
    except errors.NamingError:
        raise Exception('Could not get proxy for %s (not registered in Pyro), '
                        'you may have to restart your server-side application'
                        % nsid)
    return core.getProxyForURI(pyrouri)


def set_pyro_log_threshold(level):
    pyrologger = logging.getLogger('Pyro.%s' % str(id(util.Log)))
    # remove handlers so only the root handler is used
    pyrologger.handlers = []
    pyrologger.setLevel(level)