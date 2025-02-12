from sd_services.document_management import access_tokens_pb2 as _access_tokens_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Rotation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNCHANGED: _ClassVar[Rotation]
    LEFT: _ClassVar[Rotation]
    DOWN: _ClassVar[Rotation]
    RIGHT: _ClassVar[Rotation]
UNCHANGED: Rotation
LEFT: Rotation
DOWN: Rotation
RIGHT: Rotation

class CreateDocumentRequest(_message.Message):
    __slots__ = ("source_id", "source_type", "document_type", "uploaded_by_user_id", "uploaded_by_user_role", "s3_path", "wait_for_metadata")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    UPLOADED_BY_USER_ID_FIELD_NUMBER: _ClassVar[int]
    UPLOADED_BY_USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    S3_PATH_FIELD_NUMBER: _ClassVar[int]
    WAIT_FOR_METADATA_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    source_type: _access_tokens_pb2.SourceType
    document_type: str
    uploaded_by_user_id: int
    uploaded_by_user_role: str
    s3_path: str
    wait_for_metadata: bool
    def __init__(self, source_id: _Optional[str] = ..., source_type: _Optional[_Union[_access_tokens_pb2.SourceType, str]] = ..., document_type: _Optional[str] = ..., uploaded_by_user_id: _Optional[int] = ..., uploaded_by_user_role: _Optional[str] = ..., s3_path: _Optional[str] = ..., wait_for_metadata: bool = ...) -> None: ...

class CreateDocumentResponse(_message.Message):
    __slots__ = ("id", "uuid")
    ID_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    id: int
    uuid: str
    def __init__(self, id: _Optional[int] = ..., uuid: _Optional[str] = ...) -> None: ...

class RenameDocumentRequest(_message.Message):
    __slots__ = ("id", "new_name", "uuid")
    ID_FIELD_NUMBER: _ClassVar[int]
    NEW_NAME_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    id: int
    new_name: str
    uuid: str
    def __init__(self, id: _Optional[int] = ..., new_name: _Optional[str] = ..., uuid: _Optional[str] = ...) -> None: ...

class RenameDocumentResponse(_message.Message):
    __slots__ = ("id", "uuid")
    ID_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    id: int
    uuid: str
    def __init__(self, id: _Optional[int] = ..., uuid: _Optional[str] = ...) -> None: ...

class UploadDocumentChunk(_message.Message):
    __slots__ = ("id", "filename_with_extension", "file_bytes")
    ID_FIELD_NUMBER: _ClassVar[int]
    FILENAME_WITH_EXTENSION_FIELD_NUMBER: _ClassVar[int]
    FILE_BYTES_FIELD_NUMBER: _ClassVar[int]
    id: int
    filename_with_extension: str
    file_bytes: bytes
    def __init__(self, id: _Optional[int] = ..., filename_with_extension: _Optional[str] = ..., file_bytes: _Optional[bytes] = ...) -> None: ...

class ListDocumentsRequest(_message.Message):
    __slots__ = ("source_id", "source_type", "document_types", "include_deleted", "source_ids")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPES_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_DELETED_FIELD_NUMBER: _ClassVar[int]
    SOURCE_IDS_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    source_type: _access_tokens_pb2.SourceType
    document_types: _containers.RepeatedScalarFieldContainer[str]
    include_deleted: bool
    source_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, source_id: _Optional[str] = ..., source_type: _Optional[_Union[_access_tokens_pb2.SourceType, str]] = ..., document_types: _Optional[_Iterable[str]] = ..., include_deleted: bool = ..., source_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class ListDocumentsResponse(_message.Message):
    __slots__ = ("documents",)
    DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    documents: _containers.RepeatedCompositeFieldContainer[Document]
    def __init__(self, documents: _Optional[_Iterable[_Union[Document, _Mapping]]] = ...) -> None: ...

