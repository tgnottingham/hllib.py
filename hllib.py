"""
HLLib is a package library for Half-Life that abstracts several package
formats (e.g. GCF, VPK) and provides a simple interface for all of them.
This module provides access to the underlying C library via Python.

Directions:
    See Package class for information on handling (e.g. opening,
    closing, inspecting) packages.

    See NCFFile and WADFile for information on handling NCF and WAD
    files which is specific to those package types.

    See HLDirectoryItem, HLDirectoryFolder, and HLDirectoryFile for
    information on handling (e.g. validating, extracting) package
    contents.

    See HLStream for information on reading and writing package contents
    using streams.

String arguments:
    Functions taking string arguments may be passed unicode strings. Before
    being passed to the underlying C library, however, the unicode strings
    will be encoded using the type set by the previous call to
    set_unicode_encoding(), or the system default encoding if
    set_unicode_encoding() hasn't been called.

String return values:
    Functions returning strings return unicode strings, which are decoded
    according to the type set by the previous call to
    set_unicode_encoding(), or the system default encoding if
    set_unicode_encoding() hasn't been called.

    The only exception to this is Stream.read_char(), to make it
    consistent with Stream.read().

Buffer arguments:
    Functions taking buffer arguments (for example, HLStream.read() and
    HLStream.write()) should be passed byte-oriented containers such as
    strs (only in Python 2), bytes, bytearrays, or memoryviews thereof in
    Python 3. Functions taking buffers that will be written to should be
    passed mutable byte-oriented containers such as bytearrays.

Custom package functions:
    There is limited support for Package.open_proc(). The functions
    (open, read, write, etc.) can be set using set_value(), but the
    values passed to those functions come directly from the underlying
    C library, and so may be ctypes types.

HL types:
    The following HL type names exist in this module. A subset can be
    passed as the type argument to get_value() and set_value().

    hlBool
    hlChar
    hlWChar
    hlByte
    hlShort
    hlUShort
    hlInt
    hlUInt
    hlLong
    hlULong
    hlLongLong
    hlULongLong
    hlSingle
    hlDouble
    hlUInt8
    hlUInt16
    hlUInt32
    hlUInt64
    hlFloat
    hlString
    hlVoidPtr
"""

import ctypes as _c
import os as _os
import sys as _sys


# Exceptions

class HLError(Exception):
    pass


class HLCancel(Exception):
    pass


# Load HLLib

if _os.name == "posix":
    _hl = _c.cdll.LoadLibrary("libhl.so")
    _callback_factory = _c.CFUNCTYPE
elif _os.name == "nt":
    _hl = _c.windll.HLLib
    _callback_factory = _c.WINFUNCTYPE
else:
    raise HLError("Operating system ({0}) not supported.".format(os.name))


# Defines

HL_VERSION_NUMBER = ((2 << 24) | (4 << 16) | (5 << 8) | 0)
HL_VERSION_STRING = "2.4.5"
HL_ID_INVALID = 0xffffffff
HL_DEFAULT_PACKAGE_TEST_BUFFER_SIZE = 8
HL_DEFAULT_VIEW_SIZE = 131072
HL_DEFAULT_COPY_BUFFER_SIZE = 131072


# Typedefs

# typedef unsigned char	        hlBool;
hlBool = _c.c_ubyte

# typedef char                  hlChar;
hlChar = _c.c_char

# typedef unsigned short        hlWChar;
hlWChar = _c.c_ushort

# typedef unsigned char         hlByte;
hlByte = _c.c_ubyte

# typedef signed short          hlShort;
hlShort = _c.c_short

# typedef unsigned short        hlUShort;
hlUShort = _c.c_ushort

# typedef signed int            hlInt;
hlInt = _c.c_int

# typedef unsigned int          hlUInt;
hlUInt = _c.c_uint

# typedef signed long           hlLong;
hlLong = _c.c_long

# typedef unsigned long         hlULong;
hlULong = _c.c_ulong

# typedef signed long long      hlLongLong;
hlLongLong = _c.c_longlong

# typedef unsigned long long    hlULongLong;
hlULongLong = _c.c_ulonglong

# typedef float                 hlSingle;
hlSingle = _c.c_float

# typedef double                hlDouble;
hlDouble = _c.c_double

# typedef void                  hlVoid;
# No void ctype, only void*.

# typedef uint8_t               hlUInt8;
hlUInt8 = _c.c_uint8

# typedef uint16_t              hlUInt16;
hlUInt16 = _c.c_uint16

# typedef uint32_t              hlUInt32;
hlUInt32 = _c.c_uint32

# typedef uint64_t              hlUInt64;
hlUInt64 = _c.c_uint64

# typedef hlSingle              hlFloat;
hlFloat = hlSingle

# No string typedef in C library.
hlString = _c.c_char_p

# No void* typedef in C library.
hlVoidPtr = _c.c_void_p


# Enumerations

class HLOption(object):
    """Options which can be passed to get_value() and set_value().

    HL_VERSION:
        HLLib version.

    HL_ERROR:
        Last error message.

    HL_ERROR_SYSTEM:
        Last system error value or message.

    HL_ERROR_SHORT_FORMATED:
        Last error and system error, short format.

    HL_ERROR_LONG_FORMATED:
        Last error and system error, long format.

    HL_PROC_OPEN:
        Function to open package when Package.open_proc() is used.

        def open(file_mode, user_data). Returns success/failure boolean.

    HL_PROC_CLOSE:
        Function to close package when Package.open_proc() is used.

        def close(user_data), Returns nothing.

    HL_PROC_READ:
        Function to read from package when Package.open_proc() is used.

        def read(buffer, bytes, user_data). Returns bytes read.

    HL_PROC_WRITE:
        Function to write to package when Package.open_proc() is used.

        def write(buffer, bytes, user_data). Returns bytes written.

    HL_PROC_SEEK:
        Function to seek in package when Package.open_proc() is used.

        def seek(offset, seek_mode, user_data). Returns bytes written.

    HL_PROC_TELL:
        Function to get current position within package when
        Package.open_proc() is used.

        def tell(user_data). Returns position.

    HL_PROC_SIZE:
        Function to get package size when Package.open_proc() is used.

        def size(user_data). Returns size.

    HL_PROC_EXTRACT_ITEM_START:
        Callback to call when starting item extraction.

        def extract_item_start(directory_item). Returns nothing.

    HL_PROC_EXTRACT_ITEM_END:
        Callback to call when finishing item extraction.

        def extract_item_end(directory_item, success). Returns nothing.

    HL_PROC_EXTRACT_FILE_PROGRESS:
        Callback to call periodically during file extraction.

        def extract_file_progress(directory_file, bytes_extracted,
        bytes_total). Returns nothing. Raises HLCancel instance to
        cancel validation.

    HL_PROC_VALIDATE_FILE_PROGRESS:
        Callback to call periodically during file validation.

        def validate_file_progress(directory_file, bytes_validated,
        bytes_total). Returns nothing. Raises HLCancel instance to
        cancel validation.

    HL_OVERWRITE_FILES:
        Whether or not existing files should be overwritten when opened.

    HL_PACKAGE_BOUND:
        Whether or not a package is bound.

    HL_PACKAGE_ID:
        The bound package ID.

    HL_PACKAGE_SIZE:
        The size of the bound package in bytes.

    HL_PACKAGE_TOTAL_ALLOCATIONS:
        Number of views in mapping.

    HL_PACKAGE_TOTAL_MEMORY_ALLOCATED:
        Total memory allocated for mapped package.

    HL_PACKAGE_TOTAL_MEMORY_USED:
        Total memory actually used by mapped package.

    HL_READ_ENCRYPTED:
        Allow reading of encrypted files.

    HL_FORCE_DEFRAGMENT:
        When defragmenting, force sorting of blocks lexicographically
        even if there is no fragmentation.

    HL_PROC_DEFRAGMENT_PROGRESS:
        Callback to call periodically during file defragmentation.

        def defragment_progress(directory_file, files_defragmented,
        files_total, bytes_defragmented, bytes_total). Returns nothing.
        Raises HLCancel instance to cancel defragment.

    HL_PROC_DEFRAGMENT_PROGRESS_EX:
        As with HL_PROC_DEFRAGMENT, but byte values passed to callback
        are of larger type.

    HL_PROC_SEEK_EX:
        As with HL_PROC_SEEK, but return value is larger type.

    HL_PROC_TELL_EX:
        As with HL_PROC_TELL, but return value is larger type.

    HL_PROC_SIZE_EX:
        As with HL_PROC_SIZE, but return value is larger type.
    """
    HL_VERSION = 0
    HL_ERROR = 1
    HL_ERROR_SYSTEM = 2
    HL_ERROR_SHORT_FORMATED = 3
    HL_ERROR_LONG_FORMATED = 4
    HL_PROC_OPEN = 5
    HL_PROC_CLOSE = 6
    HL_PROC_READ = 7
    HL_PROC_WRITE = 8
    HL_PROC_SEEK = 9
    HL_PROC_TELL = 10
    HL_PROC_SIZE = 11
    HL_PROC_EXTRACT_ITEM_START = 12
    HL_PROC_EXTRACT_ITEM_END = 13
    HL_PROC_EXTRACT_FILE_PROGRESS = 14
    HL_PROC_VALIDATE_FILE_PROGRESS = 15
    HL_OVERWRITE_FILES = 16
    HL_PACKAGE_BOUND = 17
    HL_PACKAGE_ID = 18
    HL_PACKAGE_SIZE = 19
    HL_PACKAGE_TOTAL_ALLOCATIONS = 20
    HL_PACKAGE_TOTAL_MEMORY_ALLOCATED = 21
    HL_PACKAGE_TOTAL_MEMORY_USED = 22
    HL_READ_ENCRYPTED = 23
    HL_FORCE_DEFRAGMENT = 24
    HL_PROC_DEFRAGMENT_PROGRESS = 25
    HL_PROC_DEFRAGMENT_PROGRESS_EX = 26
    HL_PROC_SEEK_EX = 27
    HL_PROC_TELL_EX = 28
    HL_PROC_SIZE_EX = 29


class HLFileMode(object):
    """File mode.

    Multiple modes can be specified by bitwise OR-ing modes.

    Attributes:
        HL_MODE_INVALID:
            Invalid value.

        HL_MODE_READ:
            Allow reading from file.

        HL_MODE_WRITE:
            Allow writing to file.

        HL_MODE_CREATE:
            Depends on HLOption HL_OVERWRITE_FILES. If set, then always
                create a new file, even if it exists. Otherwise, only
                create the file if it does not exist.

        HL_MODE_VOLATILE:
            Allow opening file while it is opened for writing by another
                process.

        HL_MODE_NO_FILEMAPPING:
            Disable filemapping. Filemapping is recommended as an
                efficient way to load packages.

        HL_MODE_QUICK_FILEMAPPING:
            Map the entire file instead of bits as they are needed. May
                not be supported on some operating systems.
    """
    HL_MODE_INVALID = 0x00
    HL_MODE_READ = 0x01
    HL_MODE_WRITE = 0x02
    HL_MODE_CREATE = 0x04
    HL_MODE_VOLATILE = 0x08
    HL_MODE_NO_FILEMAPPING = 0x10
    HL_MODE_QUICK_FILEMAPPING = 0x20


class HLSeekMode(object):
    """Seek mode.

    Attributes:
        HL_SEEK_BEGINNING:
            Seek offset interpreted relative to beginning of stream.

        HL_SEEK_CURRENT:
            Seek offset interpreted relative to current position.

        HL_SEEK_END:
            Seek offste interpreted relative to end of stream.
    """
    HL_SEEK_BEGINNING = 0
    HL_SEEK_CURRENT = 1
    HL_SEEK_END = 2


class HLDirectoryItemType(object):
    """HLDirectoryItem type.

    Attributes:
        HL_ITEM_NONE:
            Invalid value.

        HL_ITEM_FOLDER:
            Item is an HLDirectoryFolder.

        HL_ITEM_FILE:
            Item is an HLDirectoryItemk
    """
    HL_ITEM_NONE = 0
    HL_ITEM_FOLDER = 1
    HL_ITEM_FILE = 2


class HLSortOrder(object):
    """Sort order.

    Attributes:
        HL_ORDER_ASCENDING:
            Order results from least to greatest.

        HL_ORDER_DESCENDING:
            Order results from greatest to least.
    """
    HL_ORDER_ASCENDING = 0
    HL_ORDER_DESCENDING = 1


class HLSortField(object):
    """Sort field.

    Attributes:
        HL_FIELD_NAME:
            Sort by name.

        HL_FIELD_SIZE:
            Sort by size.
    """
    HL_FIELD_NAME = 0
    HL_FIELD_SIZE = 1


class HLFindType(object):
    """Find mode.

    Attributes:
        HL_FIND_FILES:
            Find files.

        HL_FIND_FOLDERS:
            Find folders.

        HL_FIND_NO_RECURSE:
            Do not find results in subdirectories.

        HL_FIND_CASE_SENSITIVE:
            Find results using case-sensitive match.

        HL_FIND_MODE_STRING:
            Find results matching entire search string.

        HL_FIND_MODE_SUBSTRING:
            Find results containing search string.

        HL_FIND_MODE_WILDCARD:
            Find using wildcards (e.g. * and ?).

        HL_FIND_ALL:
            Find both files and folders.
    """
    HL_FIND_FILES = 0x01
    HL_FIND_FOLDERS = 0x02
    HL_FIND_NO_RECURSE = 0x04
    HL_FIND_CASE_SENSITIVE = 0x08
    HL_FIND_MODE_STRING = 0x10
    HL_FIND_MODE_SUBSTRING = 0x20
    HL_FIND_MODE_WILDCARD = 0x00
    HL_FIND_ALL = HL_FIND_FILES | HL_FIND_FOLDERS


