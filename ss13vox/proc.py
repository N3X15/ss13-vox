# Logical representation of an init proc, so we can break it up.
import math
from typing import List, Dict
class Proc(object):
    def __init__(self, name: str):
        self.name: str = name
        self.instructions: List[str] = []

class InitClass(object):
    INSTRUCTION_LIMIT = 1000
    SUBPROC_PREFIX = '__init_'
    def __init__(self):
        self.ninstructions: int = 0
        self.procs: Dict[str, Proc] = {}

    def addInstruction(self, instr: str) -> None:
        proc_id = self.SUBPROC_PREFIX+str(int(math.floor(self.ninstructions/self.INSTRUCTION_LIMIT)))
        proc: Proc = None
        if proc_id not in self.procs:
            proc = self.procs[proc_id] = Proc(proc_id)
        else:
            proc = self.procs[proc_id]
        proc.instructions += [instr]
        self.ninstructions += 1
