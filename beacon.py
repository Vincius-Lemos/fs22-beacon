"""Control the Farming Simulator 22 USB beacon from Windows using only the standard library.

Ported from the command bytes in blinkybeacon (pkg/fsbeacon/usbhid.go).
Usage: python beacon.py flash|spin|stop [seconds]
"""
import ctypes
import sys
import time
from ctypes import wintypes

VID, PID = 0x340D, 0x1710

MAGIC = {
    "flash": bytes([0x0, 0xFF, 0x07, 0xFF, 0x50, 0xFF, 0x1C, 0x8E, 0xB0, 0xB8]),
    "spin": bytes([0x0, 0xFF, 0x01, 0x66, 0xC8, 0xFF, 0xAD, 0x52, 0x81, 0xD6]),
    "stop": bytes([0x0, 0xFF, 0x00, 0x00, 0x64, 0x00, 0x32, 0x9E, 0xD7, 0x0D]),
}


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("InterfaceClassGuid", GUID),
                ("Flags", wintypes.DWORD), ("Reserved", ctypes.c_void_p)]


class HIDD_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Size", wintypes.DWORD), ("VendorID", wintypes.USHORT),
                ("ProductID", wintypes.USHORT), ("VersionNumber", wintypes.USHORT)]


setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
hid = ctypes.WinDLL("hid", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

DIGCF_PRESENT = 0x02
DIGCF_DEVICEINTERFACE = 0x10
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
SHARE_RW = 0x03
OPEN_EXISTING = 3
INVALID_HANDLE = ctypes.c_void_p(-1).value

setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p
setupapi.SetupDiGetClassDevsW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]
setupapi.SetupDiEnumDeviceInterfaces.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                                 wintypes.DWORD, ctypes.c_void_p]
setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                                      wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
                                                      ctypes.c_void_p]
setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
hid.HidD_GetHidGuid.argtypes = [ctypes.c_void_p]
hid.HidD_GetAttributes.argtypes = [ctypes.c_void_p, ctypes.POINTER(HIDD_ATTRIBUTES)]
k32.CreateFileW.restype = ctypes.c_void_p
k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                            wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
k32.WriteFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p, wintypes.DWORD,
                          ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]


def find_beacon_path():
    guid = GUID()
    hid.HidD_GetHidGuid(ctypes.byref(guid))
    devs = setupapi.SetupDiGetClassDevsW(ctypes.byref(guid), None, None,
                                         DIGCF_PRESENT | DIGCF_DEVICEINTERFACE)
    try:
        index = 0
        while True:
            iface = SP_DEVICE_INTERFACE_DATA()
            iface.cbSize = ctypes.sizeof(iface)
            if not setupapi.SetupDiEnumDeviceInterfaces(devs, None, ctypes.byref(guid), index,
                                                        ctypes.byref(iface)):
                break
            index += 1
            needed = wintypes.DWORD(0)
            setupapi.SetupDiGetDeviceInterfaceDetailW(devs, ctypes.byref(iface), None, 0,
                                                      ctypes.byref(needed), None)
            buf = ctypes.create_string_buffer(needed.value)
            # cbSize of SP_DEVICE_INTERFACE_DETAIL_DATA_W: 8 on 64-bit, 6 on 32-bit.
            ctypes.c_uint32.from_buffer(buf).value = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
            if not setupapi.SetupDiGetDeviceInterfaceDetailW(devs, ctypes.byref(iface), buf,
                                                             needed, None, None):
                continue
            path = ctypes.wstring_at(ctypes.addressof(buf) + 4)
            handle = k32.CreateFileW(path, GENERIC_READ | GENERIC_WRITE, SHARE_RW, None,
                                     OPEN_EXISTING, 0, None)
            if handle in (None, INVALID_HANDLE):
                continue
            attrs = HIDD_ATTRIBUTES()
            attrs.Size = ctypes.sizeof(attrs)
            ok = hid.HidD_GetAttributes(handle, ctypes.byref(attrs))
            if ok and attrs.VendorID == VID and attrs.ProductID == PID:
                return handle
            k32.CloseHandle(handle)
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(devs)
    return None


OUTPUT_REPORT_LEN = 65  # OutputReportByteLength declared by the beacon (report ID + 64 bytes)


def write(handle, data):
    data = data.ljust(OUTPUT_REPORT_LEN, b"\x00")
    written = wintypes.DWORD(0)
    if not k32.WriteFile(handle, data, len(data), ctypes.byref(written), None):
        raise OSError(ctypes.get_last_error(), "WriteFile failed")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MAGIC:
        print(__doc__)
        return 1
    mode = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0

    handle = find_beacon_path()
    if handle is None:
        print("Beacon not found (VID 340D / PID 1710).")
        return 1
    if mode == "stop":
        print("Beacon found. Turning it off.")
    else:
        print(f"Beacon found. Sending '{mode}' for {seconds:g}s...")
    try:
        end = time.time() + seconds
        # The game resends the command every few seconds to keep the beacon awake.
        while True:
            write(handle, MAGIC[mode])
            if mode == "stop" or time.time() >= end:
                break
            time.sleep(2)
        if mode != "stop":
            write(handle, MAGIC["stop"])
            print("Stopped.")
    finally:
        k32.CloseHandle(handle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