class HLStreamType(object):
    """Stream type.

    Attributes:
        HL_STREAM_NONE:
            Invalid value.

        HL_STREAM_FILE:
            Stream associated with non-specific file.

        HL_STREAM_GCF:
            Stream associated with GCF file.

        HL_STREAM_MAPPING:
            Stream associated with mapped file.

        HL_STREAM_MEMORY:
            Stream associated with memory buffer.

        HL_STREAM_PROC:
            Stream associated with procedures. Procedures are set using
                set_value() with HLOptions, e.g. HL_PROC_READ.

        HL_STREAM_NULL:
            Stream associated with empty data.
    """
    HL_STREAM_NONE = 0
    HL_STREAM_FILE = 1
    HL_STREAM_GCF = 2
    HL_STREAM_MAPPING = 3
    HL_STREAM_MEMORY = 4
    HL_STREAM_PROC = 5
    HL_STREAM_NULL = 6


class HLMappingType(object):
    """Mapping type.

    Attributes:
        HL_MAPPING_NONE:
            Invalid value.

        HL_MAPPING_FILE:
            Mapping of file to memory.

        HL_MAPPING_MEMORY:
            Mapping interface to memory.

        HL_MAPPING_STREAM:
            Mapping interface to stream.
    """
    HL_MAPPING_NONE = 0
    HL_MAPPING_FILE = 1
    HL_MAPPING_MEMORY = 2
    HL_MAPPING_STREAM = 3


class HLPackageType(object):
    """Package type.

    Attribute:
        HL_PACKAGE_NONE:
            Invalid value.

        HL_PACKAGE_BSP:
            Binary Space Partition file.

        HL_PACKAGE_GCF:
            Game Cache File.

        HL_PACKAGE_PAK:
            Package file.

        HL_PACKAGE_VBSP:
            VBSP file.

        HL_PACKAGE_WAD:
            Where's All the Data file.

        HL_PACKAGE_XZP:
            XBOX Zip file.

        HL_PACKAGE_ZIP:
            Zip file.

        HL_PACKAGE_NCF:
            No Cache File.

        HL_PACKAGE_VPK:
            Valve Package file.

        HL_PACKAGE_SGA:
            Game Archive file.
    """
    HL_PACKAGE_NONE = 0
    HL_PACKAGE_BSP = 1
    HL_PACKAGE_GCF = 2
    HL_PACKAGE_PAK = 3
    HL_PACKAGE_VBSP = 4
    HL_PACKAGE_WAD = 5
    HL_PACKAGE_XZP = 6
    HL_PACKAGE_ZIP = 7
    HL_PACKAGE_NCF = 8
    HL_PACKAGE_VPK = 9
    HL_PACKAGE_SGA = 10


class HLAttributeType(object):
    """HLAttribute value's type.

    Attribute:
        HL_ATTRIBUTE_INVALID:
            Invalid value.

        HL_ATTRIBUTE_BOOLEAN:
            Boolean value.

        HL_ATTRIBUTE_INTEGER:
            Integer value.

        HL_ATTRIBUTE_UNSIGNED_INTEGER:
            Unsigned integer value.

        HL_ATTRIBUTE_FLOAT:
            Floating point value.

        HL_ATTRIBUTE_STRING:
            String value.
    """
    HL_ATTRIBUTE_INVALID = 0
    HL_ATTRIBUTE_BOOLEAN = 1
    HL_ATTRIBUTE_INTEGER = 2
    HL_ATTRIBUTE_UNSIGNED_INTEGER = 3
    HL_ATTRIBUTE_FLOAT = 4
    HL_ATTRIBUTE_STRING = 5


class HLPackageAttribute(object):
    HL_BSP_PACKAGE_VERSION = 0
    HL_BSP_PACKAGE_COUNT = 1
    HL_BSP_ITEM_WIDTH = 0
    HL_BSP_ITEM_HEIGHT = 1
    HL_BSP_ITEM_PALETTE_ENTRIES = 2
    HL_BSP_ITEM_COUNT = 3

    HL_GCF_PACKAGE_VERSION = 0
    HL_GCF_PACKAGE_ID = 1
    HL_GCF_PACKAGE_ALLOCATED_BLOCKS = 2
    HL_GCF_PACKAGE_USED_BLOCKS = 3
    HL_GCF_PACKAGE_BLOCK_LENGTH = 4
    HL_GCF_PACKAGE_LAST_VERSION_PLAYED = 5
    HL_GCF_PACKAGE_COUNT = 6
    HL_GCF_ITEM_ENCRYPTED = 0
    HL_GCF_ITEM_COPY_LOCAL = 1
    HL_GCF_ITEM_OVERWRITE_LOCAL = 2
    HL_GCF_ITEM_BACKUP_LOCAL = 3
    HL_GCF_ITEM_FLAGS = 4
    HL_GCF_ITEM_FRAGMENTATION = 5
    HL_GCF_ITEM_COUNT = 6

    HL_NCF_PACKAGE_VERSION = 0
    HL_NCF_PACKAGE_ID = 1
    HL_NCF_PACKAGE_LAST_VERSION_PLAYED = 2
    HL_NCF_PACKAGE_COUNT = 3
    HL_NCF_ITEM_ENCRYPTED = 0
    HL_NCF_ITEM_COPY_LOCAL = 1
    HL_NCF_ITEM_OVERWRITE_LOCAL = 2
    HL_NCF_ITEM_BACKUP_LOCAL = 3
    HL_NCF_ITEM_FLAGS = 4
    HL_NCF_ITEM_COUNT = 5

    HL_PAK_PACKAGE_COUNT = 0
    HL_PAK_ITEM_COUNT = 0

    HL_SGA_PACKAGE_VERSION_MAJOR = 0
    HL_SGA_PACKAGE_VERSION_MINOR = 1
    HL_SGA_PACKAGE_MD5_FILE = 2
    HL_SGA_PACKAGE_NAME = 3
    HL_SGA_PACKAGE_MD5_HEADER = 4
    HL_SGA_PACKAGE_COUNT = 5
    HL_SGA_ITEM_SECTION_ALIAS = 0
    HL_SGA_ITEM_SECTION_NAME = 1
    HL_SGA_ITEM_MODIFIED = 2
    HL_SGA_ITEM_TYPE = 3
    HL_SGA_ITEM_CRC = 4
    HL_SGA_ITEM_VERIFICATION = 5
    HL_SGA_ITEM_COUNT = 6

    HL_VBSP_PACKAGE_VERSION = 0
    HL_VBSP_PACKAGE_MAP_REVISION = 1
    HL_VBSP_PACKAGE_COUNT = 2
    HL_VBSP_ITEM_VERSION = 0
    HL_VBSP_ITEM_FOUR_CC = 1
    HL_VBSP_ZIP_PACKAGE_DISK = 2
    HL_VBSP_ZIP_PACKAGE_COMMENT = 3
    HL_VBSP_ZIP_ITEM_CREATE_VERSION = 4
    HL_VBSP_ZIP_ITEM_EXTRACT_VERSION = 5
    HL_VBSP_ZIP_ITEM_FLAGS = 6
    HL_VBSP_ZIP_ITEM_COMPRESSION_METHOD = 7
    HL_VBSP_ZIP_ITEM_CRC = 8
    HL_VBSP_ZIP_ITEM_DISK = 9
    HL_VBSP_ZIP_ITEM_COMMENT = 10
    HL_VBSP_ITEM_COUNT = 11

    HL_VPK_PACKAGE_Archives = 0
    HL_VPK_PACKAGE_Version = 1
    HL_VPK_PACKAGE_COUNT = 2
    HL_VPK_ITEM_PRELOAD_BYTES = 0
    HL_VPK_ITEM_ARCHIVE = 1
    HL_VPK_ITEM_CRC = 2
    HL_VPK_ITEM_COUNT = 3

    HL_WAD_PACKAGE_VERSION = 0
    HL_WAD_PACKAGE_COUNT = 1
    HL_WAD_ITEM_WIDTH = 0
    HL_WAD_ITEM_HEIGHT = 1
    HL_WAD_ITEM_PALETTE_ENTRIES = 2
    HL_WAD_ITEM_MIPMAPS = 3
    HL_WAD_ITEM_COMPRESSED = 4
    HL_WAD_ITEM_TYPE = 5
    HL_WAD_ITEM_COUNT = 6

    HL_XZP_PACKAGE_VERSION = 0
    HL_XZP_PACKAGE_PRELOAD_BYTES = 1
    HL_XZP_PACKAGE_COUNT = 2
    HL_XZP_ITEM_CREATED = 0
    HL_XZP_ITEM_PRELOAD_BYTES = 1
    HL_XZP_ITEM_COUNT = 2

    HL_ZIP_PACKAGE_DISK = 0
    HL_ZIP_PACKAGE_COMMENT = 1
    HL_ZIP_PACKAGE_COUNT = 2
    HL_ZIP_ITEM_CREATE_VERSION = 0
    HL_ZIP_ITEM_EXTRACT_VERSION = 1
    HL_ZIP_ITEM_FLAGS = 2
    HL_ZIP_ITEM_COMPRESSION_METHOD = 3
    HL_ZIP_ITEM_CRC = 4
    HL_ZIP_ITEM_DISK = 5
    HL_ZIP_ITEM_COMMENT = 6
    HL_ZIP_ITEM_COUNT = 7


class HLValidation(object):
    """Validation result.

    Attributes:
        HL_VALIDATES_OK:
            File is valid.

        HL_VALIDATES_ASSUMED_OK:
            Validating is not possible, but file is assumed to be valid.

        HL_VALIDATES_INCOMPLETE:
            File is incomplete.

        HL_VALIDATES_CORRUPT:
            File is corrupt.

        HL_VALIDATES_CANCELED:
            Validation was canceled (e.g. by progress callback).

        HL_VALIDATES_ERROR:
            An error occurred during validation.
    """
    HL_VALIDATES_OK = 0
    HL_VALIDATES_ASSUMED_OK = 1
    HL_VALIDATES_INCOMPLETE = 2
    HL_VALIDATES_CORRUPT = 3
    HL_VALIDATES_CANCELED = 4
    HL_VALIDATES_ERROR = 5


# Classes

class Value(_c.Union):
    class Boolean(_c.Structure):
        _fields_ = [("value", hlBool)]

    class Integer(_c.Structure):
        _fields_ = [("value", hlInt)]

    class UnsignedInteger(_c.Structure):
        _fields_ = [
            ("value", hlUInt),
            ("hexadecimal", hlBool)
        ]

    class Float(_c.Structure):
        _fields_ = [("value", hlFloat)]

    class String(_c.Structure):
        _fields_ = [("value", hlChar * 256)]

    _fields_ = [
        ("Boolean", Boolean),
        ("Integer", Integer),
        ("UnsignedInteger", UnsignedInteger),
        ("Float", Float),
        ("String", String),
    ]


class HLAttribute(_c.Structure):
    """A named value of variable type."""

    _fields_ = [
        ("_attribute_type", hlInt),
        ("_name", hlChar * 252),
        ("_value", Value),
    ]

    def get_hexadecimal(self):
        """Returns whether or not hex flag is set for uint typed value.

        Returns:
            Whether or not hexadecimal flag is set for unsigned integer
            typed value.

        Raises:
            HLError: If the object's attribute_type is not
                HL_ATTRIBUTE_UNSIGNED_INTEGER.
        """
        if self.get_type() == HLAttributeType.HL_ATTRIBUTE_UNSIGNED_INTEGER:
            return self._value.UnsignedInteger.hexadecimal

        raise HLError("Cannot call get_hexadecimal() on an attribute "
                "that is not an unsigned integer type.")

    def get_type(self):
        """Returns the HLAttributeType of the attribute."""
        return self._attribute_type

    def get_name(self):
        """Returns the name of the attribute."""
        return self._name.decode(_unicode_encoding)

    def set_name(self, name):
        """Sets the name of the attribute."""
        name = _encode(name)
        self._name = name

    def get(self):
        """Returns the value of the attribute.

        Returns:
            The value of the attribute.

        Raises:
            HLError: If the object's attribute_type is
                HL_ATTRIBUTE_INVALID or not a value in HLAttributeType.
        """
        hlat = HLAttributeType

        if self.get_type() == hlat.HL_ATTRIBUTE_BOOLEAN:
            return bool(_hl.hlAttributeGetBoolean(_c.byref(self)))
        elif self.get_type() == hlat.HL_ATTRIBUTE_INTEGER:
            return _hl.hlAttributeGetInteger(_c.byref(self))
        elif (self.get_type() == hlat.HL_ATTRIBUTE_UNSIGNED_INTEGER):
            return _hl.hlAttributeGetUnsignedInteger(_c.byref(self))
        elif self.get_type() == hlat.HL_ATTRIBUTE_FLOAT:
            return _hl.hlAttributeGetFloat(_c.byref(self))
        elif self.get_type() == hlat.HL_ATTRIBUTE_STRING:
            string = _hl.hlAttributeGetString(_c.byref(self))
            return string.decode(_unicode_encoding)
        elif self.get_type() == hlat.HL_ATTRIBUTE_INVALID:
            raise HLError("HLAttribute's type is invalid.")
        else:
            raise HLError("HLAttribute's type is unknown.")

    def set(self, value, attribute_type=None, hexadecimal=False):
        """Sets the value of the attribute.

        Args:
            value: Value to set attribute to. Attribute type is derived
                from value type unless attribute_type argument is set.

            attribute_type: Specific HLAttributeType to set attribute
                value as. Useful for setting type to unsigned integer
                because Python has no unsigned integer type.

            hexadecimal: Whether or not hexadecimal flag should be set
                for unsigned integer typed values.

        Raises:
            HLError: If attribute_type is HL_ATTRIBUTE_UNSIGNED_INTEGER
                and the value is not an unsigned integer. Or if the
                attribute_type is HL_ATTRIBUTE_INVALID or not a value
                in HLAttributeType.
        """
        hlat = HLAttributeType

        if (attribute_type == hlat.HL_ATTRIBUTE_BOOLEAN or
                (attribute_type is None and isinstance(value, bool))):
            _hl.hlAttributeSetBoolean(_c.byref(self), None, value)

        elif (attribute_type == hlat.HL_ATTRIBUTE_INTEGER or
                (attribute_type is None and isinstance(value, int))):
            _hl.hlAttributeSetInteger(_c.byref(self), None, value)

        elif attribute_type == hlat.HL_ATTRIBUTE_UNSIGNED_INTEGER:
            if value < 0:
                raise HLError("Cannot set HLAttribute's "
                        "unsigned value to negative number.")
            _hl.hlAttributeSetUnsignedInteger(
                    _c.byref(self), None, value, hexadecimal)

        elif (attribute_type == hlat.HL_ATTRIBUTE_FLOAT or
                (attribute_type is None and isinstance(value, float))):
            _hl.hlAttributeSetFloat(_c.byref(self), None, value)

        elif (attribute_type == hlat.HL_ATTRIBUTE_STRING or
                (attribute_type is None and isinstance(value, basestring))):
            value = _encode(value)
            _hl.hlAttributeSetString(_c.byref(self), None, value)

        elif attribute_type == hlat.HL_ATTRIBUTE_INVALID:
            raise HLError("Cannot set HLAttribute value to invalid type.")

        else:
            raise HLError("Cannot set HLAttribute value to unsupported type.")


