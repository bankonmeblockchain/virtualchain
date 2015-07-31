#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    virtualchain
    ~~~~~
    :copyright: (c) 2015 by Openname.org
    :license: MIT, see LICENSE for more details.
"""

import argparse
import logging
import os
import os.path
import sys
import subprocess
import signal
import json
import datetime
import traceback
import httplib
import ssl
import threading
import time
import socket

from ..config import DEBUG
from utilitybelt import is_valid_int
from ConfigParser import SafeConfigParser

create_ssl_authproxy = False 
do_wrap_socket = False

if hasattr( ssl, "_create_unverified_context" ):
   ssl._create_default_https_context = ssl._create_unverified_context
   create_ssl_authproxy = True 

if not hasattr( ssl, "create_default_context" ):
   create_ssl_authproxy = False
   do_wrap_socket = True

log = logging.getLogger()
log.setLevel(logging.DEBUG if DEBUG else logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG if DEBUG else logging.INFO)
log_format = ('[%(levelname)s] [%(module)s:%(lineno)d] %(message)s' if DEBUG else '%(message)s')
formatter = logging.Formatter( log_format )
console.setFormatter(formatter)
log.addHandler(console)

from bitcoinrpc.authproxy import AuthServiceProxy

class BitcoindConnection( httplib.HTTPSConnection ):
   """
   Wrapped SSL connection, if we can't use SSLContext.
   """

   def __init__(self, host, port, timeout=None ):
   
      httplib.HTTPSConnection.__init__(self, host, port )
      self.timeout = timeout
        
   def connect( self ):
      
      sock = socket.create_connection((self.host, self.port), self.timeout)
      if self._tunnel_host:
         self.sock = sock
         self._tunnel()
         
      self.sock = ssl.wrap_socket( sock, cert_reqs=ssl.CERT_NONE )
      

def create_bitcoind_connection( rpc_username, rpc_password, server, port, use_https ):
   
    """
    Creates an RPC client to a bitcoind instance.
    """
    
    global do_wrap_socket, create_ssl_authproxy
        
    log.debug("[%s] Connect to bitcoind at %s://%s@%s:%s" % (os.getpid(), 'https' if use_https else 'http', rpc_username, server, port) )
    
    protocol = 'https' if use_https else 'http'
    if not server or len(server) < 1:
        raise Exception('Invalid bitcoind host address.')
    if not port or not is_valid_int(port):
        raise Exception('Invalid bitcoind port number.')
    
    authproxy_config_uri = '%s://%s:%s@%s:%s' % (protocol, rpc_username, rpc_password, server, port)
    
    if do_wrap_socket:
       # ssl._create_unverified_context and ssl.create_default_context are not supported.
       # wrap the socket directly 
       connection = BitcoindConnection( server, int(port) )
       return AuthServiceProxy(authproxy_config_uri, connection=connection)
       
    elif create_ssl_authproxy:
       # ssl has _create_unverified_context, so we're good to go 
       return AuthServiceProxy(authproxy_config_uri)
    
    else:
       # have to set up an unverified context ourselves 
       ssl_ctx = ssl.create_default_context()
       ssl_ctx.check_hostname = False
       ssl_ctx.verify_mode = ssl.CERT_NONE
       connection = httplib.HTTPSConnection( server, int(port), context=ssl_ctx )
       return AuthServiceProxy(authproxy_config_uri, connection=connection)


def connect_bitcoind( bitcoind_opts ):
    """
    Create a connection to bitcoind, using a dict of config options.
    """
    return create_bitcoind_connection( bitcoind_opts['bitcoind_user'], bitcoind_opts['bitcoind_passwd'], bitcoind_opts['bitcoind_server'], bitcoind_opts['bitcoind_port'], bitcoind_opts['bitcoind_use_https'] )
 
