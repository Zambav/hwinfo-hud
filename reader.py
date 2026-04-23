"""
HWiNFO64 Shared Memory Reader
Built from the official hwisenssm2.h SDK header.
"""
import ctypes
import logging

logger = logging.getLogger(__name__)

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

SM_NAME = "Global\\HWiNFO_SENS_SM2"
MUTEX_NAME = "Global\\HWiNFO_SM2_MUTEX"

FILE_MAP_READ = 0x0004
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
SIGNATURE_ACTIVE = 0x53695748  # "HWiS"
SIGNATURE_DEAD = 0x44414544    # "DEAD"

STRING_LEN = 128
UNIT_LEN = 16

kernel32.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
kernel32.OpenFileMappingW.restype = ctypes.c_void_p
kernel32.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
kernel32.MapViewOfFile.restype = ctypes.c_void_p
kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
kernel32.UnmapViewOfFile.restype = ctypes.c_int
kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype = ctypes.c_int
kernel32.OpenMutexW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
kernel32.OpenMutexW.restype = ctypes.c_void_p
kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
kernel32.WaitForSingleObject.restype = ctypes.c_uint32
kernel32.ReleaseMutex.argtypes = [ctypes.c_void_p]
kernel32.ReleaseMutex.restype = ctypes.c_int

READING_TYPES = {
    0: "none",
    1: "temp",
    2: "voltage",
    3: "fan",
    4: "current",
    5: "power",
    6: "clock",
    7: "usage",
    8: "other",
}


class HWiNFOHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("signature", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("revision", ctypes.c_uint32),
        ("poll_time", ctypes.c_int64),
        ("sensor_offset", ctypes.c_uint32),
        ("sensor_size", ctypes.c_uint32),
        ("sensor_count", ctypes.c_uint32),
        ("reading_offset", ctypes.c_uint32),
        ("reading_size", ctypes.c_uint32),
        ("reading_count", ctypes.c_uint32),
        ("polling_period", ctypes.c_uint32),
    ]


class HWiNFOSensor(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("sensor_id", ctypes.c_uint32),
        ("sensor_inst", ctypes.c_uint32),
        ("name_orig", ctypes.c_char * STRING_LEN),
        ("name_user", ctypes.c_char * STRING_LEN),
    ]


class HWiNFOReading(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("reading_type", ctypes.c_uint32),
        ("sensor_index", ctypes.c_uint32),
        ("reading_id", ctypes.c_uint32),
        ("label_orig", ctypes.c_char * STRING_LEN),
        ("label_user", ctypes.c_char * STRING_LEN),
        ("unit", ctypes.c_char * UNIT_LEN),
        ("value", ctypes.c_double),
        ("value_min", ctypes.c_double),
        ("value_max", ctypes.c_double),
        ("value_avg", ctypes.c_double),
    ]


def decode_cstr(buf):
    return buf.decode("utf-8", "ignore").rstrip("\x00").strip()


def _acquire_mutex():
    h = kernel32.OpenMutexW(SYNCHRONIZE, False, MUTEX_NAME)
    if not h:
        return None
    result = kernel32.WaitForSingleObject(h, 100)
    if result == WAIT_OBJECT_0:
        return h
    kernel32.CloseHandle(h)
    return None


def _release_mutex(h):
    if h:
        kernel32.ReleaseMutex(h)
        kernel32.CloseHandle(h)


def _open_mapping():
    hmap = kernel32.OpenFileMappingW(FILE_MAP_READ, False, SM_NAME)
    if not hmap:
        err = ctypes.get_last_error()
        if err == 2:
            raise RuntimeError("Shared memory not found. Is HWiNFO64 running with the sensor window open and Shared Memory Support enabled?")
        if err == 5:
            raise RuntimeError("Access denied. Run HWiNFO64 and this server with the same privilege level.")
        raise RuntimeError(f"OpenFileMappingW failed, error {err}")
    ptr = kernel32.MapViewOfFile(hmap, FILE_MAP_READ, 0, 0, 0)
    if not ptr:
        err = ctypes.get_last_error()
        kernel32.CloseHandle(hmap)
        raise RuntimeError(f"MapViewOfFile failed, error {err}")
    return hmap, ptr