def _hl_directory_instance(handle):
    if handle is None:
        raise HLError("Cannot create directory item "
                "instance from empty handle.")

    item_type = _hl.hlItemGetType(handle)

    if item_type == HLDirectoryItemType.HL_ITEM_NONE:
        raise HLError("Cannot create directory item "
                "instance from indeterminate item type.")
    elif item_type == HLDirectoryItemType.HL_ITEM_FOLDER:
        return HLDirectoryFolder(handle)
    elif item_type == HLDirectoryItemType.HL_ITEM_FILE:
        return HLDirectoryFile(handle)


class HLDirectoryItem(object):
    """Represents a file or folder within a package."""

    @classmethod
    def from_param(cls, obj):
        if not isinstance(obj, hlVoidPtr):
            raise HLError()
        return self._as_parameter_

    def __init__(self, handle):
        """Initializes instance with handle to underlying item."""
        self._as_parameter_ = handle

    # HLDirectoryItemType hlItemGetType(const HLDirectoryItem *pItem);
    def get_type(self):
        """Returns the item's HLDirectoryItemType."""
        return _hl.hlItemGetType(self)

    # const hlChar *hlItemGetName(const HLDirectoryItem *pItem);
    def get_name(self):
        """Returns the item's name."""
        return _hl.hlItemGetName(self).decode(_unicode_encoding)

    # const hlVoid *hlItemGetData(const HLDirectoryItem *pItem);
    def get_data(self):
        """Returns the item's data address."""
        return _hl.hlItemGetData(self)

    # hlUInt hlItemGetID(const HLDirectoryItem *pItem);
    def get_id(self):
        """Returns the item's ID."""
        return _hl.hlItemGetID(self)

    # hlUInt hlItemGetPackage(const HLDirectoryItem *pItem);
    def get_package(self):
        """Returns the ID of the containing package."""
        return _hl.hlItemGetPackage(self)

    # HLDirectoryItem *hlItemGetParent(HLDirectoryItem *pItem);
    def get_parent(self):
        """Returns the item's parent directory."""
        # A null pointer (None) is valid. It indicates no parent.
        item = _hl.hlItemGetParent(self)
        return None if item is None else _hl_directory_instance(item)

    # hlVoid hlItemGetPath(const HLDirectoryItem *pItem,
    #       hlChar *lpPath, hlUInt uiPathSize);
    def get_path(self):
        """Returns the item's path."""
        buf_size = 1024
        buf = _c.create_string_buffer(buf_size)
        _hl.hlItemGetPath(self, buf, buf_size)
        return buf.value.decode(_unicode_encoding)

    # hlBool hlItemExtract(HLDirectoryItem *pItem, const hlChar *lpPath);
    def extract(self, path):
        """Extracts the item to the given directory.

        Args:
            path: The path of the directory to extract to.

        Raises:
            HLError: If there is an error extracting the item.
        """
        path = _encode(path)
        if not _hl.hlItemExtract(self, path):
            raise HLError("Failed to extract {0}.".format(path))


class HLDirectoryFolder(HLDirectoryItem):
    """Represents a folder within a package."""

    @classmethod
    def from_param(cls, obj):
        if not isinstance(obj, hlVoidPtr):
            raise HLError()
        return self._as_parameter_

    def __init__(self, handle):
        """Initializes instance with handle to underlying item."""
        super(HLDirectoryFolder, self).__init__(handle)
        assert self.get_type() == HLDirectoryItemType.HL_ITEM_FOLDER

    # hlUInt hlFolderGetCount(const HLDirectoryItem *pItem);
    def get_count(self):
        """Returns the number of items in the directory."""
        return _hl.hlFolderGetCount(self)

    # HLDirectoryItem *hlFolderGetItem(HLDirectoryItem *pItem, hlUInt uiIndex);
    def get_item(self, index):
        """Returns the item at the given index in the directory.

        Args:
            index: The index of the item in the directory. The valid
                values for index are 0 to get_count() - 1.

        Returns:
            The item at the given index in the directory.

        Raises:
            HLError: If the index is invalid. Or if there is an error
                retrieving the item for any reason.
        """
        item = _hl.hlFolderGetItem(self, index)

        if item is None:
            raise HLError("Failed to get item from "
                    "folder at index {0}".format(index))

        return _hl_directory_instance(item)

    # HLDirectoryItem *hlFolderGetItemByName(HLDirectoryItem *pItem,
    #       const hlChar *lpName, HLFindType eFind);
    def get_item_by_name(self, name, find_type):
        """Returns the item in the directory with the given name."""
        name = _encode(name)
        item = _hl.hlFolderGetItemByName(self, name, find_type)
        return None if item is None else _hl_directory_instance(item)

    # HLDirectoryItem *hlFolderGetItemByPath(HLDirectoryItem *pItem,
    #       const hlChar *lpPath, HLFindType eFind);
    def get_item_by_path(self, path, find_type):
        """Returns the item in the directory with the given path."""
        path = _encode(path)
        item = _hl.hlFolderGetItemByPath(self, path, find_type)
        return None if item is None else _hl_directory_instance(item)

    # hlVoid hlFolderSort(HLDirectoryItem *pItem,
    #       HLSortField eField, HLSortOrder eOrder, hlBool bRecurse);
    def sort(self, sort_field, sort_order, recurse):
        """Sorts the items in the directory.

        Args:
            sort_field: Which field to sort on (see HLSortField).

            sort_order: What order to sort in (see HLSortOrder).
            recurse: Whether or not to sort subdirectories.
        """
        _hl.hlFolderSort(self, sort_field, sort_order, recurse)

    # HLDirectoryItem *hlFolderFindFirst(HLDirectoryItem *pFolder,
    #       const hlChar *lpSearch, HLFindType eFind);
    def find_first(self, pattern, find_type):
        """Returns first item in directory whose name matches pattern."""
        pattern = _encode(pattern)
        item = _hl.hlFolderFindFirst(self, pattern, find_type)
        return None if item is None else _hl_directory_instance(item)

    # HLDirectoryItem *hlFolderFindNext(HLDirectoryItem *pFolder,
    #       HLDirectoryItem *pItem, const hlChar *lpSearch, HLFindType eFind);
    def find_next(self, item, pattern, find_type):
        """Returns next item in directory whose name matches pattern."""
        pattern = _encode(pattern)
        item = _hl.hlFolderFindNext(self, item, pattern, find_type)
        return None if item is None else _hl_directory_instance(item)

    # hlUInt hlFolderGetSize(const HLDirectoryItem *pItem, hlBool bRecurse);
    def get_size(self, recurse):
        """Returns the size of the directory's contents in memory.

        Args:
            recurse: Whether or not to include size of subdirectories.
        """
        return _hl.hlFolderGetSizeEx(self, recurse)

    # hlUInt hlFolderGetSizeOnDisk(const HLDirectoryItem *pItem,
    #       hlBool bRecurse);
    def get_size_on_disk(self, recurse):
        """Returns the size of the directory's contents on disk.

        Args:
            recurse: Whether or not to include size of subdirectories.
        """
        return _hl.hlFolderGetSizeOnDiskEx(self, recurse)

    # hlUInt hlFolderGetFolderCount(const HLDirectoryItem *pItem,
    #       hlBool bRecurse);
    def get_folder_count(self, recurse):
        """Returns the number of folders in the directory."""
        return _hl.hlFolderGetFolderCount(self, recurse)

    # hlUInt hlFolderGetFileCount(const HLDirectoryItem *pItem,
    #       hlBool bRecurse);
    def get_file_count(self, recurse):
        """Returns the number of files in the directory."""
        return _hl.hlFolderGetFileCount(self, recurse)


class HLDirectoryFile(HLDirectoryItem):
    """Represents a file within a package."""

    @classmethod
    def from_param(cls, obj):
        if not isinstance(obj, hlVoidPtr):
            raise HLError()
        return self._as_parameter_

    def __init__(self, handle):
        """Initializes instance with handle to underlying item."""
        super(HLDirectoryFile, self).__init__(handle)
        assert self.get_type() == HLDirectoryItemType.HL_ITEM_FILE

    # hlUInt hlFileGetExtractable(const HLDirectoryItem *pItem);
    def get_extractable(self):
        """Returns whether or not this file is extractable."""
        return _hl.hlFileGetExtractable(self)

    # HLValidation hlFileGetValidation(const HLDirectoryItem *pItem);
    def get_validation(self):
        """Returns file's validation value."""
        return _hl.hlFileGetValidation(self)

    # hlUInt hlFileGetSize(const HLDirectoryItem *pItem);
    def get_size(self):
        """Returns the size of the file's contents in memory."""
        return _hl.hlFileGetSize(self)

    # hlUInt hlFileGetSizeOnDisk(const HLDirectoryItem *pItem);
    def get_size_on_disk(self):
        """Returns the size of the file's contents on disk."""
        return _hl.hlFileGetSizeOnDisk(self)

    # hlBool hlFileCreateStream(HLDirectoryItem *pItem, HLStream **pStream);
    def create_stream(self):
        """Returns a stream for this file.

        The stream can be used to, for example, read from the file.

        Returns:
            A stream for this file.

        Raises:
            HLError: If there is an error creating the stream.
        """
        pointer = hlVoidPtr()

        if not _hl.hlFileCreateStream(self, _c.byref(pointer)):
            raise HLError("Failed to create stream from "
                    "file at {0}.".format(self.get_path()))

        return HLStream(pointer)

    # hlVoid hlFileReleaseStream(HLDirectoryItem *pItem, HLStream *pStream);
    def release_stream(self, stream):
        """Releases the given stream for this file."""
        _hl.hlFileReleaseStream(self, stream)


class HLStream(object):
    """Stream interface for interacting with data in various formats."""

    @classmethod
    def from_param(cls, obj):
        if not isinstance(obj, hlVoidPtr):
            raise HLError()
        return self._as_parameter_

    def __init__(self, handle):
        """Initializes instance with handle to underlying item."""
        self._as_parameter_ = handle

    # HLStreamType hlStreamGetType(const HLStream *pStream);
    def get_type(self):
        """Returns stream's type (see HLStreamType)."""
        return _hl.hlStreamGetType(self)

    # hlBool hlStreamGetOpened(const HLStream *pStream);
    def get_opened(self):
        """Returns whether or not stream is open."""
        return _hl.hlStreamGetOpened(self)

    # hlUInt hlStreamGetMode(const HLStream *pStream);
    def get_mode(self):
        """Returns mode stream was opened with."""
        return _hl.hlStreamGetMode(self)

    # hlBool hlStreamOpen(HLStream *pStream, hlUInt uiMode);
    def open(self, file_mode):
        """Opens stream.

        Args:
            file_mode: The mode(s) with which to open the file.
                See HLFileMode.

        Raises:
            HLError: If there is an error opening the stream.
        """
        if not _hl.hlStreamOpen(self, file_mode):
            raise HLError("Failed to open stream.")

    # hlVoid hlStreamClose(HLStream *pStream);
    def close(self):
        """Closes stream."""
        _hl.hlStreamClose(self)

    # hlUInt hlStreamGetStreamSize(const HLStream *pStream);
    def get_stream_size(self):
        """Returns stream's size."""
        return _hl.hlStreamGetStreamSizeEx(self)

    # hlUInt hlStreamGetStreamPointer(const HLStream *pStream);
    def get_stream_pointer(self):
        """Returns stream's current position."""
        return _hl.hlStreamGetStreamPointerEx(self)

    # hlUInt hlStreamSeek(HLStream *pStream,
    #       hlLongLong iOffset, HLSeekMode eSeekMode);
    def seek(self, offset, seek_mode):
        """Seeks to position in stream."""
        return _hl.hlStreamSeekEx(self, offset, seek_mode)

    # hlBool hlStreamReadChar(HLStream *pStream, hlChar *pChar);
    def read_char(self):
        """Reads a character from the stream.

        Returns:
            The character read from the stream.

        Raises:
            HLError: If there is an error reading the stream.
        """
        char = hlChar()

        if not _hl.hlStreamReadChar(self, _c.byref(char)):
            raise HLError("Failed to read character "
                    "from stream or reached EOF.")

        return char.value

    # hlUInt hlStreamRead(HLStream *pStream, hlVoid *lpData, hlUInt uiBytes);
    def read(self, buf=None, n=1024):
        """Reads a number of bytes from the stream.

        Args:
            buf: A buffer to read into. If None, a buffer of size n will
                be created for the caller.

            n: The maximum number of bytes to read.

        Returns:
            A tuple of the number of bytes read, and the buffer the
            bytes were read into (which will be the passed in buffer
            if it was not None).

        Raises:
            HLError: If buf is not None and len(buf) < n.

        """
        if buf is None:
            buf = bytearray(n)

        c_buf = (_c.c_byte * n).from_buffer(buf)
        bytes_read = _hl.hlStreamRead(self, c_buf, n)

        return bytes_read, buf

    # hlBool hlStreamWriteChar(HLStream *pStream, hlChar iChar);
    def write_char(self, char):
        """Writes a character to the stream.

        Args:
            char: The character to write to the stream.

        Raises:
            HLError: If there is an error writing the stream.
        """
        if not _hl.hlStreamWriteChar(self, char):
            raise HLError("Failed to write character to stream.")

    # hlUInt hlStreamWrite(HLStream *pStream,
    #       const hlVoid *lpData, hlUInt uiBytes);
    def write(self, buf, n):
        """Writes a number of bytes to the stream.

        Args:
            buf: A buffer to write from.

            n: The maximum number of bytes to write.

        Returns:
            The number of bytes written.
        """
        c_buf = _get_const_compatible_buffer(buf, n)
        return _hl.hlStreamWrite(self, c_buf, n)


