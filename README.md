<h1 align="center">
  <img src="https://i.ibb.co/Y7KXmM1f/Chat-GPT-Image-22-6-2025-18-43-12.png" alt="Chat-GPT-Image-22-6-2025-18-43-12" border="0" width="600px">
  <br>
</h1>

<h4 align="center">Python script for emulating cpu based on given instructions (from cybersec. competition)</h4>

<p align="center">
<a href=""><img src="https://img.shields.io/badge/Python-blue"></a>
<a href=""><img src="https://img.shields.io/badge/Emulation-purple"></a>
<a href=""><img src="https://img.shields.io/badge/Logical Circuits-yellow"></a>
</p>

<br>

<p align="center">
<a href=""><img src="https://img.shields.io/github/release/LOKAI77/Good-Apple-CPU"></a>
</p>

# ABOUT

This script is based on specificaly designed instructions from a cybersecurity competition. The final script should be able to run a .bin file which has a video with the flag inside.

# WRITEUP

<h3 align="left">Emulating a CPU</h1>

**<p>What we know:</p>**

In this challenge we are supposed to emulate a CPU based on a set of instructions we are given to replay a video saved in `flag.bin`

We are given a compressed `tar.gz` archive with all the data we might need for the CPU emulation:
- `flag.bin`
- `instructions.csv`
- `cpu.circ`
- `header.asm`

Sample files:
- `main.bin`
- `main.txt`
- `main.asm`

**<p>Summary</p>**
- **Loads** a binary program into its memory.
- **Repeats**: fetch one instruction, figure out what it means, do it.
- **Updates** its own “screen” pixel by pixel.
- **Keeps track** of how fast it’s running and shows it on screen.

**<p>Preparation</p>**
- **Registers & Memory**
  - 32 numbers (“registers”) to hold calculations.
  - 1 MiB of memory to store the program and data.
- **Graphics Setup**
  - Opens a 256×256 pixel window.
  - Will paint pixels here when the program asks.

**<p>Loading</p>**
- Reads the entire input file (e.g. `flag.bin`) into the start of memory.
- Sets the program counter (PC) to 0 so it begins at the top.

**<p>Instruction Cycle</p>**
Every loop it does:
1) **Fetch** the 4-byte instruction at the PC.
2) **Decode** it into:
   - An opcode (which operation to do),
   - Up to four register numbers,
   - A small number built into the instruction.
3) **Execute** based on the opcode:
   - **Math & Logic** (add, subtract, AND, OR, shifts, rotates, multiply).
   - **Load/Store** (move data between registers and memory).
   - **Branches** (jump to a new instruction, with a one-instruction “delay slot”).
   - **Special** (load high bits of a register).
   - **Graphics I/O**:
   - **DRAW**: paint one pixel at (x,y) in a given color.
   - **CLEAR**: wipe the screen black.
   - **READ**: placeholder that just sets a register to zero.
4) **Update PC**:
   - If it did a jump, it takes the branch after one more instruction.
   - Otherwise it moves to the next instruction (PC + 4).

**<p>Keeping Track & Display</p>**
- Counts how many instructions it has run.
- Every 1 second, prints:
  - Current PC address,
  - Instructions per second (IPS),
  - How many pixels drawn and how many times the window updated.
- Keeps the window refreshing at up to 24 frames per second so your drawing appears smoothly.

**<p>Running</p>**
- Checks for a window-close event so you can quit.
- Continuously steps through instructions until you close the window or an error happens.
