# Copyright (c) 2014 Simon Kennedy <sffjunkie+code@gmail.com>.

class JSONBuffer(object):
    """A buffer for JSONRPC messages.
    
    If a result handler is provided then it will be called with the list
    of messages whenever a complete message is received.
    """
    def __init__(self):
        self.messsages = []
        
        self._in_quote = False
        self._quote_char = ''
        self._bracket_count = 0
        self._data = ''
        
    def append(self, data):
        """Append a string or a UTF-8 encoded string"""
        
        if not isinstance(data, str):
            data = data.decode('UTF-8')
            
        pos = start = 0
        end = len(data)

        prev_ch = ''

        while 1:
            ch = data[pos]
            if (ch == '"' or ch == "'") and prev_ch != '\\':
                if not self._in_quote:
                    self._in_quote = True
                    self._quote_char = ch
                elif ch == self._quote_char:
                    self._in_quote = False

            elif ch == '{':
                if not self._in_quote:
                    self._bracket_count += 1
            
            elif ch == '}':
                if not self._in_quote:
                    self._bracket_count -= 1
                    
                    if self._bracket_count == 0:
                        _data = self._data
                        _data += data[start:pos+1]
                        self._data = ''
                        data = data[pos+1:]
                        start = 0
                        end = len(data)
                        pos = -1

                        self.messsages.append(_data)

                    elif self._bracket_count < 0:
                        start = pos + 1
                        self._bracket_count = 0
                        
            prev_ch = ch
            pos += 1
            
            if pos == end:
                break
            
        self._data += data[start:end]
    