import sys
from chip8 import Chip8
import pygame_setup

def main():
    chip8 = Chip8()
    if len(sys.argv) < 2:
        print("Usage: python main.py <rom_path>")
        return
    chip8.load_rom(sys.argv[1])
    beeping = False
    running = True
    beep = pygame_setup.make_beep()

    while running:
        running = pygame_setup.handle_events(chip8)

        for _ in range(pygame_setup.INSTRUCTIONS_PER_FRAME):
            chip8.cycle()

        if hasattr(chip8, 'update_timers'):
            chip8.update_timers()
        else:
            if chip8.delay_timer > 0:
                chip8.delay_timer -= 1
            if chip8.sound_timer > 0:
                chip8.sound_timer -= 1

        if chip8.sound_timer > 0 and not beeping:
            beep.play(-1)
            beeping = True
        elif chip8.sound_timer == 0 and beeping:
            beep.stop()
            beeping = False

        if chip8.draw_flag:
            pygame_setup.draw(chip8)
            chip8.draw_flag = False

        pygame_setup.clock.tick(pygame_setup.FPS)

    pygame_setup.pygame.quit()

if __name__ == "__main__":
    main()