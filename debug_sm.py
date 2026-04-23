import ctypes
from ctypes import wintypes

ntdll = ctypes.windll.ntdll
kernel32 = ctypes.windll.kernel32

# Define necessary types
class UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ('Length', wintypes.USHORT),
        ('MaximumLength', wintypes.USHORT),
        ('Buffer', ctypes.c_wchar_p),
    ]

class OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ('Length', wintypes.ULONG),
        ('RootDirectory', ctypes.c_void_p),
        ('ObjectName', ctypes.POINTER(UNICODE_STRING)),
        ('Attributes', wintypes.ULONG),
        ('SecurityDescriptor', ctypes.c_void_p),
        ('SecurityQualityOfService', ctypes.c_void_p),
    ]

# Constants
OBJ_CASE_INSENSITIVE = 0x00000040
SECTION_MAP_READ = 0x0004

# Try to open Global\HWiNFO_SENS_SM2 using NtOpenSection
name_global = UNICODE_STRING()
name_global.Length = len(r'Global\HWiNFO_SENS_SM2') * 2
name_global.MaximumLength = name_global.Length + 2
name_global.Buffer = ctypes.c_wchar_p(r'Global\HWiNFO_SENS_SM2')

obj_attr = OBJECT_ATTRIBUTES()
obj_attr.Length = ctypes.sizeof(OBJECT_ATTRIBUTES)
obj_attr.RootDirectory = None
obj_attr.ObjectName = pointer(name_global)
obj_attr.Attributes = OBJ_CASE_INSENSITIVE
obj_attr.SecurityDescriptor = None
obj_attr.SecurityQualityOfService = None

section_handle = ctypes.c_void_p()
status = ntdll.NtOpenSection(
    ctypes.byref(section_handle),
    SECTION_MAP_READ,
    ctypes.byref(obj_attr)
)

print(f'NtOpenSection(Global\\HWiNFO_SENS_SM2): status=0x{status:08X}, handle={section_handle.value}')

if status == 0:
    # Map the section
    view_size = ctypes.c_ulonglong(0)
    base_address = ctypes.c_void_p()
    status2 = ntdll.NtMapViewOfSection(
        section_handle,
        ctypes.c_void_p(-1),  # Current process
        ctypes.byref(base_address),
        None,
        None,
        None,
        ctypes.byref(view_size),
        1,  # ViewUnmap
        0,
        0
    )
    print(f'NtMapViewOfSection: status=0x{status2:08X}, base=0x{base_address.value}')
    
    if status2 == 0 and base_address.value:
        import struct
        data = ctypes.string_at(base_address.value, 64)
        print(f'First 64 bytes: {data.hex()}')
        
        # Check signature
        sig = struct.unpack('<I', data[:4])[0]
        print(f'Signature: 0x{sig:08X} (want 0x53574548)')
        
        ntdll.NtUnmapViewOfSection(ctypes.c_void_p(-1), base_address)
    kernel32.CloseHandle(section_handle)

# Try session-specific path
import os
session_id = os.getpid()  # Not useful for getting HWiNFO's session

# Try using \BaseNamedObjects\ prefix  
name_bno = UNICODE_STRING()
name_bno.Buffer = ctypes.c_wchar_p(r'\BaseNamedObjects\HWiNFO_SENS_SM2')
name_bno.Length = len(r'\BaseNamedObjects\HWiNFO_SENS_SM2') * 2
name_bno.MaximumLength = name_bno.Length + 2

obj_attr2 = OBJECT_ATTRIBUTES()
obj_attr2.Length = ctypes.sizeof(OBJECT_ATTRIBUTES)
obj_attr2.RootDirectory = None
obj_attr2.ObjectName = ctypes.byref(name_bno)
obj_attr2.Attributes = OBJ_CASE_INSENSITIVE

section_handle2 = ctypes.c_void_p()
status3 = ntdll.NtOpenSection(ctypes.byref(section_handle2), SECTION_MAP_READ, ctypes.byref(obj_attr2))
print(f'\nNtOpenSection(\\BaseNamedObjects\\HWiNFO_SENS_SM2): status=0x{status3:08X}')