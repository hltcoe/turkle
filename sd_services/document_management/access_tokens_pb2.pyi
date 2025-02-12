from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SourceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CLOSINGS: _ClassVar[SourceType]
    ORDERS: _ClassVar[SourceType]
    PACKAGES: _ClassVar[SourceType]
    ENOTES: _ClassVar[SourceType]
    POST_CLOSINGS: _ClassVar[SourceType]
    SETTLEMENT_ORDERS: _ClassVar[SourceType]
    CLOSINGS_REDRAWS: _ClassVar[SourceType]
    CLOSINGS_CLOSINGUSERS: _ClassVar[SourceType]
    EMAILS: _ClassVar[SourceType]
    CLOSINGS_DOCUMENT_PUSHBACKS: _ClassVar[SourceType]
    PACKAGE_PAGES: _ClassVar[SourceType]
    CLOSINGS_DATA_EXPORTS: _ClassVar[SourceType]
    CLOSING_DISCLOSURES: _ClassVar[SourceType]
    CLOSING_DISCLOSURE_PAGES: _ClassVar[SourceType]
    ENOTE_PAGES: _ClassVar[SourceType]
    LOS: _ClassVar[SourceType]
CLOSINGS: SourceType
ORDERS: SourceType
PACKAGES: SourceType
ENOTES: SourceType
POST_CLOSINGS: SourceType
SETTLEMENT_ORDERS: SourceType
CLOSINGS_REDRAWS: SourceType
CLOSINGS_CLOSINGUSERS: SourceType
EMAILS: SourceType
CLOSINGS_DOCUMENT_PUSHBACKS: SourceType
PACKAGE_PAGES: SourceType
CLOSINGS_DATA_EXPORTS: SourceType
CLOSING_DISCLOSURES: SourceType
CLOSING_DISCLOSURE_PAGES: SourceType
ENOTE_PAGES: SourceType
LOS: SourceType

class AccessTokenRequest(_message.Message):
    __slots__ = ("source_id", "source_type", "permitted_actions", "document_type", "whitelisted_mime_types", "combined_document_ids", "document_id", "s3_path")
    class PermittedAction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SHOW: _ClassVar[AccessTokenRequest.PermittedAction]
        CREATE: _ClassVar[AccessTokenRequest.PermittedAction]
        DESTROY: _ClassVar[AccessTokenRequest.PermittedAction]
        INDEX: _ClassVar[AccessTokenRequest.PermittedAction]
        RENAME: _ClassVar[AccessTokenRequest.PermittedAction]
    SHOW: AccessTokenRequest.PermittedAction
    CREATE: AccessTokenRequest.PermittedAction
    DESTROY: AccessTokenRequest.PermittedAction
    INDEX: AccessTokenRequest.PermittedAction
    RENAME: AccessTokenRequest.PermittedAction
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PERMITTED_ACTIONS_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    WHITELISTED_MIME_TYPES_FIELD_NUMBER: _ClassVar[int]
    COMBINED_DOCUMENT_IDS_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    S3_PATH_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    source_type: SourceType
    permitted_actions: _containers.RepeatedScalarFieldContainer[AccessTokenRequest.PermittedAction]
    document_type: str
    whitelisted_mime_types: _containers.RepeatedScalarFieldContainer[str]
    combined_document_ids: _containers.RepeatedScalarFieldContainer[int]
    document_id: str
    s3_path: str
    def __init__(self, source_id: _Optional[str] = ..., source_type: _Optional[_Union[SourceType, str]] = ..., permitted_actions: _Optional[_Iterable[_Union[AccessTokenRequest.PermittedAction, str]]] = ..., document_type: _Optional[str] = ..., whitelisted_mime_types: _Optional[_Iterable[str]] = ..., combined_document_ids: _Optional[_Iterable[int]] = ..., document_id: _Optional[str] = ..., s3_path: _Optional[str] = ...) -> None: ...

class AccessTokenResponse(_message.Message):
    __slots__ = ("access_token",)
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    access_token: str
    def __init__(self, access_token: _Optional[str] = ...) -> None: ...
