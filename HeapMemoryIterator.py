# "What's the memory limit on SoloLearn?" : https://www.sololearn.com/Discuss/181365/?ref=app
#   None of the easy imports could I find; I could ask a shell but didn't like that...
#   So stdlib / Windows 32 API:
import ctypes
import os

SIZE_T = ctypes.c_ulong
HANDLE = ctypes.c_void_p 
ULONG_PTR = ctypes.c_ulong
DWORD = ctypes.c_ulong 
BYTE = ctypes.c_ubyte

INVALID_HANDLE_VALUE = -1
TH32CS_SNAPHEAPLIST = 0x00000001 # ctypes.c_ulong()

kerneldll = ctypes.windll.kernel32  # ctypes.cdll.coredll (CE)

_close_handle = kerneldll.CloseHandle
_create_snapshot = kerneldll.CreateToolhelp32Snapshot
_create_snapshot.reltype=ctypes.c_long
_create_snapshot.argtypes=[ctypes.c_int, ctypes.c_int]
# _close_snapshot = kerneldll.CloseToolhelp32Snapshot  # CE
_heap_list_first = kerneldll.Heap32ListFirst
_heap_list_next = kerneldll.Heap32ListNext
_heap_first = kerneldll.Heap32First
_heap_next = kerneldll.Heap32Next

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms683443(v=vs.85).aspx
class HEAPENTRY32(ctypes.Structure):
  _fields_ = [('dwSize', SIZE_T),
              ('hHandle', HANDLE),
              ('dwAddress', ULONG_PTR),
              ('dwBlockSize', SIZE_T),
              ('dwFlags', DWORD),
              ('dwLockCount', DWORD),
              ('dwResvd', DWORD),
              ('th32ProcessID', DWORD),
              ('th32HeapID', ULONG_PTR)]
              
#https://msdn.microsoft.com/en-us/library/windows/desktop/ms683449(v=vs.85).aspx              
class HEAPLIST32(ctypes.Structure):
  _fields_ = [('dwSize', SIZE_T),
              ('th32ProcessID', DWORD),
              ('th32HeapID', ULONG_PTR),
              ('dwFlags', DWORD)]
              
def _process_memory_info(pid):
  heap_size = 0
  heap_list = HEAPLIST32()
  heap_entry = HEAPENTRY32()

  heap_list.dwSize = ctypes.sizeof(HEAPLIST32)
  heap_entry.dwSize = ctypes.sizeof(HEAPENTRY32)

  handle = _create_snapshot(TH32CS_SNAPHEAPLIST, pid)
  if handle == INVALID_HANDLE_VALUE:
    return {}
  
  if not _heap_list_first(handle, ctypes.pointer(heap_list)):
    #_close_snapshot(handle) #CE
    _close_handle(handle)
    return {}
  
  more_heaps = True
  while (more_heaps):
    # print(heap_list.dwSize, heap_list.th32ProcessID, heap_list.th32HeapID, heap_list.dwFlags);
    # print(handle, ctypes.pointer(heap_entry))
    if _heap_first(ctypes.pointer(heap_entry), heap_list.th32ProcessID, heap_list.th32HeapID):
      more_entries = True
      while more_entries:
        heap_size += heap_entry.dwBlockSize
        heap_entry.dwSize = ctypes.sizeof(HEAPENTRY32)
        more_entries = _heap_next(ctypes.pointer(heap_entry))
      heap_list.dwSize = ctypes.sizeof(HEAPLIST32)
      more_heaps = _heap_list_next(handle, ctypes.pointer(heap_list))    
    
  #_close_snapshot(handle)  # CE
  _close_handle(handle)

  return {'HeapSize':heap_size}

myPID=os.getpid()
print("Bytes available to Python {0}".format(_process_memory_info(myPID)))
