# Copyright (c) 2014 Simon Kennedy <sffjunkie+code@gmail.com>

import sys
import os.path
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, p)

import pytest

import json
from jsonrpc.message import RPCRequest, RPCResponse, RPCMessageError


def test_Request_Kwargs():
    command = RPCRequest('VideoLibrary.GetMovies', uid=1, dave=True, wally=False)
    p = command.params
    assert p['dave'] == True
    assert p['wally'] == False


def test_Request_Marshal():
    command = RPCRequest('VideoLibrary.GetMovies', uid=1)
    command.params = {"properties": ["genre", "playcount", "file"]}

    message = command.marshal()
    data = json.loads(message.decode('UTF-8'))
    assert data['method'] == 'VideoLibrary.GetMovies'
    assert len(data['params']) == 1
    assert len(data['params']['properties']) == 3
    assert data['params']['properties'][1] == 'playcount'


def test_Request_Unmarshal_List():
    command = RPCRequest()
    command.unmarshal(b'{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": ["genre", "playcount", "file"], "id": 1}')
    assert command.method == 'VideoLibrary.GetMovies'
    assert len(command.params) == 3
    assert command.params[2] == 'file'


def test_Request_Unmarshal_Object():
    command = RPCRequest()
    command.unmarshal(b'{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "properties": ["genre", "playcount", "file"]}, "id": 1}')
    assert command.method == 'VideoLibrary.GetMovies'
    assert len(command.params) == 1
    assert len(command.params['properties']) == 3
    assert command.uid == 1


def test_Request_Unmarshal_NoMethod():
    command = RPCRequest()

    with pytest.raises(RPCMessageError):
        command.unmarshal(b'{"jsonrpc": "2.0", "params": { "properties": ["genre", "playcount", "file"]}, "id": 1}')


def test_Response_MarshalResult():
    response = RPCResponse(uid=1)
    response.result = 'hello'

    message = response.marshal()
    data = json.loads(message.decode('UTF-8'))
    assert data['id'] == 1
    assert data['result'] == 'hello'


def test_Response_MarshalError():
    response = RPCResponse(uid=1)
    response.error = {'code': -32768, 'message': 'Unable to get movies'}

    message = response.marshal()
    data = json.loads(message.decode('UTF-8'))
    assert data['id'] == 1
    assert data['result'] == None
    assert data['error']['code'] == -32768
    assert data['error']['message'] == 'Unable to get movies'


def test_Response_Unmarshal_List():
    response = RPCResponse()
    response.unmarshal(b'{"jsonrpc": "2.0", "result": [1, "a"], "id": 1}')
    assert len(response.result) == 2
    assert response.result[1] == 'a'


def test_Response_Unmarshal_Object():
    response = RPCResponse()
    response.unmarshal(b'{"jsonrpc": "2.0", "result": {"a": 1}, "id": 1}')
    assert len(response.result) == 1
    assert response.result['a'] == 1
    assert response.uid == 1
    assert response.version == '2.0'


def test_Response_UnmarshalError():
    with pytest.raises(RPCMessageError):
        response = RPCResponse()
        response.unmarshal(b'{"jsonrpc": "2.0", "result": null, "error": {"code": -32768, "message": "Bad id"}, "id": 1}')


def test_Response_UnmarshalErrorInfo():
    try:
        response = RPCResponse()
        response.unmarshal(b'{"jsonrpc": "2.0", "result": null, "error": {"code": -32768, "message": "Bad id"}, "id": 1}')
    except RPCMessageError as exc:
        assert exc.code == -32768
        assert exc.message == 'Bad id'
