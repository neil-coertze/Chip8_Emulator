import random

class Chip8:
    def __init__(self):
        self.memory = bytearray(4096)  # 4KB of memory
        self.v = bytearray(16)        # 16 8-bit registers (V0 to VF)
        self.I = 0                    # 16-bit index register
        self.PC = 0x200               # Program counter starts at 0x200
        self.stack = []               # Stack for storing return addresses
        self.delay_timer = 0          # Delay timer
        self.sound_timer = 0          # Sound timer
        self.display = [False] * 64 * 32  # 64x32 display
        self.keys = [False] * 16      # 16-key keypad state
        self.draw_flag = False        # Flag to indicate when the display needs to be redrawn
        self.FONT = [                 # Font set for hexadecimal characters 0-F
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
        ]
        self.FONT_START = 0x50         # Starting address in memory for the font set
        self.load_font()

    def load_font(self):
        for i, byte in enumerate(self.FONT):
            self.memory[self.FONT_START + i] = byte

    def load_rom(self, rom_path):
        with open(rom_path, 'rb') as f:
            rom_data = f.read()
            for i, byte in enumerate(rom_data):
                self.memory[0x200 + i] = byte

    def fetch(self):
        opcode = (self.memory[self.PC] << 8) | self.memory[self.PC + 1]
        self.PC += 2
        return opcode

    # Set Vx to nn
    def op_6xnn(self, x, nn):
        self.v[x] = nn

    # Add Vx and Vy, store result in Vx, set VF to 1 if there's a carry, else 0
    def op_8xy4(self, x, y):
        sum = self.v[x] + self.v[y]
        if sum > 0xFF:
            self.v[0xF] = 1  # Set carry flag
        else:
            self.v[0xF] = 0  # Clear carry flag
        self.v[x] = sum & 0xFF  # Store the result in Vx

    # Clear the display
    def op_00E0(self):
        self.display = [False] * 64 * 32
        self.draw_flag = True

    # Return from subroutine
    def op_00EE(self):
        self.PC = self.stack.pop()

    # Jump to address nnn
    def op_1nnn(self, nnn):
        self.PC = nnn

    # Jump to subroutine at nnn
    def op_2nnn(self, nnn):
        self.stack.append(self.PC)
        self.PC = nnn

    # Skip the next instruction if Vx equals nn
    def op_3xnn(self, x, nn):
        if self.v[x] == nn:
            self.PC += 2

    # Skip the next instruction if Vx does not equal nn
    def op_4xnn(self, x, nn):
        if self.v[x] != nn:
            self.PC += 2 

    # Skip the next instruction if Vx equals Vy
    def op_5xy0(self, x, y):
        if self.v[x] == self.v[y]:
            self.PC += 2

    # Set Vx to Vx + nn (without affecting the carry flag)
    def op_7xnn(self, x, nn):
        self.v[x] = (self.v[x] + nn) & 0xFF  # Ensure it wraps around at 255

    # Set Vx to Vy
    def op_8xy0(self, x, y):
        self.v[x] = self.v[y]

    # Set Vx = Vx OR Vy
    def op_8xy1(self, x, y):
        self.v[x] = self.v[x] | self.v[y]
        self.v[0xF] = 0

    # Set Vx = Vx AND Vy
    def op_8xy2(self, x, y):
        self.v[x] = self.v[x] & self.v[y]
        self.v[0xF] = 0

    # Set Vx = Vx XOR Vy
    def op_8xy3(self, x, y):
        self.v[x] = self.v[x] ^ self.v[y]
        self.v[0xF] = 0

    # Subtract Vy from Vx, set VF to NOT borrow
    def op_8xy5(self, x, y):
        if self.v[x] >= self.v[y]:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.v[x] = (self.v[x] - self.v[y]) & 0xFF

    # Shift Vx right by 1, VF = LSB of Vx before shift
    def op_8xy6(self, x, y=None):
        self.v[0xF] = self.v[x] & 0x1
        self.v[x] = self.v[x] >> 1

    # Set Vx = Vy - Vx, set VF to NOT borrow
    def op_8xy7(self, x, y):
        if self.v[y] >= self.v[x]:
            self.v[0xF] = 1
        else:
            self.v[0xF] = 0
        self.v[x] = (self.v[y] - self.v[x]) & 0xFF

    # Shift Vx left by 1, VF = MSB of Vx before shift
    def op_8xyE(self, x, y=None):
        self.v[0xF] = (self.v[x] >> 7) & 0x1
        self.v[x] = (self.v[x] << 1) & 0xFF

    # Skip next instruction if Vx != Vy
    def op_9xy0(self, x, y):
        if self.v[x] != self.v[y]:
            self.PC += 2

    # Set I = nnn
    def op_Annn(self, nnn):
        self.I = nnn

    # Jump to location nnn + V0
    def op_Bnnn(self, nnn):
        self.PC = nnn + self.v[0]

    # Set Vx = random byte AND nn
    def op_Cxnn(self, x, nn):
        self.v[x] = random.randint(0, 255) & nn

    # Display sprite starting at memory location I at (Vx, Vy), set VF = collision
    def op_Dxyn(self, x, y, n):
        self.v[0xF] = 0
        for row in range(n):
            sprite_byte = self.memory[self.I + row]
            for col in range(8):
                if sprite_byte & (0x80 >> col):
                    px = (self.v[x] + col) % 64
                    py = (self.v[y] + row) % 32
                    idx = py * 64 + px
                    if self.display[idx]:
                        self.v[0xF] = 1
                    self.display[idx] = not self.display[idx]
        self.draw_flag = True

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

    # Skip if key with value of Vx is pressed
    def op_Ex9E(self, x):
        if self.keys[self.v[x] & 0xF]:
            self.PC += 2

    # Skip if key with value of Vx is not pressed
    def op_ExA1(self, x):
        if not self.keys[self.v[x] & 0xF]:
            self.PC += 2

    # Set Vx = delay timer value
    def op_Fx07(self, x):
        self.v[x] = self.delay_timer

    # Wait for a key press, store the value of the key in Vx
    def op_Fx0A(self, x):
        pressed = -1
        for i in range(16):
            if self.keys[i]:
                pressed = i
                break
        if pressed == -1:
            self.PC -= 2
        else:
            self.v[x] = pressed

    # Set delay timer = Vx
    def op_Fx15(self, x):
        self.delay_timer = self.v[x]

    # Set sound timer = Vx
    def op_Fx18(self, x):
        self.sound_timer = self.v[x]

    # Set I = I + Vx
    def op_Fx1E(self, x):
        self.I = (self.I + self.v[x]) & 0xFFFF

    # Set I = location of sprite for digit Vx
    def op_Fx29(self, x):
        self.I = self.FONT_START + (self.v[x] & 0xF) * 5

    # Store BCD representation of Vx in memory locations I, I+1, and I+2
    def op_Fx33(self, x):
        vx = self.v[x]
        self.memory[self.I] = vx // 100
        self.memory[self.I + 1] = (vx // 10) % 10
        self.memory[self.I + 2] = vx % 10

    # Store registers V0 through Vx in memory starting at location I
    def op_Fx55(self, x):
        for i in range(x + 1):
            self.memory[self.I + i] = self.v[i]
        # Some implementations increment I, original doesn't - follow standard

    # Read registers V0 through Vx from memory starting at location I
    def op_Fx65(self, x):
        for i in range(x + 1):
            self.v[i] = self.memory[self.I + i]

    def cycle(self):
        opcode = self.fetch()

        op = (opcode & 0xF000) >> 12  # Get the first nibble of the opcode
        x = (opcode & 0x0F00) >> 8    # Get the second nibble of the opcode
        y = (opcode & 0x00F0) >> 4    # Get the third nibble of the opcode
        n = opcode & 0x000F           # Get the fourth nibble of the opcode
        nn = opcode & 0x00FF          # Get the last two nibbles of the opcode
        nnn = opcode & 0x0FFF         # Get the last three nibbles of the opcode

        match op:
            case 0x0:
                match opcode:
                    case 0x00E0:
                        self.op_00E0()
                    case 0x00EE:
                        self.op_00EE()
                    case _:
                        pass
            case 0x1:
                self.op_1nnn(nnn)
            case 0x2:
                self.op_2nnn(nnn)
            case 0x3:
                self.op_3xnn(x, nn)
            case 0x4:
                self.op_4xnn(x, nn)
            case 0x5 if n == 0x0:
                self.op_5xy0(x, y)
            case 0x6:
                self.op_6xnn(x, nn)
            case 0x7:
                self.op_7xnn(x, nn)
            case 0x8:
                match n:
                    case 0x0:
                        self.op_8xy0(x, y)
                    case 0x1:
                        self.op_8xy1(x, y)
                    case 0x2:
                        self.op_8xy2(x, y)
                    case 0x3:
                        self.op_8xy3(x, y)
                    case 0x4:
                        self.op_8xy4(x, y)
                    case 0x5:
                        self.op_8xy5(x, y)
                    case 0x6:
                        self.op_8xy6(x)
                    case 0x7:
                        self.op_8xy7(x, y)
                    case 0xE:
                        self.op_8xyE(x)
            case 0x9 if n == 0x0:
                self.op_9xy0(x, y)
            case 0xA:
                self.op_Annn(nnn)
            case 0xB:
                self.op_Bnnn(nnn)
            case 0xC:
                self.op_Cxnn(x, nn)
            case 0xD:
                self.op_Dxyn(x, y, n)
            case 0xE:
                match nn:
                    case 0x9E:
                        self.op_Ex9E(x)
                    case 0xA1:
                        self.op_ExA1(x)
            case 0xF:
                match nn:
                    case 0x07:
                        self.op_Fx07(x)
                    case 0x0A:
                        self.op_Fx0A(x)
                    case 0x15:
                        self.op_Fx15(x)
                    case 0x18:
                        self.op_Fx18(x)
                    case 0x1E:
                        self.op_Fx1E(x)
                    case 0x29:
                        self.op_Fx29(x)
                    case 0x33:
                        self.op_Fx33(x)
                    case 0x55:
                        self.op_Fx55(x)
                    case 0x65:
                        self.op_Fx65(x)
            case _:
                print(f"Unknown opcode: {opcode:04X}")

    # Draws a sprite at coordinate (Vx, Vy) that has a width of 8 pixels and a height of N pixels.
    def op_DXYN(self, x, y, n):
        self.v[0xF] = 0
        for row in range(n):
            sprite_byte = self.memory[self.I + row]
            for col in range(8):
                if sprite_byte & (0x80 >> col):
                    px = (self.v[x] + col) % 64
                    py = (self.v[y] + row) % 32
                    if self.display[py][px]:
                        self.v[0xF] = 1
                    self.display[py][px] ^= True
        self.draw_flag = True

    # Update the delay and sound timers
    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1


    