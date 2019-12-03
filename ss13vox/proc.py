# Logical representation of an init proc, so we can break it up.
import math
from typing import List, Dict
class Proc(object):
    BASE_COST = 5
    def __init__(self, name: str):
        self.name: str = name
        self.lines: List[str] = []
        self.instructions = self.BASE_COST

class InitClass(object):
    INSTRUCTION_LIMIT = 65535
    SUBPROC_PREFIX = '__init_'
    def __init__(self):
        self.instructions: int = 0
        self.nprocs: int = 1
        self.proc: Proc = None
        self.procs: Dict[str, Proc] = {}

    def addProc(self) -> None:
        #Proc(self.SUBPROC_PREFIX+str(int(math.floor(self.ninstructions/self.INSTRUCTION_LIMIT))))
        self.proc = Proc(self.SUBPROC_PREFIX+str(self.nprocs))
        self.procs[self.proc.name] = self.proc
        self.nprocs += 1

    def addInstruction(self, instr: str, cost: int) -> None:
        if self.proc is None or self.proc.instructions + cost > self.INSTRUCTION_LIMIT:
            self.addProc()
        proc = self.proc
        proc.lines += [instr]
        self.instructions += cost
        proc.instructions += cost
