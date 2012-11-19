#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Cameria System
# Copyright (C) 2008-2012 Hive Solutions Lda.
#
# This file is part of Hive Cameria System.
#
# Hive Cameria System is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hive Cameria System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hive Cameria System. If not, see <http://www.gnu.org/licenses/>.

__author__ = "João Magalhães <joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "0.1.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2012 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

import time
import socket
import httplib
import urlparse
import datetime

BASE_URL = "http://galeriadajoia.dyndns.org:7010"
""" The base url to be used in the construction of
the access url for get and post """

BASE_ADDRESS = "galeriadajoia.dyndns.org:7010"
""" The base address to be used in the construction of
the access url for get and post """

REMOTE_SERVER = "www.google.com"
""" The remote connection to be used to ensure
access to the "outside" internet """

USERNAME = "admin"
""" The username value to be used in the authentication
process for the router """

PASSWORD = "admin"
""" The password value to be used in the authentication
process for the router """

SLEEP_TIME = 10.0
""" The amount of time to be used in between
connection attempts """

COOKIE_DATA = "LOGINUNAME=%s&LOGINPASSWD=%s"
""" The base data to be sent in the cookie message
this should be the authentication value """

COOKIE_MESSAGE = "POST /cgi-bin/login.cgi HTTP/1.1\r\n\
Host: galeriadajoia.dyndns.org:7010\r\n\
Content-Length: %d\r\n\
Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.3\r\n\
\r\n\
%s"
""" The cookie base post message to be used in
the communication with the server side """

def ping():
    """
    "Ping" a remote web site to ensure that there's
    an available internet connection with the "outside"
    world.

    This method should return a boolean indicating if
    the connection is valid or not.

    @rtype: bool
    @return: If there's a valid internet connection with
    the "outside" world.
    """

    log("Ping", "running to remote server (%s) ..." % REMOTE_SERVER)

    try:
        connection = httplib.HTTPConnection(REMOTE_SERVER)
        connection.request("GET", "/")
        response = connection.getresponse()
        if not response: return False
        log("Ping", "response received with code '%s'" % response.status)
        return True
    except BaseException, exception:
        log("Ping", "failed to perform ping operation '%s'" % str(exception))
        return False

def connect(delay = 20.0):
    log("Connect", "started the connection (%fs delay) ..." % delay)

    time.sleep(delay)
    connection = get_connection()
    headers = get_headers()
    connection.request(
        "GET",
        "/cgi-bin/getcfg.cgi?wanstatus+/content/wan/wan.html+connect",
        headers = headers
    )
    response = connection.getresponse()
    log("Connect", "response received with code '%s'" % response.status)

def disconnect(delay = 20.0):
    log("Disconnect", "starts the connection (%fs delay) ..." % delay)

    time.sleep(delay)
    connection = get_connection()
    headers = get_headers()
    connection.request(
        "GET",
        "/cgi-bin/getcfg.cgi?wanstatus+/content/wan/wan.html+disconnect",
        headers = headers
    )
    response = connection.getresponse()
    log("Disconnect", "response received with code '%s'" % response.status)

def get_connection():
    connection = httplib.HTTPConnection(BASE_ADDRESS)
    return connection

def get_headers():
    cookie = get_cookie()
    return {
        "Cookie" : cookie
    }

def get_cookie():
    log("Cookie", "new connection cookie value (authentication) ...")

    # sets the "initial" socket reference as invalid
    # this is considered the default behavior
    _socket = None

    # parses the current base url unpacking it into the host
    # and part components to be used in the connection
    parse = urlparse.urlparse(BASE_URL)
    host = parse.hostname
    port = parse.port

    # tries to resolve the provided address into defined
    # address for the provided types (tcp)
    results = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)

    # iterates over all the resolution results to try
    # to create and connect to an associated socket
    for result in results:
        # unpacks the current result into the appropriate
        # parts to be used in the socket creation
        af, socktype, proto, _canon, address = result

        # creates the socket object from the (unpacked) results
        # of the resolution
        try: _socket = socket.socket(af, socktype, proto)
        except socket.error: _socket = None; continue

        # tries to connect to the remote host, in case there's
        # an error closes the socket sets it as invalid and continues
        # the current loop (tries again)
        try: _socket.connect(address)
        except socket.error:
            _socket.close()
            _socket = None
            continue

        # in case this point is reached a correct connection
        # was established, no need to continues the loop
        break

    # in case no socket was created must raise an exception
    # indicating the problem
    if _socket == None: raise RuntimeError("Socket creation was not possible")

    # creates the "final" post message to be sent to the server
    # using the currently set username and password values
    data = COOKIE_DATA % (USERNAME, PASSWORD)
    message = COOKIE_MESSAGE % (len(data), data)

    # sends the "final" message to the server and then waits
    # for the response value from it
    _socket.sendall(message)
    data = []
    while True:
        _data = _socket.recv(1024)
        if not _data: break
        data.append(_data)

    # closes the socket no need for it to remain open (no
    # more data to be transmitted)
    _socket.close()

    # joins the complete set of data for the response and
    # then splits the response into various lines
    response = "".join(data)
    lines = response.split("\n")
    headers = lines[1:]

    # starts the cookie value as unset, this is the default
    # value to be used in case it's not found
    cookie = None

    # iterates over the complete set of headers to try to find
    # the set cookie header and retrieve its value
    for header in headers:
        cenas = header.strip().split(":", 1)
        if len(cenas) == 1: continue
        name, value = cenas
        if not name == "Set-Cookie": continue
        cookie = value.strip()

    # prints a message indicating the finding of the cookie value
    # and returns the string containing it
    log("Cookie", "authentication cookie received '%s'" % cookie)
    return cookie

def log(name, message):
    current = datetime.datetime.now()
    current_string = current.strftime("%H:%M:%S")
    print "[%s] %s - %s" % (name, current_string, message)

def run():
    # iterates continuously pinging the remote web
    # server in order to ensure connection
    while True:
        # tries to ping the remote server to ensure
        # connection in case it fails reconnects the
        # connection again in the modem
        result = ping()
        if not result: connect()

        # sleeps for a while to avoid flooding of the
        # current connection
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    run()