class Package(object):
    """A collection of static methods for dealing with packages.

    See HLPackageType for examples of types of packages.
    """

    @staticmethod
    # hlBool hlBindPackage(hlUInt uiPackage);
    def bind_package(package_id):
        """Binds the package with the given ID to the context.

        Args:
            The ID of the package to bind, typically a value obtained
                from create_package().
        Raises:
            HLError: If there is an error binding the package.
        """
        if not _hl.hlBindPackage(package_id):
            raise HLError("Failed to bind package.")

    @staticmethod
    def get_package_type_from_file(path):
        """Returns the type of package given a path to the package."""
        package_type = Package.get_package_type_from_name(path)

        if package_type == HLPackageType.HL_PACKAGE_NONE:
            with open(path, "rb") as f:
                buf = f.read(HL_DEFAULT_PACKAGE_TEST_BUFFER_SIZE)
                package_type = Package.get_package_type_from_memory(
                        buf, HL_DEFAULT_PACKAGE_TEST_BUFFER_SIZE)

        return package_type

    @staticmethod
    # HLPackageType hlGetPackageTypeFromName(const hlChar *lpName);
    def get_package_type_from_name(name):
        """Returns the type of package given the package's file name."""
        name = _encode(name)
        return _hl.hlGetPackageTypeFromName(name)

    @staticmethod
    # HLPackageType hlGetPackageTypeFromMemory(const hlVoid *lpBuffer,
    #       hlUInt uiBufferSize);
    def get_package_type_from_memory(buf, n):
        """Returns the type of package given its first n bytes."""
        c_buf = _get_const_compatible_buffer(buf, n)
        return _hl.hlGetPackageTypeFromMemory(c_buf, n)

    @staticmethod
    # HLPackageType hlGetPackageTypeFromStream(HLStream *pStream);
    def get_package_type_from_stream(stream):
        """Returns the type of package given a stream of the package."""
        return _hl.hlGetPackageTypeFromStream(stream)

    @staticmethod
    # hlBool hlCreatePackage(HLPackageType ePackageType, hlUInt *uiPackage);
    def create_package(package_type):
        """Creates a package object and returns its ID.

        Args:
            package_type: The type of package object to create.
                See HLPackageType.

        Returns:
            The package ID of the created package.

        Raises:
            HLError: If the package type is invalid. Or if there is an
                error creating the package object for any reason.
        """
        result = hlUInt()

        if not _hl.hlCreatePackage(package_type, _c.byref(result)):
            raise HLError("Failed to create package of "
                    "type {0}.".format(package_type))

        return result.value

    @staticmethod
    # hlVoid hlDeletePackage(hlUInt uiPackage);
    def delete_package(package_id):
        """Deletes a package object given the ID."""
        _hl.hlDeletePackage(package_id)

    @staticmethod
    # HLPackageType hlPackageGetType();
    def get_type():
        """Returns the bound package's type (see HLPackageType)."""
        return _hl.hlPackageGetType()

    @staticmethod
    # const hlChar *hlPackageGetExtension();
    def get_extension():
        """Returns the extension associated with the bound package.

        Returns:
            The extension associated with the bound package.

        Raises:
            HLError: If there is an error getting the extension.
        """
        extension = _hl.hlPackageGetExtension()

        if extension is None:
            raise HLError("Failed to get package extension.")

        return extension.decode(_unicode_encoding)

    @staticmethod
    # const hlChar *hlPackageGetDescription();
    def get_description():
        """Returns the description associated with the bound package.

        Returns:
            The description associated with the bound package.

        Raises:
            HLError: If there is an error getting the description.
        """
        description = _hl.hlPackageGetDescription()

        if description is None:
            raise HLError("Failed to get package description.")

        return description.decode(_unicode_encoding)

    @staticmethod
    # hlBool hlPackageGetOpened();
    def get_opened():
        """Returns whether or not the bound package is open."""
        return _hl.hlPackageGetOpened()

    @staticmethod
    # hlBool hlPackageOpenFile(const hlChar *lpFileName, hlUInt uiMode);
    def open_file(file_name, file_mode):
        """Opens package file and associates it with bound package.

        Args:
            file_name: The path of the file to open.

            file_mode: The mode(s) with which to open the package.
                See HLFileMode.

        Raises:
            HLError: If there is an error opening the package.
        """
        file_name = _encode(file_name)
        if not _hl.hlPackageOpenFile(file_name, file_mode):
            raise HLError("Failed to open package file {0}.".format(file_name))

    @staticmethod
    # hlBool hlPackageOpenMemory(hlVoid *lpData,
    #       hlUInt uiBufferSize, hlUInt uiMode);
    def open_memory(buf, n, file_mode):
        """Opens memory package and associates it with bound package.

        Args:
            buf: The buffer from which the package data will be read.

            n: The number of bytes in the buffer from which the
                package data will be read.

            file_mode: The mode(s) with which to open the package.
                See HLFileMode.

        Raises:
            HLError: If there is an error opening the package.
        """
        c_buf = (_c.c_byte * n).from_buffer(buf)

        if not _hl.hlPackageOpenMemory(c_buf, n, file_mode):
            raise HLError("Failed to open package from memory.")

    @staticmethod
    # hlBool hlPackageOpenProc(hlVoid *pUserData, hlUInt uiMode);
    def open_proc(user_data, file_mode):
        """Opens package using custom functions.

        Associates package data with bound package object.

        See HLOptions HL_PROC_OPEN, HL_PROC_READ, etc.

        Args:
            user_data: Arbitrary data which should be passed to the
                custom functions.

            file_mode: The mode(s) with which to open the package.
                See HLFileMode.

        Raises:
            HLError: If there is an error opening the package.
        """
        if not _hl.hlPackageOpenProc(user_data, file_mode):
            raise HLError("Failed to open package using procedure.""")

    @staticmethod
    # hlBool hlPackageOpenStream(HLStream *pStream, hlUInt uiMode);
    def open_stream(stream, file_mode):
        """Opens package stream and associates it with bound package.

        Args:
            buf: The stream from which the package data will be read.

            file_mode: The mode(s) with which to open the package.
                See HLFileMode.

        Raises:
            HLError: If there is an error opening the package.
        """
        if not _hl.hlPackageOpenStream(stream, file_mode):
            raise HLError("Failed to open package from stream.")

    @staticmethod
    # hlVoid hlPackageClose();
    def close():
        """Closes bound package."""
        _hl.hlPackageClose()

    @staticmethod
    # hlBool hlPackageDefragment();
    def defragment():
        """Defragments bound package.

        Raises:
            HLError: If there is an error defragmenting the package.
        """
        if not _hl.hlPackageDefragment():
            raise HLError("Failed to defragment package.")

    @staticmethod
    # HLDirectoryItem *hlPackageGetRoot();
    def get_root():
        """Returns root directory of bound package.

        Returns:
            Root directory of bound package.

        Raises:
            HLError: If there is an error getting the root directory.
        """
        item = _hl.hlPackageGetRoot()

        if item is None:
            raise HLError("Failed to get root directory of package.")

        return _hl_directory_instance(item)

    @staticmethod
    # hlUInt hlPackageGetAttributeCount();
    def get_attribute_count():
        """Returns the number of attributes for bound package."""
        return _hl.hlPackageGetAttributeCount()

    @staticmethod
    # const hlChar *hlPackageGetAttributeName(HLPackageAttribute eAttribute);
    def get_attribute_name(package_attribute):
        """Returns name of the package attribute for the bound package.

        Args:
            package_attribute: The HLPackageAttribute value. The
                valid values for the currently bound package are
                0 to Package.get_attribute_count() - 1.

        Returns:
            The name of the package attribute for the bound package.

        Raises:
            HLError: If the package_attribute is invalid. Or if there
                is an error getting the attribute name for any reason.
        """
        name = _hl.hlPackageGetAttributeName(package_attribute)

        if name is None:
            raise HLError("Failed to get package attribute name "
                    "for package attribute {0}.".format(name))

        return name.decode(_unicode_encoding)

    @staticmethod
    # hlBool hlPackageGetAttribute(HLPackageAttribute eAttribute,
    #       HLAttribute *pAttribute);
    def get_attribute(package_attribute):
        """Returns the package attribute for the bound package.

        Args:
            package_attribute: The HLPackageAttribute value. The
                valid values for the currently bound package are
                0 to Package.get_attribute_count() - 1.

        Returns:
            The value of the package attribute for the bound package.

        Raises:
            HLError: If the package_attribute is invalid. Or if there
                is an error getting the attribute for any reason.
        """
        attribute = HLAttribute()

        if not _hl.hlPackageGetAttribute(
                package_attribute, _c.byref(attribute)):
            raise HLError("Failed to get package attribute "
                    "{0}.".format(package_attribute))

        return attribute

    @staticmethod
    # hlUInt hlPackageGetItemAttributeCount();
    def get_item_attribute_count():
        """Returns the number of item attributes for bound package."""
        return _hl.hlPackageGetItemAttributeCount()

    @staticmethod
    # const hlChar *hlPackageGetItemAttributeName(
    #       HLPackageAttribute eAttribute);
    def get_item_attribute_name(item_attribute):
        """Returns name of the item attribute for the bound package.

        Args:
            item_attribute: The HLPackageAttribute value. The
                valid values for the currently bound package are
                0 to Package.get_item_attribute_count() - 1.

        Returns:
            The name of the item attribute for the bound package.

        Raises:
            HLError: If the item_attribute is invalid. Or if there
                is an error getting the attribute name for any reason.
        """
        attribute_name = _hl.hlPackageGetItemAttributeName(item_attribute)

        if attribute_name is None:
            raise HLError("Failed to get item attribute name for "
                    "package attribute {0}".format(item_attribute))

        return attribute_name.decode(_unicode_encoding)

    @staticmethod
    # hlBool hlPackageGetItemAttribute(const HLDirectoryItem *pItem,
    #       HLPackageAttribute eAttribute, HLAttribute *pAttribute);
    def get_item_attribute(directory_item, item_attribute):
        """Returns the item attribute for the item and bound package.

        Args:
            item_attribute: The HLPackageAttribute value. The
                valid values for the currently bound package are
                0 to Package.get_item_attribute_count() - 1.

        Returns:
            The value of the item attribute for the item and bound
            package.

        Raises:
            HLError: If the item_attribute is invalid. Or if there
                is an error getting the attribute for any reason.
        """
        attribute = HLAttribute()

        if not _hl.hlPackageGetItemAttribute(directory_item,
                item_attribute, _c.byref(attribute)):
            raise HLError("Failed to get item attribute "
                    "{0}.".format(item_attribute))

        return attribute

    @staticmethod
    # hlBool hlPackageGetExtractable(const HLDirectoryItem *pFile,
    #       hlBool *pExtractable);
    def get_extractable(directory_file):
        """Returns whether or not the directory file is extractable.

        Args:
            directory_file: The file whose extractability is to be
                determined.

        Returns:
            Whether or not the directory file is extractable.

        Raises:
            HLError: If there is an error determining whether or not
                the item is extractable.
        """
        result = hlBool()

        if not _hl.hlPackageGetExtractable(directory_file, _c.byref(result)):
            raise HLError("Failed to determine if directory item {0} "
                    "is extractable.".format(directory_file.get_name()))

        return result.value

    @staticmethod
    # hlBool hlPackageGetFileSize(const HLDirectoryItem *pFile, hlUInt *pSize);
    def get_file_size(directory_file):
        """Returns the size of the file's contents in memory.

        Args:
            directory_file: The file whose size is to be determined.

        Returns:
            The size of the file's contents in memory.

        Raises:
            HLError: If there is an error getting the file size.
        """
        result = hlUInt()

        if not _hl.hlPackageGetFileSize(directory_file, _c.byref(result)):
            raise HLError("Failed to get file size of directory "
                    "file {0}.".format(directory_file.get_name()))

        return result.value

    @staticmethod
    # hlBool hlPackageGetFileSizeOnDisk(const HLDirectoryItem *pFile,
    #       hlUInt *pSize);
    def get_file_size_on_disk(directory_file):
        """Returns the size of the file's contents on disk.

        Args:
            directory_file: The file whose size is to be determined.

        Returns:
            The size of the file's contents on disk.

        Raises:
            HLError: If there is an error getting the file size.
        """
        result = hlUInt()

        if not _hl.hlPackageGetFileSizeOnDisk(
                directory_file, _c.byref(result)):
            raise HLError("Failed to get file size on disk of directory "
                    "file {0}.".format(directory_file.get_name()))

        return result.value

    @staticmethod
    # hlBool hlPackageCreateStream(const HLDirectoryItem *pFile,
    #       HLStream **pStream);
    def create_stream(directory_file):
        """Returns a stream for the directory file.

        The stream can be used to, for example, read from the file.

        Args:
            directory_file: The file for which a stream is to be
                created.

        Returns:
            A stream for the directory file.

        Raises:
            HLError: If there is an error creating the stream.
        """
        pointer = hlVoidPtr()

        if not _hl.hlPackageCreateStream(directory_file, _c.byref(result)):
            raise HLError("Failed to create stream from directory "
                    "file {0}.".format(directory_file.get_name()))

        return HLStream(pointer)

    @staticmethod
    # hlVoid hlPackageReleaseStream(HLStream *pStream);
    def release_stream(stream):
        """Releases the given stream."""
        _hl.hlPackageReleaseStream(stream)


class NCFFile(object):
    """A collection of static methods for dealing with NCF packages."""

    @staticmethod
    # const hlChar *hlNCFFileGetRootPath();
    def get_root_path():
        """Returns the NCF's root path.

        Raises:
            HLError: If there is an error getting the root path.
        """
        result = _hl.hlNCFFileGetRootPath()

        if result is None:
            raise HLError("Failed to get root path.")

        return result.decode(_unicode_encoding)

    @staticmethod
    # hlVoid hlNCFFileSetRootPath(const hlChar *lpRootPath);
    def set_root_path(root_path):
        """Sets the NCF's root path."""
        root_path = _encode(root_path)
        _hl.hlNCFFileSetRootPath(root_path)


