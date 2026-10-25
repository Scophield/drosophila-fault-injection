"""Measured worker hardware/memory, without installing a monitoring dependency."""
import ctypes
import os
import platform


def resources():
    result=dict(system=platform.platform(),processor_description=platform.processor(),logical_cpus=os.cpu_count())
    if os.name=='nt':
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k:
            result['processor_model']=winreg.QueryValueEx(k,'ProcessorNameString')[0].strip()
        class Mem(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ['total','available','page_total','page_available','virtual_total','virtual_available','extended']]
        m=Mem();m.length=ctypes.sizeof(m)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            result.update(physical_memory_bytes=m.total,available_memory_bytes=m.available)
        class Counter(ctypes.Structure):
            _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ['peak_working_set','working_set','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private']]
        c=Counter();c.cb=ctypes.sizeof(c)
        current=ctypes.windll.kernel32.GetCurrentProcess;current.restype=ctypes.c_void_p
        probe=ctypes.windll.psapi.GetProcessMemoryInfo
        probe.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counter),ctypes.c_ulong]
        if probe(current(),ctypes.byref(c),c.cb):
            result.update(worker_peak_working_set_bytes=c.peak_working_set,worker_working_set_bytes=c.working_set,worker_private_bytes=c.private)
    else:
        import resource
        result['worker_maxrss_native']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return result
