# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: messages.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'messages.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0emessages.proto\x12\x08messages\"y\n\x18MessageTranscriptionTask\x12\x0f\n\x07task_id\x18\x01 \x01(\t\x12\x10\n\x08\x66ile_url\x18\x02 \x01(\t\x12\x14\n\x0c\x63\x61llback_url\x18\x03 \x01(\t\x12\x12\n\nstart_time\x18\x04 \x01(\x01\x12\x10\n\x08\x65nd_time\x18\x05 \x01(\x01\"M\n\x12MessageConvertTask\x12\x0f\n\x07task_id\x18\x01 \x01(\t\x12\x10\n\x08\x66ile_url\x18\x02 \x01(\t\x12\x14\n\x0c\x63\x61llback_url\x18\x03 \x01(\t\"W\n\x12MessageDiarizeTask\x12\x0f\n\x07task_id\x18\x01 \x01(\t\x12\x1a\n\x12\x63onverted_file_url\x18\x02 \x01(\t\x12\x14\n\x0c\x63\x61llback_url\x18\x03 \x01(\t\"@\n\x07Segment\x12\x0f\n\x07speaker\x18\x01 \x01(\x05\x12\x12\n\nstart_time\x18\x02 \x01(\x01\x12\x10\n\x08\x65nd_time\x18\x03 \x01(\x01\";\n\x14SegmentsTaskResponse\x12#\n\x08segments\x18\x01 \x03(\x0b\x32\x11.messages.Segment\"2\n\x19TranscriptionTaskResponse\x12\x15\n\rtranscription\x18\x01 \x01(\tB\x13Z\x11main/pkg/messagesb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'messages_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z\021main/pkg/messages'
  _globals['_MESSAGETRANSCRIPTIONTASK']._serialized_start=28
  _globals['_MESSAGETRANSCRIPTIONTASK']._serialized_end=149
  _globals['_MESSAGECONVERTTASK']._serialized_start=151
  _globals['_MESSAGECONVERTTASK']._serialized_end=228
  _globals['_MESSAGEDIARIZETASK']._serialized_start=230
  _globals['_MESSAGEDIARIZETASK']._serialized_end=317
  _globals['_SEGMENT']._serialized_start=319
  _globals['_SEGMENT']._serialized_end=383
  _globals['_SEGMENTSTASKRESPONSE']._serialized_start=385
  _globals['_SEGMENTSTASKRESPONSE']._serialized_end=444
  _globals['_TRANSCRIPTIONTASKRESPONSE']._serialized_start=446
  _globals['_TRANSCRIPTIONTASKRESPONSE']._serialized_end=496
# @@protoc_insertion_point(module_scope)