class WADFile(object):
    """A collection of static methods for dealing with WAD packages."""
    @staticmethod
    # hlBool hlWADFileGetImageSizePaletted(const HLDirectoryItem *pFile,
    #       hlUInt *uiPaletteDataSize, hlUInt *uiPixelDataSize);
    def get_image_size_paletted(directory_file):
        """Returns the data size of the palette and pixels in the file.

        Args:
            directory_file: The directory file from which the image size
                is to be determined.

        Returns:
            A tuple of the size of the buffer needed to hold the
            palette data and the size of the buffer needed to hold
            the pixel data.

        Raises:
            HLError: If there is an error getting the data sizes.
        """
        palette_data_size = hlUInt()
        pixel_data_size = hlUInt()

        if not _hl.hlWADFileGetImageSizePaletted(directory_file,
                _c.byref(palette_data_size), _c.byref(pixel_data_size)):
            raise HLError("Failed to get image size of directory "
                    "file {0}.".format(directory_file.get_name()))

        return palette_data_size.value, pixel_data_size.value

    @staticmethod
    # hlBool hlWADFileGetImageDataPaletted(const HLDirectoryItem *pFile,
    #       hlUInt *uiWidth, hlUInt *uiHeight, hlByte **lpPaletteData,
    #       hlByte **lpPixelData);
    def get_image_data_paletted(directory_file,
            palette_data_buf=None, pixel_data_buf=None):
        """Returns the palette and pixel data in the file.

        Args:
            directory_file: The directory file from which the data is to
                be extracted.

            palette_data_buf: A buffer to hold the palette data.
                If None, one will be created for the caller.

            pixel_data_buf: A buffer to hold the pixel data.
                If None, one will be created for the caller.

        Returns:
            A tuple of the image width, height, palette buffer,
            and pixel buffer.

        Raises:
            HLError: If the buffers are smaller than the corresponding
                sizes returned by get_image_size_paletted(). Or if there
                is an error getting the data for any reason.
        """
        palette_data_size, pixel_data_size = (
                WADFile.get_image_size_paletted(directory_file))

        if palette_data_buf is None:
            palette_data_buf = bytearray(palette_data_size)
        elif len(palette_data_buf) < palette_data_size:
            raise HLError("Palette buffer is too small "
                    "to contain palette data.")

        if pixel_data_buf is None:
            pixel_data_buf = bytearray(pixel_data_size)
        elif len(pixel_data_buf) < pixel_data_size:
            raise HLError("Pixel buffer is too small to contain pixel data.")

        width = hlUInt()
        height = hlUInt()

        c_palette_buf_type = hlByte * len(palette_data_buf)
        c_palette_buf = c_palette_buf_type.from_buffer(palette_data_buf)

        c_pixel_buf_type = hlByte * len(pixel_data_buf)
        c_pixel_buf = c_pixel_buf_type.from_buffer(pixel_data_buf)

        if not _hl.hlWADFileGetImageDataPaletted(directory_file,
                _c.byref(width), _c.byref(height),
                _c.byref(c_palette_buf), _c.byref(c_pixel_buf)):
            raise HLError("Failed to get image data of directory "
                    "file {0}.".format(directory_file.get_name()))

        return width, height, palette_data_buf, pixel_data_buf

    @staticmethod
    # hlBool hlWADFileGetImageSize(const HLDirectoryItem *pFile,
    #       hlUInt *uiPixelDataSize);
    def get_image_size(directory_file):
        """Returns data size of pixels in the file.

        Args:
            directory_file: The directory file from which the image size
                is to be determined.

        Returns:
            The size of the buffer needed to hold the pixel data.

        Raises:
            HLError: If there is an error getting data size.
        """
        pixel_data_size = hlUInt()

        if not _hl.hlWADFileGetImageSize(
                directory_file, _c.byref(pixel_data_size)):
            raise HLError("Failed to get image size of directory "
                    "file {0}.".format(directory_file.get_name()))

        return pixel_data_size.value

    @staticmethod
    # hlBool hlWADFileGetImageData(const HLDirectoryItem *pFile,
    #       hlUInt *uiWidth, hlUInt *uiHeight, hlByte **lpPixelData);
    def get_image_data(directory_file):
        """Returns the pixel data in the file.

        Args:
            directory_file: The directory file from which the data is to
                be extracted.

            pixel_data_buf: A buffer to hold the pixel data.
                If None, one will be created for the caller.

        Returns:
            A tuple of the image width, height, and pixel buffer.

        Raises:
            HLError: If the buffer is smaller than the size returned
                by get_image_size(). Or if there is an error getting
                the data for any reason.
        """
        pixel_data_size = WADFile.get_image_size(directory_file)

        if pixel_data_buf is None:
            pixel_data_buf = bytearray(pixel_data_size)
        elif len(pixel_data_buf) < pixel_data_size:
            raise HLError("Pixel buffer is too small to contain pixel data.")

        width = hlUInt()
        height = hlUInt()

        c_pixel_buf_type = hlByte * len(pixel_data_buf)
        c_pixel_buf = c_pixel_buf_type.from_buffer(pixel_data_buf)

        if not _hl.hlWADFileGetImageData(directory_file,
                _c.byref(width), _c.byref(height), _c.byref(c_pixel_buf)):
            raise HLError("Failed to get image data of directory "
                    "file {0}.".format(directory_file.get_name()))

        return width, height, pixel_data_buf


# Functions


_unicode_encoding = _sys.getdefaultencoding()


def _encode(string):
    """Encode a unicode string using the set encoding."""
    version = _sys.version_info[0]

    if ((version == 2 and isinstance(string, unicode)) or
            (version == 3 and isinstance(string, str))):
        return string.encode(_unicode_encoding)
    else:
        # Good luck.
        return string


def set_unicode_encoding(encoding):
    """Sets the encoding for unicode strings.

    Unicode strings passed to functions will be encoded using this.
    """
    global _unicode_encoding
    _unicode_encoding = encoding


def get_unicode_encoding():
    """Gets the encoding for unicode strings.

    Unicode strings passed to functions will be encoded using this.
    """
    return _unicode_encoding


def _get_const_compatible_buffer(buf, n):
    """Returns buffer that can be passed as const pointer to C function."""
    if len(buf) < n:
        raise HLError("Buffer length ({0}) is smaller than "
                "requested length ({1}).".format(len_buf), n)

    version = _sys.version_info[0]

    # Can pass strings directly to C functions taking const pointers.
    if not (version == 2 and isinstance(buf, str) or
            version == 3 and isinstance(buf, bytes)):
        try:
            # Can create ctypes buffer from writeable buffers.
            buf = (_c.c_byte * n).from_buffer(buf)
            print("writeable buf")
        except TypeError:
            # Cannot create ctypes buffer from non-writeable buffers.
            # Fall back on copying the buffer if type supports it.
            print("other buf")
            buf = (_c.c_byte * n).from_buffer_copy(buf)
            print("other buf success")

    return buf


# hlVoid hlInitialize();
def initialize():
    """Initialize the library."""
    _hl.hlInitialize()


# hlVoid hlShutdown();
def shutdown():
    """Perform cleanup and shutdown the library."""
    _hl.hlShutdown()


def _get_value(option, hl_type, type_string, function):
    result = hl_type()

    if not function(option, _c.byref(result)):
        raise HLError("Failed to get {0} value for "
                "option {1}.".format(type_string, option))

    return result.value


# hlBool hlGetBooleanValidate(HLOption eOption, hlBool *pValue);
def _get_boolean(option):
    return _get_value(option, hlBool, "boolean", _hl.hlGetBooleanValidate)


#hlBool hlGetIntegerValidate(HLOption eOption, hlInt *pValue);
def _get_integer(option):
    return _get_value(option, hlInt, "integer", _hl.hlGetIntegerValidate)


# hlBool hlGetUnsignedIntegerValidate(HLOption eOption, hlUInt *pValue);
def _get_unsigned_integer(option):
    return _get_value(option, hlUInt, "unsigned integer",
            _hl.hlGetUnsignedIntegerValidate)


# hlBool hlGetLongLongValidate(HLOption eOption, hlLongLong *pValue);
def _get_long_long(option):
    return _get_value(option, hlLongLong, "long long",
            _hl.hlGetLongLongValidate)


# hlBool hlGetUnsignedLongLongValidate(HLOption eOption, hlULongLong *pValue);
def _get_unsigned_long_long(option):
    return _get_value(option, hlULongLong, "unsigned long long",
            _hl.hlGetUnsignedLongLongValidate)


# hlBool hlGetFloatValidate(HLOption eOption, hlFloat *pValue);
def _get_float(option):
    return _get_value(option, hlFloat, "float", _hl.hlGetFloatValidate)


# hlBool hlGetStringValidate(HLOption eOption, const hlChar **pValue);
def _get_string(option):
    string = _get_value(option, hlString, "float", _hl.hlGetStringValidate)

    if string is not None:
        string = string.decode(_unicode_encoding)

    return string


# hlBool hlGetVoidValidate(HLOption eOption, const hlVoid **pValue);
def _get_void(option):
    return _get_value(option, hlVoidPtr, "void pointer", _hl.hlGetVoidValidate)


_getters = {
    (HLOption.HL_VERSION, hlUInt): _get_unsigned_integer,
    (HLOption.HL_VERSION, hlString): _get_string,
    (HLOption.HL_VERSION, None): _get_string,

    (HLOption.HL_ERROR, hlString): _get_string,
    (HLOption.HL_ERROR, None): _get_string,

    (HLOption.HL_ERROR_SYSTEM, hlUInt): _get_unsigned_integer,
    (HLOption.HL_ERROR_SYSTEM, hlString): _get_string,
    (HLOption.HL_ERROR_SYSTEM, None): _get_string,

    (HLOption.HL_ERROR_SHORT_FORMATED, hlString): _get_string,
    (HLOption.HL_ERROR_SHORT_FORMATED, None): _get_string,

    (HLOption.HL_ERROR_LONG_FORMATED, hlString): _get_string,
    (HLOption.HL_ERROR_LONG_FORMATED, None): _get_string,

    (HLOption.HL_OVERWRITE_FILES, hlBool): _get_boolean,
    (HLOption.HL_OVERWRITE_FILES, None): _get_boolean,

    (HLOption.HL_PACKAGE_BOUND, hlBool): _get_boolean,
    (HLOption.HL_PACKAGE_BOUND, None): _get_boolean,

    (HLOption.HL_PACKAGE_ID, hlUInt): _get_unsigned_integer,
    (HLOption.HL_PACKAGE_ID, hlULongLong): _get_unsigned_long_long,
    (HLOption.HL_PACKAGE_ID, None): _get_unsigned_long_long,

    (HLOption.HL_PACKAGE_SIZE, hlUInt): _get_unsigned_integer,
    (HLOption.HL_PACKAGE_SIZE, hlULongLong): _get_unsigned_long_long,
    (HLOption.HL_PACKAGE_SIZE, None): _get_unsigned_long_long,

    (HLOption.HL_PACKAGE_TOTAL_ALLOCATIONS, hlUInt): _get_unsigned_integer,
    (HLOption.HL_PACKAGE_TOTAL_ALLOCATIONS, hlULongLong):
            _get_unsigned_long_long,
    (HLOption.HL_PACKAGE_TOTAL_ALLOCATIONS, None): _get_unsigned_long_long,

    (HLOption.HL_PACKAGE_TOTAL_MEMORY_ALLOCATED, hlUInt):
            _get_unsigned_integer,
    (HLOption.HL_PACKAGE_TOTAL_MEMORY_ALLOCATED, hlULongLong):
            _get_unsigned_long_long,
    (HLOption.HL_PACKAGE_TOTAL_MEMORY_ALLOCATED, None):
            _get_unsigned_long_long,

    (HLOption.HL_PACKAGE_TOTAL_MEMORY_USED, hlUInt): _get_unsigned_integer,
    (HLOption.HL_PACKAGE_TOTAL_MEMORY_USED, hlULongLong):
            _get_unsigned_long_long,
    (HLOption.HL_PACKAGE_TOTAL_MEMORY_USED, None): _get_unsigned_long_long,

    (HLOption.HL_READ_ENCRYPTED, hlBool): _get_boolean,
    (HLOption.HL_READ_ENCRYPTED, None): _get_boolean,

    (HLOption.HL_FORCE_DEFRAGMENT, hlBool): _get_boolean,
    (HLOption.HL_FORCE_DEFRAGMENT, None): _get_boolean,

    (HLOption.HL_PROC_OPEN, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_OPEN, None): _get_void,

    (HLOption.HL_PROC_CLOSE, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_CLOSE, None): _get_void,

    (HLOption.HL_PROC_READ, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_READ, None): _get_void,

    (HLOption.HL_PROC_WRITE, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_WRITE, None): _get_void,

    (HLOption.HL_PROC_SEEK, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_SEEK, None): _get_void,

    (HLOption.HL_PROC_SEEK_EX, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_SEEK_EX, None): _get_void,

    (HLOption.HL_PROC_TELL, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_TELL, None): _get_void,

    (HLOption.HL_PROC_TELL_EX, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_TELL_EX, None): _get_void,

    (HLOption.HL_PROC_SIZE, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_SIZE, None): _get_void,

    (HLOption.HL_PROC_SIZE_EX, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_SIZE_EX, None): _get_void,

    (HLOption.HL_PROC_EXTRACT_ITEM_START, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_EXTRACT_ITEM_START, None): _get_void,

    (HLOption.HL_PROC_EXTRACT_ITEM_END, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_EXTRACT_ITEM_END, None): _get_void,

    (HLOption.HL_PROC_EXTRACT_FILE_PROGRESS, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_EXTRACT_FILE_PROGRESS, None): _get_void,

    (HLOption.HL_PROC_VALIDATE_FILE_PROGRESS, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_VALIDATE_FILE_PROGRESS, None): _get_void,

    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS, None): _get_void,

    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS_EX, hlVoidPtr): _get_void,
    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS_EX, None): _get_void,
}