class Document(_message.Message):
    __slots__ = ("id", "uuid", "source_type", "source_id", "document_type", "file_size", "sha256_checksum", "content_type", "json_metadata", "filename", "remote_url", "s3_key", "uploaded_by_user_id", "uploaded_by_user_role", "created_at", "deleted_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    SHA256_CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    JSON_METADATA_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    REMOTE_URL_FIELD_NUMBER: _ClassVar[int]
    S3_KEY_FIELD_NUMBER: _ClassVar[int]
    UPLOADED_BY_USER_ID_FIELD_NUMBER: _ClassVar[int]
    UPLOADED_BY_USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    DELETED_AT_FIELD_NUMBER: _ClassVar[int]
    id: int
    uuid: str
    source_type: _access_tokens_pb2.SourceType
    source_id: str
    document_type: str
    file_size: int
    sha256_checksum: str
    content_type: str
    json_metadata: str
    filename: str
    remote_url: str
    s3_key: str
    uploaded_by_user_id: int
    uploaded_by_user_role: str
    created_at: _timestamp_pb2.Timestamp
    deleted_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[int] = ..., uuid: _Optional[str] = ..., source_type: _Optional[_Union[_access_tokens_pb2.SourceType, str]] = ..., source_id: _Optional[str] = ..., document_type: _Optional[str] = ..., file_size: _Optional[int] = ..., sha256_checksum: _Optional[str] = ..., content_type: _Optional[str] = ..., json_metadata: _Optional[str] = ..., filename: _Optional[str] = ..., remote_url: _Optional[str] = ..., s3_key: _Optional[str] = ..., uploaded_by_user_id: _Optional[int] = ..., uploaded_by_user_role: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., deleted_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CombineDocumentsRequest(_message.Message):
    __slots__ = ("source_id", "source_type", "combined_document_type", "disable_document_event_publish", "uploaded_by_user_role")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    COMBINED_DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DISABLE_DOCUMENT_EVENT_PUBLISH_FIELD_NUMBER: _ClassVar[int]
    UPLOADED_BY_USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    source_type: _access_tokens_pb2.SourceType
    combined_document_type: str
    disable_document_event_publish: bool
    uploaded_by_user_role: str
    def __init__(self, source_id: _Optional[str] = ..., source_type: _Optional[_Union[_access_tokens_pb2.SourceType, str]] = ..., combined_document_type: _Optional[str] = ..., disable_document_event_publish: bool = ..., uploaded_by_user_role: _Optional[str] = ...) -> None: ...

class CombineDocumentsByIdsRequest(_message.Message):
    __slots__ = ("ids", "source_id", "source_type", "combined_document_type", "delay_seconds")
    IDS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    COMBINED_DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DELAY_SECONDS_FIELD_NUMBER: _ClassVar[int]
    ids: _containers.RepeatedScalarFieldContainer[int]
    source_id: str
    source_type: str
    combined_document_type: str
    delay_seconds: int
    def __init__(self, ids: _Optional[_Iterable[int]] = ..., source_id: _Optional[str] = ..., source_type: _Optional[str] = ..., combined_document_type: _Optional[str] = ..., delay_seconds: _Optional[int] = ...) -> None: ...

class SplitDocumentRequest(_message.Message):
    __slots__ = ("document_id", "document_splits")
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_SPLITS_FIELD_NUMBER: _ClassVar[int]
    document_id: int
    document_splits: _containers.RepeatedCompositeFieldContainer[DocumentSplit]
    def __init__(self, document_id: _Optional[int] = ..., document_splits: _Optional[_Iterable[_Union[DocumentSplit, _Mapping]]] = ...) -> None: ...

class DocumentSplit(_message.Message):
    __slots__ = ("page_numbers", "document")
    PAGE_NUMBERS_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    page_numbers: _containers.RepeatedScalarFieldContainer[int]
    document: CreateDocumentRequest
    def __init__(self, page_numbers: _Optional[_Iterable[int]] = ..., document: _Optional[_Union[CreateDocumentRequest, _Mapping]] = ...) -> None: ...

class GetDocumentRequest(_message.Message):
    __slots__ = ("id", "uuid", "url_expire_seconds")
    ID_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    URL_EXPIRE_SECONDS_FIELD_NUMBER: _ClassVar[int]
    id: int
    uuid: str
    url_expire_seconds: int
    def __init__(self, id: _Optional[int] = ..., uuid: _Optional[str] = ..., url_expire_seconds: _Optional[int] = ...) -> None: ...

class GetDocumentMetadataResponse(_message.Message):
    __slots__ = ("document",)
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    document: Document
    def __init__(self, document: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...

class GetDocumentResponseChunk(_message.Message):
    __slots__ = ("id", "filename_with_extension", "file_bytes")
    ID_FIELD_NUMBER: _ClassVar[int]
    FILENAME_WITH_EXTENSION_FIELD_NUMBER: _ClassVar[int]
    FILE_BYTES_FIELD_NUMBER: _ClassVar[int]
    id: int
    filename_with_extension: str
    file_bytes: bytes
    def __init__(self, id: _Optional[int] = ..., filename_with_extension: _Optional[str] = ..., file_bytes: _Optional[bytes] = ...) -> None: ...

class DestroyDocumentsRequest(_message.Message):
    __slots__ = ("source_id", "source_type", "document_types", "skip_events")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPES_FIELD_NUMBER: _ClassVar[int]
    SKIP_EVENTS_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    source_type: str
    document_types: _containers.RepeatedScalarFieldContainer[str]
    skip_events: bool
    def __init__(self, source_id: _Optional[str] = ..., source_type: _Optional[str] = ..., document_types: _Optional[_Iterable[str]] = ..., skip_events: bool = ...) -> None: ...

class DestroyDocumentRequest(_message.Message):
    __slots__ = ("id", "uuid")
    ID_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    id: int
    uuid: str
    def __init__(self, id: _Optional[int] = ..., uuid: _Optional[str] = ...) -> None: ...

class GetOriginalDocumentIdsRequest(_message.Message):
    __slots__ = ("combined_document_id",)
    COMBINED_DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    combined_document_id: int
    def __init__(self, combined_document_id: _Optional[int] = ...) -> None: ...

class GetOriginalDocumentIdsResponse(_message.Message):
    __slots__ = ("document_ids",)
    DOCUMENT_IDS_FIELD_NUMBER: _ClassVar[int]
    document_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, document_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class GetPresignedUploadUrlRequest(_message.Message):
    __slots__ = ("filename", "expires_in_secs", "http_method")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_SECS_FIELD_NUMBER: _ClassVar[int]
    HTTP_METHOD_FIELD_NUMBER: _ClassVar[int]
    filename: str
    expires_in_secs: int
    http_method: str
    def __init__(self, filename: _Optional[str] = ..., expires_in_secs: _Optional[int] = ..., http_method: _Optional[str] = ...) -> None: ...

class GetPresignedUploadUrlResponse(_message.Message):
    __slots__ = ("url", "s3_key", "fields")
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    URL_FIELD_NUMBER: _ClassVar[int]
    S3_KEY_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    url: str
    s3_key: str
    fields: _containers.ScalarMap[str, str]
    def __init__(self, url: _Optional[str] = ..., s3_key: _Optional[str] = ..., fields: _Optional[_Mapping[str, str]] = ...) -> None: ...

class RecombineSource(_message.Message):
    __slots__ = ("id", "page_numbers", "rotation")
    ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBERS_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    id: int
    page_numbers: _containers.RepeatedScalarFieldContainer[int]
    rotation: Rotation
    def __init__(self, id: _Optional[int] = ..., page_numbers: _Optional[_Iterable[int]] = ..., rotation: _Optional[_Union[Rotation, str]] = ...) -> None: ...

class RecombineDocument(_message.Message):
    __slots__ = ("source_id", "document_type", "sources")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCES_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    document_type: str
    sources: _containers.RepeatedCompositeFieldContainer[RecombineSource]
    def __init__(self, source_id: _Optional[str] = ..., document_type: _Optional[str] = ..., sources: _Optional[_Iterable[_Union[RecombineSource, _Mapping]]] = ...) -> None: ...

class RecombineDocumentsRequest(_message.Message):
    __slots__ = ("source_type", "new_documents")
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    NEW_DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    source_type: _access_tokens_pb2.SourceType
    new_documents: _containers.RepeatedCompositeFieldContainer[RecombineDocument]
    def __init__(self, source_type: _Optional[_Union[_access_tokens_pb2.SourceType, str]] = ..., new_documents: _Optional[_Iterable[_Union[RecombineDocument, _Mapping]]] = ...) -> None: ...

class CopyDocumentRequest(_message.Message):
    __slots__ = ("uuid", "source_id", "filename")
    UUID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    source_id: str
    filename: str
    def __init__(self, uuid: _Optional[str] = ..., source_id: _Optional[str] = ..., filename: _Optional[str] = ...) -> None: ...

class CopyDocumentResponse(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class TransferDocumentsRequest(_message.Message):
    __slots__ = ("uuids", "source_id", "source_type", "document_type")
    UUIDS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    uuids: _containers.RepeatedScalarFieldContainer[str]
    source_id: str
    source_type: _access_tokens_pb2.SourceType
    document_type: str
    def __init__(self, uuids: _Optional[_Iterable[str]] = ..., source_id: _Optional[str] = ..., source_type: _Optional[_Union[_access_tokens_pb2.SourceType, str]] = ..., document_type: _Optional[str] = ...) -> None: ...

class TransferDocumentsResponse(_message.Message):
    __slots__ = ("documents",)
    DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    documents: _containers.RepeatedCompositeFieldContainer[Document]
    def __init__(self, documents: _Optional[_Iterable[_Union[Document, _Mapping]]] = ...) -> None: ...

class ArchiveDocumentRequest(_message.Message):
    __slots__ = ("uuid", "id", "archive_bucket", "archive_key", "storage_class", "acl")
    UUID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    ARCHIVE_BUCKET_FIELD_NUMBER: _ClassVar[int]
    ARCHIVE_KEY_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CLASS_FIELD_NUMBER: _ClassVar[int]
    ACL_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    id: int
    archive_bucket: str
    archive_key: str
    storage_class: str
    acl: str
    def __init__(self, uuid: _Optional[str] = ..., id: _Optional[int] = ..., archive_bucket: _Optional[str] = ..., archive_key: _Optional[str] = ..., storage_class: _Optional[str] = ..., acl: _Optional[str] = ...) -> None: ...

class ArchiveDocumentResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetDocumentsRequest(_message.Message):
    __slots__ = ("uuids", "ids", "url_expire_seconds", "content_disposition")
    UUIDS_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    URL_EXPIRE_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_DISPOSITION_FIELD_NUMBER: _ClassVar[int]
    uuids: _containers.RepeatedScalarFieldContainer[str]
    ids: _containers.RepeatedScalarFieldContainer[int]
    url_expire_seconds: int
    content_disposition: str
    def __init__(self, uuids: _Optional[_Iterable[str]] = ..., ids: _Optional[_Iterable[int]] = ..., url_expire_seconds: _Optional[int] = ..., content_disposition: _Optional[str] = ...) -> None: ...

class GetDocumentsResponse(_message.Message):
    __slots__ = ("by_uuid", "by_id")
    class ByUuidEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Document
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...
    class ByIdEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: Document
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...
    BY_UUID_FIELD_NUMBER: _ClassVar[int]
    BY_ID_FIELD_NUMBER: _ClassVar[int]
    by_uuid: _containers.MessageMap[str, Document]
    by_id: _containers.MessageMap[int, Document]
    def __init__(self, by_uuid: _Optional[_Mapping[str, Document]] = ..., by_id: _Optional[_Mapping[int, Document]] = ...) -> None: ...
