import claripy
from angr import SimProcedure
from angr.procedures import SIM_PROCEDURES
from angr.errors import SimProcedureError

from .helper import *
from .sym_struct import * # pylint: disable=W0614

class rt_sigaction(SimProcedure):
    IS_SYSCALL = True

    def run(self, signum, act, oldact):
        # TODO: do real signal registery?
        if not test_concrete_value(self, oldact, 0):
            sigaction(oldact).store_all(self)
        return errno_success(self)


class rt_sigprocmask(SimProcedure):
    IS_SYSCALL = True

    def run(self, how, set, oldset):
        # TODO: do real signal registery?
        if not test_concrete_value(self, oldset, 0):
            self.state.memory.store(oldset, self.state.se.BVS('oldset', 128 * 8))
        return errno_success(self)
            

class connect(SimProcedure):
    IS_SYSCALL = True

    def run(self, sockfd, addr, addrlen):
        # NOTE: recv from angr == read, so connect does nothing
        # TODO: deal with sockaddr?
        return self.state.posix.open(sockfd)
        

class access(SimProcedure):
    IS_SYSCALL = True

    def run(self, pathname, mode):
        return self.state.se.BVS("access", 32)


class getgroups(SimProcedure):
    IS_SYSCALL = True

    def run(self, size, list):
        # TODO: actually read groups to state
        return self.state.se.BVS('getgroups', 32)


class setgroups(SimProcedure):
    IS_SYSCALL = True

    def run(self, size, list):
        # TODO: actually set groups to state
        return errno_success(self)


class getdents(SimProcedure):
    IS_SYSCALL = True

    def run(self, fd, dirp, count):
        linux_dirent(dirp).store_all(self)
        return errno_success(self)


class getdents64(SimProcedure):
    IS_SYSCALL = True

    def run(self, fd, dirp, count):
        linux_dirent64(dirp).store_all(self)
        return errno_success(self)


class getpriority(SimProcedure):
    IS_SYSCALL = True
    
    def run(self, which, who):
        '''
        The value which is one of PRIO_PROCESS, PRIO_PGRP, or PRIO_USER, and
        who is interpreted relative to which (a process identifier for
        PRIO_PROCESS, process group identifier for PRIO_PGRP, and a user ID
        for PRIO_USER).  A zero value for who denotes (respectively) the
        calling process, the process group of the calling process, or the
        real user ID of the calling process.
        '''
        return self.state.se.BVS('getpriority', 32)


class setpriority(SimProcedure):
    IS_SYSCALL = True

    def run(self, which, who, prio):
        # TODO: add priority to state
        return errno_success(self)


class arch_prctl(SimProcedure):
    IS_SYSCALL = True
    
    ARCH_SET_GS = 0x1001
    ARCH_SET_FS = 0x1002
    ARCH_GET_FS = 0x1003
    ARCH_GET_GS = 0x1004

    def run(self, code, addr):
        if self.state.se.symbolic(code):
            raise Exception("what to do here?")
        if test_concrete_value(self, code, self.ARCH_SET_GS):
            self.state.regs.gs = addr
        elif test_concrete_value(self, code, self.ARCH_SET_FS):
            self.state.regs.fs = addr
        elif test_concrete_value(self, code, self.ARCH_GET_GS):
            self.state.memory.store(addr, self.state.regs.gs)
        elif test_concrete_value(self, code, self.ARCH_GET_FS):
            self.state.memory.store(addr, self.state.regs.Fs)
        return errno_success(self)


class set_tid_address(SimProcedure):
    IS_SYSCALL = True

    def run(self, tidptr):
        # Currently we have no multiple process
        # so no set_child_tid or clear_child_tid
        return self.state.se.BVS('set_tid_address', 32)

    
class kill(SimProcedure):
    IS_SYSCALL = True

    def run(self, pid, sig):
        # TODO: manager signal
        return errno_success(self)


class get_robust_list(SimProcedure):
    IS_SYSCALL = True

    def run(self, head, length):
        self.state.memory.store(head, self.state.robust_list_head)
        self.state.memory.store(length, self.state.robust_list_size)
        return errno_success(self)


class set_robust_list(SimProcedure):
    IS_SYSCALL = True

    def run(self, head, length):
        self.state.robust_list_head = head
        self.state.libc.max_robust_size = 0x20
        if self.state.se.symbolic(length):
            length = minmax(self, length, self.state.libc.max_robust_size)
        else:
            length = self.state.se.eval(length)
        self.state.robust_list_size = length
        for i in range(length):
            robust_list_head(head + i * robust_list_head.size).store_all(self) # pylint: disable=E1101
        return errno_success(self)


class nanosleep(SimProcedure):
    IS_SYSCALL = True

    def run(self, req, rem):
        timespec(rem).store_all(self)
        return errno_success(self)


class sysinfo(SimProcedure):
    IS_SYSCALL = True

    def run(self, info):
        sysinfo_t(info).store_all(self)
        return errno_success(self)


class execve(SimProcedure):
    IS_SYSCALL = True

    def run(self, filename, argv, envp):
        # TODO: do nothing here
        return errno_success(self)


class exit_group(SimProcedure):
    IS_SYSCALL = True
    NO_RET = True

    def run(self, status):
        self.exit(status)


class futex(SimProcedure):
    IS_SYSCALL = True

    def run(self, uaddr, futex_op, val, timeout, uaddr2, val3):
        # do nothing
        return self.state.se.BVS('futex', 32)


class readlink(SimProcedure):
    IS_SYSCALL = True

    def run(self, path, buf, bufsize):
        self.state.memory.store(buf, self.state.se.BVS('readlink', bufsize * 8))
        return errno_success(self)

    
class alarm(SimProcedure):
    IS_SYSCALL = True

    def run(self, seconds):
        return self.state.se.BVS('alarm', 32)