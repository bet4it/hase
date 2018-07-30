from __future__ import absolute_import, division, print_function

import os
import mmap
import ctypes as ct
from typing import Generator

from .consts import perf_event_header
from .snapshot import EVENTS
from ..mmap import MMap


def perf_events(trace_file):
    # type: (str) -> Generator[ct.Structure, None, None]

    with open(trace_file, "rb+") as f:
        fd = f.fileno()
        size = os.fstat(fd).st_size
        with MMap(fd, size, mmap.PROT_READ, mmap.MAP_SHARED) as mm:
            header_size = ct.sizeof(perf_event_header)
            i = 0
            while i != size:
                assert (size - i) >= header_size
                ev = perf_event_header.from_address(mm.addr + i)
                struct_factory = EVENTS.get(ev.type)
                if struct_factory is None:
                    raise Exception("unexpected perf_event type: %d",
                                    ev.type)
                struct_type = struct_factory(ev.size)
                struct_size = ct.sizeof(struct_type)
                assert (size - i) >= struct_size
                struct = struct_type.from_address(mm.addr + i)

                yield struct

                i += ev.size
