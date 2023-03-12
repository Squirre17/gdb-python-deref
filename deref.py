import gdb
import functools
from typing import Callable, Any

ulp = gdb.lookup_type('unsigned long').pointer()

def only_when_running(func):

    @functools.wraps(func)
    def wrapper(*args):
        if gdb.selected_inferior() is None:
            print("[-] Process is not running, cannot use this cmd")
            return
        return func(*args)
    return wrapper

import traceback
def handle_exception(func : Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args , **kwargs) -> Any:
        try :
            return func(*args, **kwargs)
        except:
            print("[-] Exception occur!")
            print(traceback.format_exc())
    return wrapper

class DereferenceLinkedList(gdb.Command):
    def __init__(self):
        super().__init__("dll", gdb.COMMAND_USER)

    @only_when_running
    @handle_exception
    @DeprecationWarning
    def do_invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) != 2:
            print("[-] Usage: dll <struct_ptr> <node_ptr_offset>")
            return
        
        struct_ptr = args[0]
        print("[D] struct_ptr is " + repr(struct_ptr))

        node_ptr_offset = int(args[1], 0)
        node_ptr_type = ulp  # assume there no source code and debug info
        ptr_val = gdb.parse_and_eval(struct_ptr)
        node_ptr_val = ptr_val + node_ptr_offset
        node_ptr = gdb.Value(int(node_ptr_val)).cast(node_ptr_type)

        print('[D] node_ptr is ' + repr(hex(int(node_ptr))))
        
        node_ptr_deref = int(struct_ptr, 0x10)
        idx = 1
        while node_ptr:
            try :
                addr = hex(int(node_ptr_deref))
                off = node_ptr_offset // 8
                gdb.execute(f"x/{off}gx {addr}")
            except gdb.MemoryError:
                break
            print(f"   \t↓ [{idx}]")
            idx += 1
            node_ptr_deref = node_ptr.dereference()

            node_ptr_val = node_ptr_deref + node_ptr_offset
            node_ptr = gdb.Value(int(node_ptr_val)).cast(node_ptr_type)
    
    node_ptr_type = "mylist"
    tag           = "next"

    @only_when_running
    @handle_exception
    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) < 1:
            print("[-] Usage: dll <address> [struct name] [next tag] [max depth]")
            return

        # memorize struct name and tag
        try:
            ptr_type = args[1]
            self.node_ptr_type = ptr_type
            tag = args[2]
            self.tag = tag
            md = args[3]
            try:
                self.max_depth = int(md)
            except ValueError:
                self.max_depth = int(md, 16)
            except Exception as e:
                raise e
        except IndexError:
            pass

        struct_ptr = args[0]
        ptr_val = gdb.parse_and_eval(struct_ptr)

        ptr_of_type = gdb.lookup_type(self.node_ptr_type).pointer()
        node_ptr = gdb.Value(int(ptr_val)).cast(ptr_of_type)
        idx = 0
        while node_ptr:
            print(f"[{idx}]", end="")
            print(node_ptr.dereference())
            # node_ptr = node_ptr.cast(ptr_of_type)
            node_ptr = node_ptr[self.tag]            # Replace with your node tag
            node_ptr = node_ptr.cast(ptr_of_type)
            idx += 1
            if idx > self.max_depth:
                break

DereferenceLinkedList()
