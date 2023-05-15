from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CreatePuppetReply(_message.Message):
    __slots__ = ["id", "vin_filename"]
    ID_FIELD_NUMBER: _ClassVar[int]
    VIN_FILENAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    vin_filename: str
    def __init__(self, id: _Optional[str] = ..., vin_filename: _Optional[str] = ...) -> None: ...

class DestroyPuppetRequest(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class StartStdinNotifyRequest(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class StdinContent(_message.Message):
    __slots__ = ["id", "payload"]
    ID_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    id: str
    payload: str
    def __init__(self, id: _Optional[str] = ..., payload: _Optional[str] = ...) -> None: ...

class StdinNotify(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
