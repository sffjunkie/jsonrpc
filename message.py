# Copyright (c) 2013-2014 Simon Kennedy <sffjunkie+code@gmail.com>.

import json
import uuid

from ..jsonrpc import RPCError

__all__ = ['RPCMessageError', 'RPCRequest', 'RPCResponse']


class RPCMessageError(RPCError):
    def __init__(self, message, code=None, data=None):
        Exception.__init__(self, message)
        self.message = message


class RPCRequestError(RPCError):
    def __init__(self, message, code=None, data=None):
        Exception.__init__(self, message)
        self.message = message
        self.code = code
        self.data = data

    def __str__(self):
        if self.code:
            return '%d:%s' % (self.code, self.message)
        else:
            return '%s' % self.message


class RPCRequest(object):
    def __init__(self, method='', uid=None, version='2.0',
    			 notification=False, *args, **kwargs):
        """Construct a JSON request
        
        :param method: The method name to call
        :type method:  str
        :param uid: The message id to send can be any type
        :type uid: Any JSON encodeable value
        :param version: The version of JSON message to produce
        :type version: str
        :param notification: True if this is a notification message,
                             False otherwise
        :type notification: bool
        
        Any keyword arguments other than those specified above are encoded as
        named parameters."""
        
        self.method = method
        self.version = version

        self.uid = None
        if not notification:
            if not uid:
                self.uid = str(uuid.uuid4())
            elif uid == '':
                raise RPCMessageError('RPCRequest: No (u)id provided')
            else:
                self.uid = uid

        self.notification = notification
        
        if args and kwargs:
            raise RPCMessageError(('JSONRPC cannot handle positional and '
                            'named arguments in the same request'))

        self.params = None
        if args:
            self.params = list(args)
        
        if kwargs:
            self.params = kwargs.copy()

    def __repr__(self):
        return 'RPCRequest: %s, %s' % (str(self.uid), self.method)
        
    def append(self, nameorvalue, value=None):
        """Append a parameter.
        
        A JSON command can have either named or unnamed parameters
        but not both.
        
        :param nameorvalue: Name of parameter to add to named parameters or
                            value of unnamed parameter.
        :type nameorvalue:  Any - If a parameter name then this will be
                            converted to a string.
        :param value:       Value of a named parameter
        :type value:        Any
        """
        if value is None:
            if self.params is None:
                self.params = [nameorvalue]
            else:
                if isinstance(self.params, list):
                    self.params.append(nameorvalue)
                else:
                    raise RPCMessageError(('Cannot add positional parameter %s '
                                    'to command with named arguments.') % \
                                    nameorvalue)
        else:
            if self.params is None:
                self.params = {}
                
            self.params[str(nameorvalue)] = value
        
    def marshal(self):
        """Convert command to a string ready to be sent over the wire"""
        
        if self.method == '':
            raise RPCMessageError(('RPCRequest.marshal: '
                            'No method name specified.'))
        
        data = { 'method': self.method }
        
        if self.params is not None:
            data['params'] = self.params

        if self.uid is not None:
            data['id'] = self.uid
        
        if self.version == '1.1':
            data['version'] = '1.1'
        elif self.version == '2.0':
            data['jsonrpc'] = '2.0'
        
        return json.dumps(data).encode('UTF-8')

    def unmarshal(self, data):
        """Initialise the command with data from over the wire
        
        :param data: The data to initialise the command with.
        :type data: string
        """
        
        if len(data) == 0:
            raise RPCMessageError('Empty JSON data received.')
        
        if isinstance(data, (bytes, bytearray)):
            data = data.decode('UTF-8')
            
        data = json.loads(data)
        
        if 'jsonrpc' in data:
            self.version = data.pop('jsonrpc')
        else:
            self.version = data.pop('version', '1.0')
        
        self.uid = data.pop('id', None)
        self.notification = self.uid is None
            
        self.method = data.pop('method', None)
        
        if not self.method:
            raise RPCMessageError('No method specified.')
            
        if 'params' not in data:
            self.params = None
        elif isinstance(data['params'], (list, dict)):
            self.params = data['params']
        else:
            self.params = [data['params']]


class RPCResponse(object):
    def __init__(self, uid='', version='2.0'):
        """Construct a JSON response
        
        :param uid:      ID of command we are responding to
        :type uid:       Any
        :param version: The JSON RPC version to use. Should be one of
                        1.0, 1.1 or 2.0
        :type version:  string
        """
        
        self.uid = uid
        self.version = version
        self.result = None
        self.error = None

    def __getitem__(self, key):
        if self.result is not None:
            try:
                return self.result[key]
            except KeyError:
                raise RPCMessageError('%s not found in result' % key)
        else:
            raise RPCMessageError('No results found')

    def __repr__(self):
        return 'RPCResponse: %s' % str(self.uid)
    
    def marshal(self):
        """Convert response to bytes ready to be sent over the wire"""
        
        if self.uid == '':
            raise RPCMessageError('Unable to marshal response: No id specified.')
        
        data = {
            'id': self.uid,
            'result': None,
            'error': None,
        }
        
        if self.version == '2.0':
            data['jsonrpc'] = '2.0'
        else:
            data['version'] = self.version
            
        if self.error is not None:
            data['error'] = self.error
        elif self.result is not None:
            data['result'] = self.result
            
        return json.dumps(data).encode('UTF-8')
        
    def unmarshal(self, data):
        """Initialise the response with data from over the wire
        
        :param data:   The data to initialise the command with.
        :type data:    string
        """
        if len(data) == 0:
            raise RPCMessageError('Empty JSON data received.')
        
        if isinstance(data, (bytes, bytearray)):
            data = data.decode('UTF-8')
            
        data = json.loads(data)

        self.result = data.pop('result', None)
        self.error = data.pop('error', None)
        
        if self.result and self.error:
            raise RPCMessageError('Invalid response data: Both "result" and "error" specified.')
        
        if not self.result and not self.error:
            raise RPCMessageError('Invalid response data: "result" or "error" not specified.')
        
        if self.error is not None:
            data = self.error.get('data', None)
            raise RPCRequestError(self.error['message'], self.error['code'], data)

        self.uid = data.pop('id')
        
        if 'jsonrpc' in data:
            self.version = data['jsonrpc']
        else:
            self.version = data.get('version', '1.0')

