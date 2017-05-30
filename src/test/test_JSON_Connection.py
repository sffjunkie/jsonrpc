# Copyright (c) 2014 Simon Kennedy <sffjunkie+code@gmail.com>

import sys
import os.path
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, p)

import pytest
import asyncio

from jsonrpc.client import RPCClient
from jsonrpc.message import RPCRequest


def async_test(f):
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    return wrapper


#@async_test
#def test_JSONConnection_Http_GetArtists():
#    conn = RPCClient(host='127.0.0.1', port=8080,
#                     username='xbmc', password='xbmc')
#    request = RPCRequest('AudioLibrary.GetArtists')
#    response = yield from conn.request(request)


#@async_test
#def test_JSONConnection_Http_Introspect():
#    conn = RPCClient(host='127.0.0.1', port=8080,
#                     username='xbmc', password='xbmc')
#    response = yield from conn.JSONRPC.Introspect(filter={'getdescriptions': True})


#@async_test
#def test_JSONConnection_Http_BadPort():
#    conn = RPCClient(host='127.0.0.1', port=8081,
#                     username='xbmc', password='xbmc')
#    request = RPCRequest('AudioLibrary.GetArtists')
#
#    with pytest.raises(Exception):
#        yield from conn.request(request)


#@async_test
#def test_JSONConnection_Http_BadPassword():
#    conn = RPCClient(host='127.0.0.1', port=8080,
#                     username='xbmc', password='dave')
#    request = RPCRequest('AudioLibrary.GetArtists')
#
#    with pytest.raises(Exception):
#        yield from conn.request(request)


#@async_test
#def test_JSONConnection_Http_BadIP():
#    conn = RPCClient(host='192.168.1.10', port=8080,
#                     username='xbmc', password='xbmc',
#                     timeout=1)
#    request = RPCRequest('AudioLibrary.GetArtists')
#
#    with pytest.raises(asyncio.TimeoutError):
#        yield from conn.request(request)


@async_test
def test_JSONConnection_Tcp_Introspect():
    conn = RPCClient(host='127.0.0.1', port=9090, method='tcp')
    request = RPCRequest('JSONRPC.Introspect')
    response = yield from conn.request(request)
    conn.close()


@async_test
def test_JSONConnection_Tcp_Introspect_AttrAccess():
    conn = RPCClient(host='127.0.0.1', port=9090, method='tcp')
    response = yield from conn.JSONRPC.Introspect(getdescriptions=True)
    conn.close()
#    pass


@async_test
def test_JSONConnection_Tcp_Introspect_BadParameter():
    conn = RPCClient(host='127.0.0.1', port=9090, method='tcp')
    response = yield from conn.JSONRPC.Introspect(filter={'getdescriptions': True})
    conn.close()