def get_debug_info():
    try:
        hmap, ptr = _open_mapping()
    except Exception as e:
        return {"active_name": None, "header_ok": False, "results": [{"name": SM_NAME, "found": False, "error": str(e)}]}

    mutex = _acquire_mutex()
    try:
        hdr_size = ctypes.sizeof(HWiNFOHeader)
        buf = ctypes.string_at(ptr, hdr_size)
        hdr = HWiNFOHeader.from_buffer_copy(buf)
        return {
            "active_name": SM_NAME,
            "header_ok": hdr.signature == SIGNATURE_ACTIVE,
            "results": [{
                "name": SM_NAME,
                "found": True,
                "signature": hdr.signature,
                "signature_hex": f"0x{hdr.signature:08X}",
                "version": hdr.version,
                "revision": hdr.revision,
                "sensor_offset": hdr.sensor_offset,
                "sensor_size": hdr.sensor_size,
                "sensor_count": hdr.sensor_count,
                "reading_offset": hdr.reading_offset,
                "reading_size": hdr.reading_size,
                "reading_count": hdr.reading_count,
                "polling_period": hdr.polling_period,
                "raw_32": buf[:32].hex(" "),
            }]
        }
    finally:
        _release_mutex(mutex)
        kernel32.UnmapViewOfFile(ptr)
        kernel32.CloseHandle(hmap)


def read_hwinfo():
    hmap, ptr = _open_mapping()
    mutex = _acquire_mutex()
    try:
        hdr = HWiNFOHeader.from_buffer_copy(ctypes.string_at(ptr, ctypes.sizeof(HWiNFOHeader)))

        if hdr.signature == SIGNATURE_DEAD:
            raise RuntimeError("HWiNFO shared memory is marked DEAD. Sensor window may be closed.")
        if hdr.signature != SIGNATURE_ACTIVE:
            raise RuntimeError(f"Bad signature 0x{hdr.signature:08X}, expected 0x{SIGNATURE_ACTIVE:08X} ('HWiS')")

        sensors = []
        for i in range(hdr.sensor_count):
            offset = hdr.sensor_offset + i * hdr.sensor_size
            raw = ctypes.string_at(ptr + offset, ctypes.sizeof(HWiNFOSensor))
            s = HWiNFOSensor.from_buffer_copy(raw)
            name = decode_cstr(s.name_user) or decode_cstr(s.name_orig)
            sensors.append(name)

        readings = []
        for i in range(hdr.reading_count):
            offset = hdr.reading_offset + i * hdr.reading_size
            raw = ctypes.string_at(ptr + offset, ctypes.sizeof(HWiNFOReading))
            r = HWiNFOReading.from_buffer_copy(raw)
            label = decode_cstr(r.label_user) or decode_cstr(r.label_orig)
            readings.append({
                "type": READING_TYPES.get(r.reading_type, "other"),
                "sensor": sensors[r.sensor_index] if r.sensor_index < len(sensors) else "?",
                "label": label,
                "unit": decode_cstr(r.unit),
                "value": round(r.value, 3),
                "min": round(r.value_min, 3),
                "max": round(r.value_max, 3),
                "avg": round(r.value_avg, 3),
            })

        return {
            "meta": {
                "mapping_name": SM_NAME,
                "version": hdr.version,
                "revision": hdr.revision,
                "sensor_count": hdr.sensor_count,
                "reading_count": hdr.reading_count,
                "polling_period": hdr.polling_period,
            },
            "sensors": [{"name": s} for s in sensors],
            "readings": readings,
        }
    finally:
        _release_mutex(mutex)
        kernel32.UnmapViewOfFile(ptr)
        kernel32.CloseHandle(hmap)


if __name__ == "__main__":
    import json
    print(json.dumps(get_debug_info(), indent=2))
