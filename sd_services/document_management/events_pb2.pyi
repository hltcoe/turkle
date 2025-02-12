from sd_services.document_management import access_tokens_pb2 as _access_tokens_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DocumentActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CREATED: _ClassVar[DocumentActionType]
    DOWNLOADED: _ClassVar[DocumentActionType]
    DELETED: _ClassVar[DocumentActionType]
    RENAMED: _ClassVar[DocumentActionType]
CREATED: DocumentActionType
DOWNLOADED: DocumentActionType
DELETED: DocumentActionType
RENAMED: DocumentActionType

class DocumentEvent(_message.Message):
    __slots__ = ("source_id", "source_type", "document_type", "id", "generated_by_user_id", "generated_by_user_role", "filename", "request", "action", "previous_filename")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    GENERATED_BY_USER_ID_FIELD_NUMBER: _ClassVar[int]
    GENERATED_BY_USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_FILENAME_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    source_type: _access_tokens_pb2.SourceType
    document_type: str
    id: int
    generated_by_user_id: int
    generated_by_user_role: str
    filename: str
    request: UserHttpRequest
    action: DocumentActionType
    previous_filename: str
    def __init__(self, source_id: _Optional[str] = ..., source_type: _Optional[_Union[_access_tokens_pb2.SourceType, str]] = ..., document_type: _Optional[str] = ..., id: _Optional[int] = ..., generated_by_user_id: _Optional[int] = ..., generated_by_user_role: _Optional[str] = ..., filename: _Optional[str] = ..., request: _Optional[_Union[UserHttpRequest, _Mapping]] = ..., action: _Optional[_Union[DocumentActionType, str]] = ..., previous_filename: _Optional[str] = ...) -> None: ...

class UserHttpRequest(_message.Message):
    __slots__ = ("remote_ip", "user_agent", "original_url", "referer")
    REMOTE_IP_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_URL_FIELD_NUMBER: _ClassVar[int]
    REFERER_FIELD_NUMBER: _ClassVar[int]
    remote_ip: str
    user_agent: str
    original_url: str
    referer: str
    def __init__(self, remote_ip: _Optional[str] = ..., user_agent: _Optional[str] = ..., original_url: _Optional[str] = ..., referer: _Optional[str] = ...) -> None: ...
