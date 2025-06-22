#!/usr/bin/env python3
"""
Verbose CPU emulator for the Logisim-CTF processor
(fixed 6-bit opcodes + word-indexed RAM).

Usage:
    python cpu_emulator.py flag.bin
"""

import pygame, sys, time, pathlib

# ── helpers ────────────────────────────────────────────────────────────
MASK32 = 0xFFFFFFFF
u32    = lambda v: v & MASK32
s16    = lambda v: (v & 0x7FFF) - (v & 0x8000)
rol32  = lambda v: ((v << 1) | (v >> 31)) & MASK32
ror32  = lambda v: ((v >> 1) | (v << 31)) & MASK32

# real 6-bit opcodes (bits 31-26) --------------------------------------
OP_NOT   = 0x00
OP_XOR   = 0x01
OP_OR    = 0x02
OP_AND   = 0x03
OP_SHL   = 0x04
OP_SHR   = 0x05
OP_ROTL  = 0x06
OP_ROTR  = 0x07
OP_ADD   = 0x08
OP_SUB   = 0x09
OP_INC   = 0x0A
OP_DEC   = 0x0B
OP_MUL   = 0x0C
OP_ORI   = 0x12
OP_ANDI  = 0x13
OP_ADDI  = 0x18
OP_MOV   = 0x20
OP_SW    = 0x25
OP_LW    = 0x27
OP_JMP   = 0x28
OP_JZ    = 0x2A
OP_JNZ   = 0x2B
OP_MOVH  = 0x30
OP_JMPI  = 0x38
OP_JMPIZ = 0x3A
OP_JMPINZ= 0x3B
OP_READ  = 0x3C
OP_DRAW  = 0x3E
OP_CLEAR = 0x3F

