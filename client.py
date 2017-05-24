# Copyright (c) 2014 Simon Kennedy <sffjunkie+code@gmail.com>.

import asyncio
import aiohttp
from functools import partial

from mogul.jsonrpc import buffer
from mogul.jsonrpc.message import RPCRequest, RPCResponse, RPCMessageError

__all__ = ['RPCClient']


class RPCClient():
    """An asyncio JSON RPC client.

    Args:
        host (str): Host name to send requests to
        port (int): Port number on the host to communicate with.
        timeout (float): Timeout in seconds for connection to the host
        method (str): The method to use to send the requests either
                      'http' (default) or 'tcp'
        path (str): The path to send the request to; (http only)
        username (str): User name to authenticate with; (http only)
        password (str): Password to authenticate with; (http only)
        notification_handler (coroutine): A coroutine which receives RPCResponse
            notifications (tcp only)
    """
    def __init__(self, host,
                 port=8080,
                 timeout=-1,
                 method='http',
                 path='/jsonrpc',
                 username='', password='',
                 notification_handler=None):

        if method not in ['tcp', 'http']:        
            raise RPCMessageError('Unrecognised method %s specified', method)

        self.host = host
        self.port = port
        self.timeout = timeout
        self.method = method
        self.path = path
        self.username = username
        self.password = password
        self.notification_handler = notification_handler
        
        self._tcp_protocol = None
        self._namespace_cache = {}
        
        self.loop = asyncio.get_event_loop()
    
    @asyncio.coroutine
    def request(self, request, method=None, *args, **kwargs):
        """Send an RPC request.
        
        Args:
            request (:class:`RPCRequest`): The request to send.
            
        Returns:
            None: No response received.
            :class:`RPCResponse`: The response from the host
        """
        method = method or self.method
        if method == 'http':
            response = yield from self._send_http_request(request, *args, **kwargs)
        elif method == 'tcp':
            response = yield from self._send_tcp_request(request, *args, **kwargs)

        return response
    
    def close(self):
        if self._tcp_protocol:
            self._tcp_protocol._transport.close()
    
    @asyncio.coroutine
    def _send_http_request(self, request, *args, **kwargs):
        """Send a request using HTTP
        
        Args:
            request (:class:`RPCRequest`): The request to send.
            
        Returns:
            None: No response received.
            :class:`RPCResponse`: The response from the host.
        """
        request_data = request.marshal()
        
        path = kwargs.get('path', self.path)
        
        url = 'http://{}:{}{}'.format(self.host, self.port, path)
        
        auth = None
        if self.username != '':
            
            if self.password == '':
                auth = aiohttp.BasicAuth(self.username)
            else:
                auth = aiohttp.BasicAuth(self.username, self.password)
                
        headers = {'Content-Type': 'application/json'}

        http_request = aiohttp.request('POST', url,
                                       data=request_data,
                                       headers=headers,
                                       auth=auth,
                                       loop=self.loop)
        
        if request.notification:
            return None
        else:
            if self.timeout == -1:
                http_response = yield from http_request
            else:
                http_response = yield from asyncio.wait_for(http_request,
                                                            self.timeout)
            
            if http_response.status == 200:
                body = yield from http_response.read()
                
                response = RPCResponse()
                response.unmarshal(body)
                result = response.result
            else:
                result = None
                
            return result
    
    @asyncio.coroutine
    def _send_tcp_request(self, request, *args, **kwargs):
        """Send a request using TCP
        
        Args:
            request (:class:`RPCRequest`): The request to send.
        """
        if not self._tcp_protocol:
            factory = lambda: _TCPProtocol(self.timeout,
                                           self.notification_handler)
            
            coro = self.loop.create_connection(factory,
                self.host, self.port)
            
            if self.timeout == -1:
                (_t, protocol) = yield from coro
            else:
                (_t, protocol) = yield from asyncio.wait_for(coro,
                                                             self.timeout)
            
            self._tcp_protocol = protocol

        response = yield from protocol.send(request)
        return response

    def __getattr__(self, namespace):
        if namespace in self._namespace_cache:
            return self._namespace_cache[namespace]

        nsobj = self.RPCNamespace(namespace, self)
        self._namespace_cache[namespace] = nsobj
        
        return nsobj
    
    class RPCNamespace(object):
        def __init__(self, name, protocol):
            self.name = name
            self.protocol = protocol
            self._id = 1
            self._handler_cache = {}
    
        def __getattr__(self, method):
            if method in self._handler_cache:
                return self._handler_cache[method]
    
            @asyncio.coroutine
            def handler(method, *args, **kwargs):
                method = '{}.{}'.format(self.name, method)
                request = RPCRequest(method, *args, **kwargs)
                response = yield from self.protocol.request(request)
                return response
            
            h = partial(handler, method)
            self._handler_cache[method] = h
            return h


class _TCPProtocol(asyncio.Protocol):
    """Send JSONRPC messages using the TCP _transport"""
    
    def __init__(self, timeout=-1, notification_handler=None):
        self.responses = None
        self.notifications = None

        self._timeout = timeout
        self._notification_handler = notification_handler
    
    @asyncio.coroutine
    def send(self, request):
        """Send a request
        
        Args:
            request (:class:`RPCRequest`): The request to send.
        """
        request_data = request.marshal()
        
        self._transport.write(request_data)
        
        if request.notification:
            return None
        else:
            response = yield from self._wait_for_response(request.uid)
            return response
    
    def connection_made(self, transport):
        self.responses = {}
        self.notifications = []
        
        self._buffer = buffer.JSONBuffer()
        self._transport = transport
        
    def data_received(self, data):
        self._buffer.append(data)
    
    @asyncio.coroutine
    def _wait_for_data(self, uid):
        while True:
            for data in self._buffer.messsages:
                try:
                    message = RPCResponse()
                    message.unmarshal(data)
                    
                    self.responses[message.uid] = message
                    
                # If there's an error unmarshaling a Response then we
                # need to try to unmarshall as a notification Request
                except RPCMessageError:
                    message = RPCRequest()
                    message.unmarshal(message)
                    self.notifications.append(message)
                    
            del self._buffer.messages[:]
            yield from asyncio.sleep(0.1)
    
    @asyncio.coroutine
    def _wait_for_response(self, uid):
        while True:
            response = self.responses.pop(uid, None)
            if response:
                return response
            else:
                yield from asyncio.sleep(0.1)
    

