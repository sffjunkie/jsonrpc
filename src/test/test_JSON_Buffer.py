# Copyright (c) 2014 Simon Kennedy <sffjunkie+code@gmail.com>.

import sys
import os.path
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, p)

from unittest import mock

from jsonrpc.buffer import JSONBuffer

def test_JSONBuffer_CompleteMessage():
    h = mock.MagicMock()
    b = JSONBuffer(result_handler=h)
    b.append(b'{"result1": "1"}')
    assert h.call_count == 1


def test_JSONBuffer_2Parts():
    h = mock.MagicMock()
    b = JSONBuffer(result_handler=h)
    b.append(b'{"result2":')
    b.append(b' "1"}')
    assert h.call_count == 1


def test_JSONBuffer_PartialAtStart():
    h = mock.MagicMock()
    b = JSONBuffer(result_handler=h)
    b.append(b' "1"}')
    b.append(b'{"result3": "\'1"}')
    assert h.call_count == 1


def test_JSONBuffer_2CompleteMessages():
    h = mock.MagicMock()
    b = JSONBuffer(result_handler=h)
    b.append(b'{"result4": "1"}{"result5": "\'1"}')
    assert h.call_count == 2


def test_JSONBuffer_2PartialMessages():
    h = mock.MagicMock()
    b = JSONBuffer(result_handler=h)
    b.append(b'{"res')
    b.append(b'ult6": "1"}{"')
    b.append(b'result7": "\'1"}')
    assert h.call_count == 2