def get_value(option, hl_type=None):
    """Returns the value associated with the given option.

    This corresponds to the hlGetBoolValidate(), hlGetStringValidate(),
    etc. functions in the C library version of HLLib.

    The value of some options cannot be retrieved.

    The value of some options can be retrieved, but should be regarded
    as an unstable artifact of the current API. In particular, the value
    retrieved for an HLOption corresponding to a callback, such as
    HLOption.HL_PROC_EXTRACT_FILE_PROGRESS, is not the value that was
    set by the previous set_value() call for the same option. The value
    currently returned is the address of the C callback function.

    Args:
        option: The HLOption to get the value for.

        hl_type: A type such as hlInt, hlString, etc. Setting this to
            something other than None causes this function to attempt
            to retrieve the value as a specific type. If there is no
            support for getting the value of the option for the
            specified type, an HLError will be raised.

    Returns:
        Returns the value associated with the given option.

    Raises:
        HLError: If the value for the given option cannot be retrieved.
            Reasons include: not supporting getting the value of the
            option, not supporting getting the value of the option given
            the hl_type, the program state being such that the value
            cannot currently be obtained (e.g. no package bound), etc.
    """
    key = (option, hl_type)
    function = _getters.get(key)

    if function is None:
        raise HLError("Cannot get value for option {0} "
                "given type {1}".format(option, hl_type))

    return function(option)


# TODO Define callback setters more succinctly.


# typedef hlBool (*POpenProc) (hlUInt, hlVoid *);
_proc_open_type = _callback_factory(hlBool, hlUInt, hlVoidPtr)
_proc_open = None


def _set_proc_open(option, callback):
    global _proc_open
    _proc_open = _proc_open_type(callback)
    _hl.hlSetVoid(option, _proc_open)


# typedef hlVoid (*PCloseProc)(hlVoid *);
_proc_close_type = _callback_factory(None, hlVoidPtr)
_proc_close = None


def _set_proc_close(option, callback):
    global _proc_close
    _proc_open = _proc_close_type(wrapper)
    _hl.hlSetVoid(option, _proc_close)


# typedef hlUInt (*PReadProc)  (hlVoid *, hlUInt, hlVoid *);
_proc_read_type = _callback_factory(hlUInt, hlVoidPtr, hlUInt, hlVoidPtr)
_proc_read = None


def _set_proc_read(option, callback):
    global _proc_read
    _proc_read = _proc_read_type(callback)
    _hl.hlSetVoid(option, _proc_read)


# typedef hlUInt (*PWriteProc)  (const hlVoid *, hlUInt, hlVoid *);
_proc_write_type = _callback_factory(hlUInt, hlVoidPtr, hlUInt, hlVoidPtr)
_proc_write = None


def _set_proc_write(option, callback):
    global _proc_write
    _proc_write = _proc_write_type(callback)
    _hl.hlSetVoid(option, _proc_write)


# typedef hlUInt (*PSeekProc) (hlLongLong, HLSeekMode, hlVoid *);
_proc_seek_type = _callback_factory(hlUInt, hlLongLong, hlInt, hlVoidPtr)
_proc_seek = None


def _set_proc_seek(option, callback):
    global _proc_seek
    _proc_seek = _proc_seek_type(callback)
    _hl.hlSetVoid(option, _proc_seek)


# typedef hlULongLong (*PSeekExProc) (hlLongLong, HLSeekMode, hlVoid *);
_proc_seek_ex_type = _callback_factory(hlULongLong,
        hlLongLong, hlInt, hlVoidPtr)
_proc_seek_ex = None


def _set_proc_seek_ex(option, callback):
    global _proc_seek_ex
    _proc_seek_ex = _proc_seek_ex_type(callback)
    _hl.hlSetVoid(option, _proc_seek_ex)


# typedef hlUInt (*PTellProc) (hlVoid *);
_proc_tell_type = _callback_factory(hlUInt, hlVoidPtr)
_proc_tell = None


def _set_proc_tell(option, callback):
    global _proc_tell
    _proc_tell = _proc_tell_type(callback)
    _hl.hlSetVoid(option, _proc_tell)


# typedef hlULongLong (*PTellExProc) (hlVoid *);
_proc_tell_ex_type = _callback_factory(hlULongLong, hlVoidPtr)
_proc_tell_ex = None


def _set_proc_tell_ex(option, callback):
    global _proc_tell_ex
    _proc_tell_ex = _proc_tell_ex_type(callback)
    _hl.hlSetVoid(option, _proc_tell_ex)


# typedef hlUInt (*PSizeProc) (hlVoid *);
_proc_size_type = _callback_factory(hlUInt, hlVoidPtr)
_proc_size = None


def _set_proc_size(option, callback):
    global _proc_size
    _proc_size = _proc_size_type(callback)
    _hl.hlSetVoid(option, _proc_size)


# typedef hlULongLong (*PSizeExProc) (hlVoid *);
_proc_size_ex_type = _callback_factory(hlULongLong, hlVoidPtr)
_proc_size_ex = None


def _set_proc_size_ex(option, callback):
    global _proc_size_ex
    _proc_size_ex = _proc_size_ex_type(callback)
    _hl.hlSetVoid(option, _proc_size_ex)


# typedef hlVoid (*PExtractItemStartProc) (const HLDirectoryItem *pItem);
_proc_extract_item_start_type = _callback_factory(None, hlVoidPtr)
_proc_extract_item_start = None


def _set_proc_extract_item_start(option, callback):
    def wrapper(handle):
        callback(_hl_directory_instance(handle))

    global _proc_extract_item_start
    _proc_extract_item_start = _proc_extract_item_start_type(wrapper)
    _hl.hlSetVoid(option, _proc_extract_item_start)


# typedef hlVoid (*PExtractItemEndProc) (const HLDirectoryItem *pItem,
#       hlBool bSuccess);
_proc_extract_item_end_type = _callback_factory(None, hlVoidPtr, hlBool)
_proc_extract_item_end = None


def _set_proc_extract_item_end(option, callback):
    def wrapper(handle, success):
        callback(_hl_directory_instance(handle), success)

    global _proc_extract_item_end
    _proc_extract_item_end = _proc_extract_item_end_type(wrapper)
    _hl.hlSetVoid(option, _proc_extract_item_end)


# typedef hlVoid (*PExtractFileProgressProc) (const HLDirectoryItem *pFile,
#       hlUInt uiBytesExtracted, hlUInt uiBytesTotal, hlBool *pCancel);
_proc_extract_file_progress_type = _callback_factory(None, hlVoidPtr,
        hlUInt, hlUInt, _c.POINTER(hlBool))
_proc_extract_file_progress = None


def _set_proc_extract_file_progress(option, callback):
    def wrapper(handle, bytes_extracted, bytes_total, cancel):
        try:
            callback(_hl_directory_instance(handle),
                    bytes_extracted, bytes_total)
        except HLCancel:
            cancel[0] = True

    global _proc_extract_file_progress
    _proc_extract_file_progress = _proc_extract_file_progress_type(wrapper)
    _hl.hlSetVoid(option, _proc_extract_file_progress)


# typedef hlVoid (*PValidateFileProgressProc) (const HLDirectoryItem *pFile,
#       hlUInt uiBytesValidated, hlUInt uiBytesTotal, hlBool *pCancel);
_proc_validate_file_progress_type = _callback_factory(None, hlVoidPtr,
        hlUInt, hlUInt, _c.POINTER(hlBool))
_proc_validate_file_progress = None


def _set_proc_validate_file_progress(option, callback):
    def wrapper(handle, bytes_validated, bytes_total, cancel):
        try:
            callback(_hl_directory_instance(handle),
                    bytes_validated, bytes_total)
        except HLCancel:
            cancel[0] = True

    global _proc_validate_file_progress
    _proc_validate_file_progress = _proc_validate_file_progress_type(wrapper)
    _hl.hlSetVoid(option, _proc_validate_file_progress)


# typedef hlVoid (*PDefragmentProgressProc) (const HLDirectoryItem *pFile,
#       hlUInt uiFilesDefragmented, hlUInt uiFilesTotal,
#       hlUInt uiBytesDefragmented, hlUInt uiBytesTotal, hlBool *pCancel);
_proc_defragment_progress_type = _callback_factory(None, hlVoidPtr,
        hlUInt, hlUInt, hlUInt, hlUInt, _c.POINTER(hlBool))
_proc_defragment_progress = None


def _set_proc_defragment_progress(option, callback):
    def wrapper(handle, files_defragmented, files_total,
            bytes_defragmented, bytes_total, cancel):
        try:
            callback(_hl_directory_instance(handle), files_defragmented,
                    files_total, bytes_defragmented, bytes_total)
        except HLCancel:
            cancel[0] = True

    global _proc_defragment_progress
    _proc_defragment_progress = _proc_defragment_progress_type(wrapper)
    _hl.hlSetVoid(option, _proc_defragment_progress)


# typedef hlVoid (*PDefragmentProgressExProc) (const HLDirectoryItem *pFile,
#       hlUInt uiFilesDefragmented, hlUInt uiFilesTotal,
#       hlULongLong uiBytesDefragmented, hlULongLong uiBytesTotal,
#       hlBool *pCancel);
_proc_defragment_progress_ex_type = _callback_factory(None, hlVoidPtr,
        hlUInt, hlUInt, hlULongLong, hlULongLong, _c.POINTER(hlBool))
_proc_defragment_progress_ex = None


def _set_proc_defragment_progress_ex(option, callback):
    def wrapper(handle, files_defragmented, files_total,
            bytes_defragmented, bytes_total, cancel):
        try:
            callback(_hl_directory_instance(handle), files_defragmented,
                    files_total, bytes_defragmented, bytes_total)
        except HLCancel:
            cancel[0] = True

    global _proc_defragment_progress_ex
    _proc_defragment_progress_ex = _proc_defragment_progress_ex_type(wrapper)
    _hl.hlSetVoid(option, _proc_defragment_progress_ex)


_setters = {
    (HLOption.HL_OVERWRITE_FILES, hlBool): _hl.hlSetBoolean,
    (HLOption.HL_OVERWRITE_FILES, None): _hl.hlSetBoolean,

    (HLOption.HL_READ_ENCRYPTED, hlBool): _hl.hlSetBoolean,
    (HLOption.HL_READ_ENCRYPTED, None): _hl.hlSetBoolean,

    (HLOption.HL_FORCE_DEFRAGMENT, hlBool): _hl.hlSetBoolean,
    (HLOption.HL_FORCE_DEFRAGMENT, None): _hl.hlSetBoolean,

    (HLOption.HL_PROC_OPEN, hlVoidPtr): _set_proc_open,
    (HLOption.HL_PROC_OPEN, None): _set_proc_open,

    (HLOption.HL_PROC_CLOSE, hlVoidPtr): _set_proc_close,
    (HLOption.HL_PROC_CLOSE, None): _set_proc_close,

    (HLOption.HL_PROC_READ, hlVoidPtr): _set_proc_read,
    (HLOption.HL_PROC_READ, None): _set_proc_read,

    (HLOption.HL_PROC_WRITE, hlVoidPtr): _set_proc_write,
    (HLOption.HL_PROC_WRITE, None): _set_proc_write,

    (HLOption.HL_PROC_SEEK, hlVoidPtr): _set_proc_seek,
    (HLOption.HL_PROC_SEEK, None): _set_proc_seek,

    (HLOption.HL_PROC_SEEK_EX, hlVoidPtr): _set_proc_seek_ex,
    (HLOption.HL_PROC_SEEK_EX, None): _set_proc_seek_ex,

    (HLOption.HL_PROC_TELL, hlVoidPtr): _set_proc_tell,
    (HLOption.HL_PROC_TELL, None): _set_proc_tell,

    (HLOption.HL_PROC_TELL_EX, hlVoidPtr): _set_proc_tell_ex,
    (HLOption.HL_PROC_TELL_EX, None): _set_proc_tell_ex,

    (HLOption.HL_PROC_SIZE, hlVoidPtr): _set_proc_size,
    (HLOption.HL_PROC_SIZE, None): _set_proc_size,

    (HLOption.HL_PROC_SIZE_EX, hlVoidPtr): _set_proc_size_ex,
    (HLOption.HL_PROC_SIZE_EX, None): _set_proc_size_ex,

    (HLOption.HL_PROC_EXTRACT_ITEM_START, hlVoidPtr):
        _set_proc_extract_item_start,
    (HLOption.HL_PROC_EXTRACT_ITEM_START, None):
        _set_proc_extract_item_start,

    (HLOption.HL_PROC_EXTRACT_ITEM_END, hlVoidPtr):
        _set_proc_extract_item_end,
    (HLOption.HL_PROC_EXTRACT_ITEM_END, None):
        _set_proc_extract_item_end,

    (HLOption.HL_PROC_EXTRACT_FILE_PROGRESS, hlVoidPtr):
        _set_proc_extract_file_progress,
    (HLOption.HL_PROC_EXTRACT_FILE_PROGRESS, None):
        _set_proc_extract_file_progress,

    (HLOption.HL_PROC_VALIDATE_FILE_PROGRESS, hlVoidPtr):
        _set_proc_validate_file_progress,
    (HLOption.HL_PROC_VALIDATE_FILE_PROGRESS, None):
        _set_proc_validate_file_progress,

    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS, hlVoidPtr):
        _set_proc_defragment_progress,
    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS, None):
        _set_proc_defragment_progress,

    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS_EX, hlVoidPtr):
        _set_proc_defragment_progress_ex,
    (HLOption.HL_PROC_DEFRAGMENT_PROGRESS_EX, None):
        _set_proc_defragment_progress_ex,
}


def set_value(option, value, hl_type=None):
    """Sets the value associated with a given option.

    This corresponds to the hlSetBool(), hlSetString(), etc. functions
    in the C library version of HLLib.

    The value of some options cannot be set.

    Args:
        option: The HLOption to set the value for.

        value: The value to set for the option.

        hl_type: A type such as hlInt, hlString, etc. Setting this to
            something other than None causes this function to attempt
            to set the value as a specific type. If there is no
            support for setting the value of the option for the
            specified type, an HLError will be raised.

    Raises:
        HLError: If the value for the given option cannot be retrieved.
            Reasons include: not supporting setting the value of the
            option, not supporting setting the value of the option given
            the hl_type, the program state being such that the value
            cannot currently be set (e.g. no package bound), etc.
    """
    key = (option, hl_type)
    function = _setters.get(key)

    if function is None:
        raise HLError("Cannot set value for option {0} "
                "given type {1}".format(option, hl_type))

    return function(option, value)


