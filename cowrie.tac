# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

import sys, os
if sys.platform == 'win32':
    import os, inspect
    # this is when just running on win32
    sys.path.insert(0, os.path.abspath(os.getcwd()))
    # and this is when running as a service
    #os.chdir(os.path.dirname(inspect.getfile(inspect.currentframe())))

from twisted.application import internet, service
from twisted.cred import portal
from twisted.conch.ssh import factory, keys

if os.name == 'posix' and os.getuid() == 0:
    print 'ERROR: You must not run cowrie as root!'
    sys.exit(1)

if not os.path.exists('cowrie.cfg'):
    print 'ERROR: cowrie.cfg is missing!'
    sys.exit(1)

from cowrie.core import auth
from cowrie.core import ssh
from cowrie.core.config import config

factory = ssh.HoneyPotSSHFactory()
factory.portal = portal.Portal(ssh.HoneyPotRealm())

factory.portal.registerChecker(auth.HoneypotPublicKeyChecker())
factory.portal.registerChecker(auth.HoneypotPasswordChecker())

rsa_pubKeyString, rsa_privKeyString = ssh.getRSAKeys()
dsa_pubKeyString, dsa_privKeyString = ssh.getDSAKeys()
factory.publicKeys = {'ssh-rsa': keys.Key.fromString(data=rsa_pubKeyString),
                      'ssh-dss': keys.Key.fromString(data=dsa_pubKeyString)}
factory.privateKeys = {'ssh-rsa': keys.Key.fromString(data=rsa_privKeyString),
                       'ssh-dss': keys.Key.fromString(data=dsa_privKeyString)}

cfg = config()
if cfg.has_option('honeypot', 'ssh_addr'):
    ssh_addr = cfg.get('honeypot', 'ssh_addr')
else:
    ssh_addr = '0.0.0.0'

application = service.Application('honeypot')
for i in ssh_addr.split():
    service = internet.TCPServer(
        int(cfg.get('honeypot', 'ssh_port')), factory,
        interface=i)
    service.setServiceParent(application)

if cfg.has_option('honeypot', 'interact_enabled') and \
        cfg.get('honeypot', 'interact_enabled').lower() in \
        ('yes', 'true', 'on'):
    iport = int(cfg.get('honeypot', 'interact_port'))
    from cowrie.core import interact
    from twisted.internet import protocol
    service = internet.TCPServer(iport, interact.makeInteractFactory(factory))
    service.setServiceParent(application)

# vim: set ft=python sw=4 et:
