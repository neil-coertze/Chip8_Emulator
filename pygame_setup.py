import pygame
from array import array

SCALE = 10                       # each CHIP-8 pixel = 10x10 screen pixels
WIDTH, HEIGHT = 64, 32           # CHIP-8 display resolution
FPS = 60                         # target frames per second
INSTRUCTIONS_PER_FRAME = 10      # ~600 instr/sec; tweak per game

ON_COLOR  = (255, 255, 255)      # color for "on" pixels (white)
OFF_COLOR = (0, 0, 0)            # color for "off" pixels (black)

pygame.init()
screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
pygame.display.set_caption("CHIP-8")
clock = pygame.time.Clock()

KEYMAP = {
    pygame.K_KP0: 0x0, pygame.K_KP1: 0x1, pygame.K_KP2: 0x2, pygame.K_KP3: 0x3,
    pygame.K_KP4: 0x4, pygame.K_KP5: 0x5, pygame.K_KP6: 0x6, pygame.K_KP7: 0x7,
    pygame.K_KP8: 0x8, pygame.K_KP9: 0x9,
    pygame.K_4: 0xC, pygame.K_r: 0xD, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_c: 0xB, pygame.K_v: 0xF,
    pygame.K_a: 0x7, pygame.K_d: 0x8, pygame.K_w: 0x9, pygame.K_s: 0x2,
}

# Handle Pygame events (keyboard input, window close, etc.)
def handle_events(chip8):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in KEYMAP:
                chip8.keys[KEYMAP[event.key]] = True
        if event.type == pygame.KEYUP:
            if event.key in KEYMAP:
                chip8.keys[KEYMAP[event.key]] = False
    return True

# Draw the CHIP-8 display to the Pygame window
def draw(chip8):
    screen.fill(OFF_COLOR)
    display = getattr(chip8, 'display', [])
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = y * WIDTH + x
            if isinstance(display, list) and len(display) == HEIGHT and isinstance(display[0], list):
                pixel = display[y][x]
            elif isinstance(display, list) and len(display) == HEIGHT * WIDTH:
                pixel = display[idx]
            elif hasattr(display, '__getitem__'):
                try:
                    if len(display) == HEIGHT * WIDTH:
                        pixel = display[idx]
                    else:
                        pixel = display[y][x]
                except Exception:
                    pixel = False
            else:
                pixel = False
            if pixel:
                pygame.draw.rect(screen, ON_COLOR,
                                 (x * SCALE, y * SCALE, SCALE, SCALE))
    # push the frame to the window
    pygame.display.flip()        

pygame.mixer.init(frequency=44100, size=-16, channels=1)

# Generate a square-wave beep sound for the CHIP-8 sound timer
def make_beep(freq=440, volume=3000, sample_rate=44100):
    period = sample_rate // freq
    samples = array("h", [volume if (i % period) < period // 2 else -volume
                          for i in range(period)])   # one square-wave cycle
    return pygame.mixer.Sound(buffer=samples)



    