# Ctypes Function Specifications

# hlVoid hlInitialize();
_hl.hlInitialize.argtypes = []
_hl.hlInitialize.restype = None

# hlVoid hlShutdown();
_hl.hlShutdown.argtypes = []
_hl.hlShutdown.restype = None

# Get/Set

# hlBool hlGetBoolean(HLOption eOption);
_hl.hlGetBoolean.argtypes = [hlInt]
_hl.hlGetBoolean.restype = hlBool

# hlBool hlGetBooleanValidate(HLOption eOption, hlBool *pValue);
_hl.hlGetBooleanValidate.argtypes = [hlInt, _c.POINTER(hlBool)]
_hl.hlGetBooleanValidate.restype = hlBool

# hlVoid hlSetBoolean(HLOption eOption, hlBool bValue);
_hl.hlSetBoolean.argtypes = [hlInt, hlBool]
_hl.hlSetBoolean.restype = None

# hlInt hlGetInteger(HLOption eOption);
_hl.hlGetInteger.argtypes = [hlInt]
_hl.hlGetInteger.restype = hlInt

#hlBool hlGetIntegerValidate(HLOption eOption, hlInt *pValue);
_hl.hlGetIntegerValidate.argtypes = [hlInt, _c.POINTER(hlInt)]
_hl.hlGetIntegerValidate.restype = hlBool

# hlVoid hlSetInteger(HLOption eOption, hlInt iValue);
_hl.hlSetInteger.argtypes = [hlInt, hlInt]
_hl.hlSetInteger.restype = None

# hlUInt hlGetUnsignedInteger(HLOption eOption);
_hl.hlGetUnsignedInteger.argtypes = [hlInt]
_hl.hlGetUnsignedInteger.restype = hlUInt

# hlBool hlGetUnsignedIntegerValidate(HLOption eOption, hlUInt *pValue);
_hl.hlGetUnsignedIntegerValidate.argtypes = [hlInt, _c.POINTER(hlUInt)]
_hl.hlGetUnsignedIntegerValidate.restype = hlBool

# hlVoid hlSetUnsignedInteger(HLOption eOption, hlUInt iValue);
_hl.hlSetUnsignedInteger.argtypes = [hlInt, hlUInt]
_hl.hlSetUnsignedInteger.restype = None

# hlLongLong hlGetLongLong(HLOption eOption);
_hl.hlGetLongLong.argtypes = [hlInt]
_hl.hlGetLongLong.restype = hlLongLong

# hlBool hlGetLongLongValidate(HLOption eOption, hlLongLong *pValue);
_hl.hlGetLongLongValidate.argtypes = [hlInt, _c.POINTER(hlLongLong)]
_hl.hlGetLongLongValidate.restype = hlBool

# hlVoid hlSetLongLong(HLOption eOption, hlLongLong iValue);
_hl.hlSetLongLong.argtypes = [hlInt, hlLongLong]
_hl.hlSetLongLong.restype = None

# hlULongLong hlGetUnsignedLongLong(HLOption eOption);
_hl.hlGetUnsignedLongLong.argtypes = [hlInt]
_hl.hlGetUnsignedLongLong.restype = hlULongLong

# hlBool hlGetUnsignedLongLongValidate(HLOption eOption, hlULongLong *pValue);
_hl.hlGetUnsignedLongLongValidate.argtypes = [hlInt, _c.POINTER(hlULongLong)]
_hl.hlGetUnsignedLongLongValidate.restype = hlBool

# hlVoid hlSetUnsignedLongLong(HLOption eOption, hlULongLong iValue);
_hl.hlSetUnsignedLongLong.argtypes = [hlInt, hlULongLong]
_hl.hlSetUnsignedLongLong.restype = None

# hlFloat hlGetFloat(HLOption eOption);
_hl.hlGetFloat.argtypes = [hlInt]
_hl.hlGetFloat.restype = hlFloat

# hlBool hlGetFloatValidate(HLOption eOption, hlFloat *pValue);
_hl.hlGetFloatValidate.argtypes = [hlInt, _c.POINTER(hlFloat)]
_hl.hlGetFloatValidate.restype = hlBool

# hlVoid hlSetFloat(HLOption eOption, hlFloat fValue);
_hl.hlSetFloat.argtypes = [hlInt, hlFloat]
_hl.hlSetFloat.restype = None

# const hlChar *hlGetString(HLOption eOption);
_hl.hlGetString.argtypes = [hlInt]
_hl.hlGetString.restype = hlString

# hlBool hlGetStringValidate(HLOption eOption, const hlChar **pValue);
_hl.hlGetStringValidate.argtypes = [hlInt, _c.POINTER(hlString)]
_hl.hlGetStringValidate.restype = hlBool

# hlVoid hlSetString(HLOption eOption, const hlChar *lpValue);
_hl.hlSetString.argtypes = [hlInt, hlString]
_hl.hlSetString.restype = None

# const hlVoid *hlGetVoid(HLOption eOption);
_hl.hlGetVoid.argtypes = [hlInt]
_hl.hlGetVoid.restype = hlVoidPtr

# hlBool hlGetVoidValidate(HLOption eOption, const hlVoid **pValue);
_hl.hlGetVoidValidate.argtypes = [hlInt, _c.POINTER(hlVoidPtr)]
_hl.hlGetVoidValidate.restype = hlBool

# hlVoid hlSetVoid(HLOption eOption, const hlVoid *pValue);
_hl.hlSetVoid.argtypes = [hlInt, hlVoidPtr]
_hl.hlSetVoid.restype = None

# Attributes

# hlBool hlAttributeGetBoolean(HLAttribute *pAttribute);
_hl.hlAttributeGetBoolean.argtypes = [_c.POINTER(HLAttribute)]
_hl.hlAttributeGetBoolean.restype = hlBool

# hlVoid hlAttributeSetBoolean(HLAttribute *pAttribute,
#       const hlChar *lpName, hlBool bValue);
_hl.hlAttributeSetBoolean.argtypes = [
        _c.POINTER(HLAttribute), hlString, hlBool]
_hl.hlAttributeSetBoolean.restype = None

# hlInt hlAttributeGetInteger(HLAttribute *pAttribute);
_hl.hlAttributeGetInteger.argtypes = [_c.POINTER(HLAttribute)]
_hl.hlAttributeGetInteger.restype = hlInt

# hlVoid hlAttributeSetInteger(HLAttribute *pAttribute,
#       const hlChar *lpName, hlInt iValue);
_hl.hlAttributeSetInteger.argtypes = [_c.POINTER(HLAttribute), hlString, hlInt]
_hl.hlAttributeSetInteger.restype = None

# hlUInt hlAttributeGetUnsignedInteger(HLAttribute *pAttribute);
_hl.hlAttributeGetUnsignedInteger.argtypes = [_c.POINTER(HLAttribute)]
_hl.hlAttributeGetUnsignedInteger.restype = hlInt

# hlVoid hlAttributeSetUnsignedInteger(HLAttribute *pAttribute,
#       const hlChar *lpName, hlUInt uiValue, hlBool bHexadecimal);
_hl.hlAttributeSetUnsignedInteger.argtypes = [
        _c.POINTER(HLAttribute), hlString, hlUInt, hlBool]
_hl.hlAttributeSetUnsignedInteger.restype = None

# hlFloat hlAttributeGetFloat(HLAttribute *pAttribute);
_hl.hlAttributeGetFloat.argtypes = [_c.POINTER(HLAttribute)]
_hl.hlAttributeGetFloat.restype = hlFloat

# hlVoid hlAttributeSetFloat(HLAttribute *pAttribute,
#       const hlChar *lpName, hlFloat fValue);
_hl.hlAttributeSetFloat.argtypes = [_c.POINTER(HLAttribute), hlString, hlFloat]
_hl.hlAttributeSetFloat.restype = None

# const hlChar *hlAttributeGetString(HLAttribute *pAttribute);
_hl.hlAttributeGetString.argtypes = [_c.POINTER(HLAttribute)]
_hl.hlAttributeGetString.restype = hlString

# hlVoid hlAttributeSetString(HLAttribute *pAttribute,
#       const hlChar *lpName, const hlChar *lpValue);
_hl.hlAttributeSetString.argtypes = [
        _c.POINTER(HLAttribute), hlString, hlString]
_hl.hlAttributeSetString.restype = None

# Directory Item

# HLDirectoryItemType hlItemGetType(const HLDirectoryItem *pItem);
_hl.hlItemGetType.argtypes = [hlVoidPtr]
_hl.hlItemGetType.restype = hlInt

# const hlChar *hlItemGetName(const HLDirectoryItem *pItem);
_hl.hlItemGetName.argtypes = [hlVoidPtr]
_hl.hlItemGetName.restype = hlString

# hlUInt hlItemGetID(const HLDirectoryItem *pItem);
_hl.hlItemGetID.argtypes = [hlVoidPtr]
_hl.hlItemGetID.restype = hlUInt

# const hlVoid *hlItemGetData(const HLDirectoryItem *pItem);
_hl.hlItemGetData.argtypes = [hlVoidPtr]
_hl.hlItemGetData.restype = hlVoidPtr

# hlUInt hlItemGetPackage(const HLDirectoryItem *pItem);
_hl.hlItemGetPackage.argtypes = [hlVoidPtr]
_hl.hlItemGetPackage.restype = hlUInt

# HLDirectoryItem *hlItemGetParent(HLDirectoryItem *pItem);
_hl.hlItemGetParent.argtypes = [hlVoidPtr]
_hl.hlItemGetParent.restype = hlVoidPtr

# hlBool hlItemGetSize(const HLDirectoryItem *pItem, hlUInt *pSize);
_hl.hlItemGetSize.argtypes = [hlVoidPtr, _c.POINTER(hlUInt)]
_hl.hlItemGetSize.restype = hlBool

# hlBool hlItemGetSizeEx(const HLDirectoryItem *pItem, hlULongLong *pSize);
_hl.hlItemGetSizeEx.argtypes = [hlVoidPtr, _c.POINTER(hlULongLong)]
_hl.hlItemGetSizeEx.restype = hlBool

# hlBool hlItemGetSizeOnDisk(const HLDirectoryItem *pItem, hlUInt *pSize);
_hl.hlItemGetSizeOnDisk.argtypes = [hlVoidPtr, _c.POINTER(hlUInt)]
_hl.hlItemGetSizeOnDisk.restype = hlBool

# hlBool hlItemGetSizeOnDiskEx(const HLDirectoryItem *pItem,
#       hlULongLong *pSize);
_hl.hlItemGetSizeOnDiskEx.argtypes = [hlVoidPtr, _c.POINTER(hlULongLong)]
_hl.hlItemGetSizeOnDiskEx.restype = hlBool

# hlVoid hlItemGetPath(const HLDirectoryItem *pItem,
#       hlChar *lpPath, hlUInt uiPathSize);
_hl.hlItemGetPath.argtypes = [hlVoidPtr, hlString, hlUInt]
_hl.hlItemGetPath.restype = None

# hlBool hlItemExtract(HLDirectoryItem *pItem, const hlChar *lpPath);
_hl.hlItemExtract.argtypes = [hlVoidPtr, hlString]
_hl.hlItemExtract.restype = hlBool

# Directory Folder

# hlUInt hlFolderGetCount(const HLDirectoryItem *pItem);
_hl.hlFolderGetCount.argtypes = [hlVoidPtr]
_hl.hlFolderGetCount.restype = hlUInt

# HLDirectoryItem *hlFolderGetItem(HLDirectoryItem *pItem, hlUInt uiIndex);
_hl.hlFolderGetItem.argtypes = [hlVoidPtr, hlUInt]
_hl.hlFolderGetItem.restype = hlVoidPtr

# HLDirectoryItem *hlFolderGetItemByName(HLDirectoryItem *pItem,
#       const hlChar *lpName, HLFindType eFind);
_hl.hlFolderGetItemByName.argtypes = [hlVoidPtr, hlString, hlInt]
_hl.hlFolderGetItemByName.restype = hlVoidPtr

# HLDirectoryItem *hlFolderGetItemByPath(HLDirectoryItem *pItem,
#       const hlChar *lpPath, HLFindType eFind);
_hl.hlFolderGetItemByPath.argtypes = [hlVoidPtr, hlString, hlInt]
_hl.hlFolderGetItemByPath.restype = hlVoidPtr

# hlVoid hlFolderSort(HLDirectoryItem *pItem,
#       HLSortField eField, HLSortOrder eOrder, hlBool bRecurse);
_hl.hlFolderSort.argtypes = [hlVoidPtr, hlInt, hlInt, hlBool]
_hl.hlFolderSort.restype = None

# HLDirectoryItem *hlFolderFindFirst(HLDirectoryItem *pFolder,
#       const hlChar *lpSearch, HLFindType eFind);
_hl.hlFolderFindFirst.argtypes = [hlVoidPtr, hlString, hlInt]
_hl.hlFolderFindFirst.restype = hlVoidPtr

# HLDirectoryItem *hlFolderFindNext(HLDirectoryItem *pFolder,
#       HLDirectoryItem *pItem, const hlChar *lpSearch, HLFindType eFind);
_hl.hlFolderFindNext.argtypes = [hlVoidPtr, hlVoidPtr, hlString, hlInt]
_hl.hlFolderFindNext.restype = hlVoidPtr

# hlUInt hlFolderGetSize(const HLDirectoryItem *pItem, hlBool bRecurse);
_hl.hlFolderGetSize.argtypes = [hlVoidPtr, hlBool]
_hl.hlFolderGetSize.restype = hlUInt

# hlULongLong hlFolderGetSizeEx(const HLDirectoryItem *pItem, hlBool bRecurse);
_hl.hlFolderGetSizeEx.argtypes = [hlVoidPtr, hlBool]
_hl.hlFolderGetSizeEx.restype = hlULongLong

# hlUInt hlFolderGetSizeOnDisk(const HLDirectoryItem *pItem, hlBool bRecurse);
_hl.hlFolderGetSizeOnDisk.argtypes = [hlVoidPtr, hlBool]
_hl.hlFolderGetSizeOnDisk.restype = hlUInt