# ── CPU class (your original structure kept) ──────────────────────────
class CPUEmulator:
    def __init__(self):
        self.registers = [0]*32
        self.memory    = bytearray(1<<20)      # 1 MiB
        self.running   = False
        self.delay     = False
        self.d_addr    = 0
        self.debug     = True

        # pygame video -------------------------------------------------
        pygame.init()
        self.screen = pygame.display.set_mode((256,256))
        pygame.display.set_caption("CPU Emulator")
        self.clock  = pygame.time.Clock()
        self.draw_calls  = 0
        self.frame_updates = 0
        self.last_flip = time.time()

    # ── ROM loader ----------------------------------------------------
    def load_rom(self, path):
        data = pathlib.Path(path).read_bytes()
        self.memory[:len(data)] = data
        print(f"Loaded {len(data)} bytes from {path}")

    # ── tiny RAM helpers (word-index!) --------------------------------
    def r32w(self, word_addr):
        b = word_addr << 2
        return int.from_bytes(self.memory[b:b+4],"big")
    def w32w(self, word_addr, value):
        b = word_addr << 2
        self.memory[b:b+4] = u32(value).to_bytes(4,"big")

    # ── fetch / decode ------------------------------------------------
    def fetch(self, pc):
        b = self.memory[pc:pc+4]
        return int.from_bytes(b,"big")
    def decode(self, ins):
        return ((ins>>26)&0x3F,            # opcode
                (ins>>21)&0x1F,            # r1
                (ins>>16)&0x1F,            # r2
                (ins>>11)&0x1F,            # r3
                (ins>> 6)&0x1F,            # r4
                 ins      &0xFFFF,         # imm16
                 ins      &0x03FFFFFF)     # imm26

    # ── helpers -------------------------------------------------------
    def wreg(self, r, v):   # r0 hard-wired to 0
        if r: self.registers[r] = u32(v)
    def set_zero(self, v):
        if v==0: self.registers[31] |=1
        else   : self.registers[31] &=~1
    def z(self): return self.registers[31]&1

    # ── execute one instruction --------------------------------------
    def step(self):
        pc  = self.registers[30]
        ins = self.fetch(pc)
        op,r1,r2,r3,r4,imm16,imm26 = self.decode(ins)
        RR = lambda r: 0 if r==0 else self.registers[r]
        s_imm = s16(imm16)

        # --- ALU ------------------------------------------------------
        if   op==OP_NOT : res = ~RR(r2); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_XOR : res = RR(r2)^RR(r3); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_OR  : res = RR(r2)|RR(r3); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_AND : res = RR(r2)&RR(r3); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_SHL : res = (RR(r2)<<1)&MASK32; self.wreg(r1,res); self.set_zero(res)
        elif op==OP_SHR : res = RR(r2)>>1; self.wreg(r1,res); self.set_zero(res)
        elif op==OP_ROTL: res = rol32(RR(r2)); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_ROTR: res = ror32(RR(r2)); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_ADD : res = RR(r2)+RR(r3); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_SUB : res = RR(r2)-RR(r3); self.wreg(r1,res); self.set_zero(res)
        elif op==OP_INC : res = RR(r2)+1; self.wreg(r1,res); self.set_zero(res)
        elif op==OP_DEC : res = RR(r2)-1; self.wreg(r1,res); self.set_zero(res)
        elif op==OP_MUL :
            prod = RR(r3)*RR(r4)
            self.wreg(r1, prod & MASK32)
            self.wreg(r2, prod >> 32)
            self.set_zero(prod & MASK32)
        elif op==OP_ORI : res = RR(r2)|imm16; self.wreg(r1,res); self.set_zero(res)
        elif op==OP_ANDI: res = RR(r2)&imm16; self.wreg(r1,res); self.set_zero(res)
        elif op==OP_ADDI: res = RR(r2)+s_imm; self.wreg(r1,res); self.set_zero(res)

        # --- register / memory ---------------------------------------
        elif op==OP_MOV : self.wreg(r1, RR(r2))
        elif op==OP_SW  : self.w32w(RR(r1), RR(r2))
        elif op==OP_LW  : self.wreg(r1, self.r32w(RR(r2)))

        # --- jumps ----------------------------------------------------
        elif op==OP_JMP : self.delay, self.d_addr = True, RR(r1)
        elif op==OP_JZ  : 
            if self.z(): self.delay, self.d_addr = True, RR(r1)
        elif op==OP_JNZ : 
            if not self.z(): self.delay, self.d_addr = True, RR(r1)

        elif op==OP_MOVH: self.wreg(r1, imm16<<16)
        elif op==OP_JMPI : self.delay, self.d_addr = True, imm26<<2
        elif op==OP_JMPIZ: 
            if self.z(): self.delay, self.d_addr = True, imm26<<2
        elif op==OP_JMPINZ:
            if not self.z(): self.delay, self.d_addr = True, imm26<<2

        # --- I/O & video ---------------------------------------------
        elif op==OP_READ: self.wreg(r1,0)   # stub
        elif op==OP_DRAW:
            x =  RR(r1)      &0xFF
            y = (RR(r1)>>8) &0xFF
            col = RR(r2)&0xFFFFFF
            self.screen.set_at((x,y),
                               ((col>>16)&0xFF,(col>>8)&0xFF,col&0xFF))
            self.draw_calls += 1
            if self.draw_calls % 256 == 0:
                pygame.display.flip(); self.frame_updates += 1
        elif op==OP_CLEAR:
            self.screen.fill((0,0,0)); pygame.display.flip(); self.frame_updates+=1
        else:
            raise RuntimeError(f"unknown opcode {op:02X} @ {pc:08X}")

        # delayed slot PC update
        if self.delay:
            self.registers[30] = self.d_addr
            self.delay=False
        else:
            self.registers[30] = (pc+4) & MASK32

    # ── outer loop (with your logging) --------------------------------
    def run(self):
        self.running=True
        instr=0; start=time.time(); last=time.time()
        while self.running:
            for event in pygame.event.get():
                if event.type==pygame.QUIT: self.running=False
            self.step(); instr+=1

            # 24 fps window refresh
            now=time.time()
            if now-self.last_flip>=1/24:
                pygame.display.flip(); self.last_flip=now

            # debug line every second
            if now-last>=1.0:
                ips = instr/(now-start)
                pc  = self.registers[30]
                print(f"PC:{pc:08x} IPS:{ips:,.0f} "
                      f"Draw:{self.draw_calls} Frames:{self.frame_updates}")
                last=now

# ── main ───────────────────────────────────────────────────────────────
if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage: python cpu_emulator.py flag.bin"); sys.exit(1)
    cpu = CPUEmulator(); cpu.load_rom(sys.argv[1]); cpu.run()
