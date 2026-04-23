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

NAMES_TO_TRY = [
    'Global\\HWiNFO_SENS_SM2',
    'HWiNFO_SENS_SM2',
    'Global\\HWiNFO_SENS_SM',
    'HWiNFO_SENS_SM',
    'Global\\HWiNFO_SENS',
    'HWiNFO_SENS',
]


def try_open(name):
    handle = kernel32.OpenFileMappingW(FILE_MAP_READ, False, name)
    if not handle:
        err = ctypes.get_last_error()
        return None, err
    return handle, 0


def read_handle(handle, size=256):
    ptr = kernel32.MapViewOfFile(handle, FILE_MAP_READ, 0, 0, size)
    if not ptr:
        err = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(f'MapViewOfFile failed, error {err}')
    try:
        return ctypes.string_at(ptr, size)
    finally:
        kernel32.UnmapViewOfFile(ptr)
        kernel32.CloseHandle(handle)


print('=' * 60)
print('HWiNFO shared memory diagnostic')
print('=' * 60)

found = False
for name in NAMES_TO_TRY:
    handle, err = try_open(name)
    if handle:
        try:
            buf = read_handle(handle)
        except Exception as e:
            print(f'[FOUND] {name} but map/read failed: {e}')
            continue

        sig = struct.unpack_from('<I', buf, 0)[0]
        ver = struct.unpack_from('<I', buf, 4)[0]
        rev = struct.unpack_from('<I', buf, 8)[0]
        n_sensors = struct.unpack_from('<I', buf, 24)[0]
        n_readings = struct.unpack_from('<I', buf, 32)[0]

        print(f'\n[FOUND] {name}')
        print(f' Signature : 0x{sig:08X} (expected 0x53574548 = HEWS)')
        print(f' Version   : {ver}  Revision: {rev}')
        print(f' Sensors   : {n_sensors}')
        print(f' Readings  : {n_readings}')
        print(f' First 32 bytes: {buf[:32].hex(" ")}')

        if sig == 0x53574548:
            print(' STATUS: signature OK, this is the right mapping')
            found = True
        elif sig == 0:
            print(' STATUS: all zeros, mapping exists but HWiNFO has not written to it yet')
        else:
            print(' STATUS: unexpected signature, wrong layout or version mismatch')
    else:
        reason = 'not found' if err == 2 else f'access denied / error {err}'
        print(f'[miss] {name}, {reason}')

if not found:
    print('\n[RESULT] No valid HWiNFO mapping found.')
    print('Checklist:')
    print(' 1. Is HWiNFO64 running?')
    print(' 2. Is the sensor window open?')
    print(' 3. Is Shared Memory Support checked?')
    print(' 4. Try running this script as Administrator')
    print(' 5. If HWiNFO runs as admin, Python must too, or vice versa')