# hlULongLong hlFolderGetSizeOnDiskEx(const HLDirectoryItem *pItem,
#       hlBool bRecurse);
_hl.hlFolderGetSizeOnDiskEx.argtypes = [hlVoidPtr, hlBool]
_hl.hlFolderGetSizeOnDiskEx.restype = hlULongLong

# hlUInt hlFolderGetFolderCount(const HLDirectoryItem *pItem, hlBool bRecurse);
_hl.hlFolderGetFolderCount.argtypes = [hlVoidPtr, hlBool]
_hl.hlFolderGetFolderCount.restype = hlUInt

# hlUInt hlFolderGetFileCount(const HLDirectoryItem *pItem, hlBool bRecurse);
_hl.hlFolderGetFileCount.argtypes = [hlVoidPtr, hlBool]
_hl.hlFolderGetFileCount.restype = hlUInt

# Directory File

# hlUInt hlFileGetExtractable(const HLDirectoryItem *pItem);
_hl.hlFileGetExtractable.argtypes = [hlVoidPtr]
_hl.hlFileGetExtractable.restype = hlUInt

# HLValidation hlFileGetValidation(const HLDirectoryItem *pItem);
_hl.hlFileGetValidation.argtypes = [hlVoidPtr]
_hl.hlFileGetValidation.restype = hlInt

# hlUInt hlFileGetSize(const HLDirectoryItem *pItem);
_hl.hlFileGetSize.argtypes = [hlVoidPtr]
_hl.hlFileGetSize.restype = hlUInt

# hlUInt hlFileGetSizeOnDisk(const HLDirectoryItem *pItem);
_hl.hlFileGetSizeOnDisk.argtypes = [hlVoidPtr]
_hl.hlFileGetSizeOnDisk.restype = hlUInt

# hlBool hlFileCreateStream(HLDirectoryItem *pItem, HLStream **pStream);
_hl.hlFileCreateStream.argtypes = [hlVoidPtr, hlVoidPtr]
_hl.hlFileCreateStream.restype = hlBool

# hlVoid hlFileReleaseStream(HLDirectoryItem *pItem, HLStream *pStream);
_hl.hlFileReleaseStream.argtypes = [hlVoidPtr, hlVoidPtr]
_hl.hlFileReleaseStream.restype = None

# Stream

# HLStreamType hlStreamGetType(const HLStream *pStream);
_hl.hlStreamGetType.argtypes = [hlVoidPtr]
_hl.hlStreamGetType.restype = hlInt

# hlBool hlStreamGetOpened(const HLStream *pStream);
_hl.hlStreamGetOpened.argtypes = [hlVoidPtr]
_hl.hlStreamGetOpened.restype = hlBool

# hlUInt hlStreamGetMode(const HLStream *pStream);
_hl.hlStreamGetMode.argtypes = [hlVoidPtr]
_hl.hlStreamGetMode.restype = hlUInt

# hlBool hlStreamOpen(HLStream *pStream, hlUInt uiMode);
_hl.hlStreamOpen.argtypes = [hlVoidPtr, hlUInt]
_hl.hlStreamOpen.restype = hlBool

# hlVoid hlStreamClose(HLStream *pStream);
_hl.hlStreamClose.argtypes = [hlVoidPtr]
_hl.hlStreamClose.restype = None

# hlUInt hlStreamGetStreamSize(const HLStream *pStream);
_hl.hlStreamGetStreamSize.argtypes = [hlVoidPtr]
_hl.hlStreamGetStreamSize.restype = hlUInt

# hlULongLong hlStreamGetStreamSizeEx(const HLStream *pStream);
_hl.hlStreamGetStreamSizeEx.argtypes = [hlVoidPtr]
_hl.hlStreamGetStreamSizeEx.restype = hlULongLong

# hlUInt hlStreamGetStreamPointer(const HLStream *pStream);
_hl.hlStreamGetStreamPointer.argtypes = [hlVoidPtr]
_hl.hlStreamGetStreamPointer.restype = hlUInt

# hlULongLong hlStreamGetStreamPointerEx(const HLStream *pStream);
_hl.hlStreamGetStreamPointerEx.argtypes = [hlVoidPtr]
_hl.hlStreamGetStreamPointerEx.restype = hlULongLong

# hlUInt hlStreamSeek(HLStream *pStream,
#       hlLongLong iOffset, HLSeekMode eSeekMode);
_hl.hlStreamSeek.argtypes = [hlVoidPtr, hlLongLong, hlInt]
_hl.hlStreamSeek.restype = hlUInt

# hlULongLong hlStreamSeekEx(HLStream *pStream,
#       hlLongLong iOffset, HLSeekMode eSeekMode);
_hl.hlStreamSeekEx.argtypes = [hlVoidPtr, hlLongLong, hlInt]
_hl.hlStreamSeekEx.restype = hlULongLong

# hlBool hlStreamReadChar(HLStream *pStream, hlChar *pChar);
_hl.hlStreamReadChar.argtypes = [hlVoidPtr, hlString]
_hl.hlStreamReadChar.restype = hlBool

# hlUInt hlStreamRead(HLStream *pStream, hlVoid *lpData, hlUInt uiBytes);
_hl.hlStreamRead.argtypes = [hlVoidPtr, hlVoidPtr, hlUInt]
_hl.hlStreamRead.restype = hlUInt

# hlBool hlStreamWriteChar(HLStream *pStream, hlChar iChar);
_hl.hlStreamWriteChar.argtypes = [hlVoidPtr, hlChar]
_hl.hlStreamWriteChar.restype = hlBool

# hlUInt hlStreamWrite(HLStream *pStream,
#       const hlVoid *lpData, hlUInt uiBytes);
_hl.hlStreamWrite.argtypes = [hlVoidPtr, hlVoidPtr, hlUInt]
_hl.hlStreamWrite.restype = hlUInt

# Package

# hlBool hlBindPackage(hlUInt uiPackage);
_hl.hlBindPackage.argtypes = [hlUInt]
_hl.hlBindPackage.restype = hlBool

# HLPackageType hlGetPackageTypeFromName(const hlChar *lpName);
_hl.hlGetPackageTypeFromName.argtypes = [hlString]
_hl.hlGetPackageTypeFromName.restype = hlInt

# HLPackageType hlGetPackageTypeFromMemory(const hlVoid *lpBuffer,
#       hlUInt uiBufferSize);
_hl.hlGetPackageTypeFromMemory.argtypes = [hlVoidPtr, hlUInt]
_hl.hlGetPackageTypeFromMemory.restype = hlInt

# HLPackageType hlGetPackageTypeFromStream(HLStream *pStream);
_hl.hlGetPackageTypeFromStream.argtypes = [hlVoidPtr]
_hl.hlGetPackageTypeFromStream.restype = hlInt

# hlBool hlCreatePackage(HLPackageType ePackageType, hlUInt *uiPackage);
_hl.hlCreatePackage.argtypes = [hlInt, _c.POINTER(hlUInt)]
_hl.hlCreatePackage.restype = hlBool

# hlVoid hlDeletePackage(hlUInt uiPackage);
_hl.hlDeletePackage.argtypes = [hlUInt]
_hl.hlDeletePackage.restype = None

# HLPackageType hlPackageGetType();
_hl.hlPackageGetType.argtypes = []
_hl.hlPackageGetType.restype = hlInt

# const hlChar *hlPackageGetExtension();
_hl.hlPackageGetExtension.argtypes = []
_hl.hlPackageGetExtension.restype = hlString

# const hlChar *hlPackageGetDescription();
_hl.hlPackageGetDescription.argtypes = []
_hl.hlPackageGetDescription.restype = hlString

# hlBool hlPackageGetOpened();
_hl.hlPackageGetOpened.argtypes = []
_hl.hlPackageGetOpened.restype = hlBool

# hlBool hlPackageOpenFile(const hlChar *lpFileName, hlUInt uiMode);
_hl.hlPackageOpenFile.argtypes = [hlString, hlUInt]
_hl.hlPackageOpenFile.restype = hlBool

# hlBool hlPackageOpenMemory(hlVoid *lpData,
#       hlUInt uiBufferSize, hlUInt uiMode);
_hl.hlPackageOpenMemory.argtypes = [hlVoidPtr, hlUInt, hlUInt]
_hl.hlPackageOpenMemory.restype = hlBool

# hlBool hlPackageOpenProc(hlVoid *pUserData, hlUInt uiMode);
_hl.hlPackageOpenProc.argtypes = [hlVoidPtr, hlUInt]
_hl.hlPackageOpenProc.restype = hlBool

# hlBool hlPackageOpenStream(HLStream *pStream, hlUInt uiMode);
_hl.hlPackageOpenStream.argtypes = [hlVoidPtr, hlUInt]
_hl.hlPackageOpenStream.restype = hlBool

# hlVoid hlPackageClose();
_hl.hlPackageClose.argtypes = []
_hl.hlPackageClose.restype = None

# hlBool hlPackageDefragment();
_hl.hlPackageDefragment.argtypes = []
_hl.hlPackageDefragment.restype = hlBool

# HLDirectoryItem *hlPackageGetRoot();
_hl.hlPackageGetRoot.argtypes = []
_hl.hlPackageGetRoot.restype = hlVoidPtr

# hlUInt hlPackageGetAttributeCount();
_hl.hlPackageGetAttributeCount.argtypes = []
_hl.hlPackageGetAttributeCount.restype = hlUInt

# const hlChar *hlPackageGetAttributeName(HLPackageAttribute eAttribute);
_hl.hlPackageGetAttributeName.argtypes = [hlInt]
_hl.hlPackageGetAttributeName.restype = hlString

# hlBool hlPackageGetAttribute(HLPackageAttribute eAttribute,
#       HLAttribute *pAttribute);
_hl.hlPackageGetAttribute.argtypes = [hlInt, _c.POINTER(HLAttribute)]
_hl.hlPackageGetAttribute.restype = hlBool

# hlUInt hlPackageGetItemAttributeCount();
_hl.hlPackageGetItemAttributeCount.argtypes = []
_hl.hlPackageGetItemAttributeCount.restype = hlUInt

# const hlChar *hlPackageGetItemAttributeName(HLPackageAttribute eAttribute);
_hl.hlPackageGetItemAttributeName.argtypes = [hlInt]
_hl.hlPackageGetItemAttributeName.restype = hlString

# hlBool hlPackageGetItemAttribute(const HLDirectoryItem *pItem,
#       HLPackageAttribute eAttribute, HLAttribute *pAttribute);
_hl.hlPackageGetItemAttribute.argtypes = [
        hlVoidPtr, hlInt, _c.POINTER(HLAttribute)]
_hl.hlPackageGetItemAttribute.restype = hlBool

# hlBool hlPackageGetExtractable(const HLDirectoryItem *pFile,
#       hlBool *pExtractable);
_hl.hlPackageGetExtractable.argtypes = [hlVoidPtr, _c.POINTER(hlBool)]
_hl.hlPackageGetExtractable.restype = hlBool

# hlBool hlPackageGetFileSize(const HLDirectoryItem *pFile, hlUInt *pSize);
_hl.hlPackageGetFileSize.argtypes = [hlVoidPtr, _c.POINTER(hlUInt)]
_hl.hlPackageGetFileSize.restype = hlBool

# hlBool hlPackageGetFileSizeOnDisk(const HLDirectoryItem *pFile,
#       hlUInt *pSize);
_hl.hlPackageGetFileSizeOnDisk.argtypes = [hlVoidPtr, _c.POINTER(hlUInt)]
_hl.hlPackageGetFileSizeOnDisk.restype = hlBool

# hlBool hlPackageCreateStream(const HLDirectoryItem *pFile,
#       HLStream **pStream);
_hl.hlPackageCreateStream.argtypes = [hlVoidPtr, _c.POINTER(hlVoidPtr)]
_hl.hlPackageCreateStream.restype = hlBool

# hlVoid hlPackageReleaseStream(HLStream *pStream);
_hl.hlPackageReleaseStream.argtypes = [hlVoidPtr]
_hl.hlPackageReleaseStream.restype = None

# const hlChar *hlNCFFileGetRootPath();
_hl.hlNCFFileGetRootPath.argtypes = []
_hl.hlNCFFileGetRootPath.restype = hlString

# hlVoid hlNCFFileSetRootPath(const hlChar *lpRootPath);
_hl.hlNCFFileSetRootPath.argtypes = []
_hl.hlNCFFileSetRootPath.restype = None

# hlBool hlWADFileGetImageSizePaletted(const HLDirectoryItem *pFile,
#       hlUInt *uiPaletteDataSize, hlUInt *uiPixelDataSize);
_hl.hlWADFileGetImageSizePaletted.argtypes = [
        hlVoidPtr, _c.POINTER(hlUInt), _c.POINTER(hlUInt)]
_hl.hlWADFileGetImageSizePaletted.restype = hlBool

# hlBool hlWADFileGetImageDataPaletted(const HLDirectoryItem *pFile,
#       hlUInt *uiWidth, hlUInt *uiHeight, hlByte **lpPaletteData,
#       hlByte **lpPixelData);
_hl.hlWADFileGetImageDataPaletted.argtypes = [
        hlVoidPtr, _c.POINTER(hlUInt), _c.POINTER(hlUInt),
        _c.POINTER(hlByte), _c.POINTER(hlByte)]
_hl.hlWADFileGetImageDataPaletted.restype = hlBool

# hlBool hlWADFileGetImageSize(const HLDirectoryItem *pFile,
#       hlUInt *uiPixelDataSize);
_hl.hlWADFileGetImageSize.argtypes = [hlVoidPtr, hlUInt]
_hl.hlWADFileGetImageSize.restype = hlBool

# hlBool hlWADFileGetImageData(const HLDirectoryItem *pFile,
#       hlUInt *uiWidth, hlUInt *uiHeight, hlByte **lpPixelData);
_hl.hlWADFileGetImageData.argtypes = [
        hlVoidPtr, _c.POINTER(hlUInt), _c.POINTER(hlUInt),
        _c.POINTER(_c.POINTER(hlByte))]
_hl.hlWADFileGetImageData.restype = hlBool


# Version Check

_version_number = get_value(HLOption.HL_VERSION, hlUInt)

if HL_VERSION_NUMBER != _version_number:
    raise HLError("Python module version ({0}) and C library version ({1}) "
            "do not match.".format(HL_VERSION_NUMBER, _version_number))
