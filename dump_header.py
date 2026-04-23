import ctypes
import struct

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
FILE_MAP_READ = 0x0004
kernel32.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
kernel32.OpenFileMappingW.restype = ctypes.c_void_p
kernel32.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
kernel32.MapViewOfFile.restype = ctypes.c_void_p
kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
kernel32.UnmapViewOfFile.restype = ctypes.c_int
kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype = ctypes.c_int

name = 'Global\\HWiNFO_SENS_SM2'
h = kernel32.OpenFileMappingW(FILE_MAP_READ, False, name)
print('handle:', h)
if not h:
    print('open failed:', ctypes.get_last_error())
    raise SystemExit(1)

p = kernel32.MapViewOfFile(h, FILE_MAP_READ, 0, 0, 128)
print('ptr:', hex(p) if p else p)
if not p:
    print('map failed:', ctypes.get_last_error())
    kernel32.CloseHandle(h)
    raise SystemExit(1)

b = ctypes.string_at(p, 128)
print('hex:', b.hex(' '))
print('ascii sig:', b[:4])
for off in range(0, 64, 4):
    print(f'u32 @{off:02}:', struct.unpack_from('<I', b, off)[0])
print('u64 @12:', struct.unpack_from('<Q', b, 12)[0])
print('u64 @16:', struct.unpack_from('<Q', b, 16)[0])

kernel32.UnmapViewOfFile(p)
kernel32.CloseHandle(h)
