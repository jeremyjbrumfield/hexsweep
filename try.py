import pygame
import math
import random
import argparse
import time
import os

# Initial setup
WIDTH, HEIGHT = 1366, 768  # Full screen resolution
FPS = 30
HEX_SIZE = 40
NUM_MINES = 10  # Number of mines

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Load music
pygame.mixer.music.load("background_music.mp3")  # Your background music file
pygame.mixer.music.play(-1)  # Loop the music indefinitely

def load_sounds():
    """Load sound effects for the game, if files exist."""
    sounds = {}
    sound_files = {
        "click": "click.wav",
        "reveal": "reveal.wav",
        "game_over": "game_over.wav"
    }
    for key, file in sound_files.items():
        if os.path.exists(file):
            sounds[key] = pygame.mixer.Sound(file)
        else:
            sounds[key] = None  # No sound for this action
    return sounds

class Hex:
    _directions = [
        (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)
    ]

    def __init__(self, q, r, color=(0, 255, 0), is_mine=False):
        self.q = q  # Axial coordinate q
        self.r = r  # Axial coordinate r
        self.color = color
        self.is_mine = is_mine
        self.revealed = False
        self.adjacent_mines = 0

    def corners(self, center_x, center_y):
        """Calculate corners of the hexagon."""
        return [(center_x + HEX_SIZE * math.cos(math.pi / 3 * i),
                 center_y + HEX_SIZE * math.sin(math.pi / 3 * i)) for i in range(6)]

    def center(self, offset_x, offset_y):
        """Calculate the center of the hexagon based on axial coordinates."""
        x = HEX_SIZE * 1.5 * self.q + offset_x
        y = HEX_SIZE * math.sqrt(3) * (self.r + self.q / 2) + offset_y
        return x, y

def draw_hexagon(screen, hexagon, offset_x, offset_y, debug_mode=False):
    """Draw the hexagon."""
    cx, cy = hexagon.center(offset_x, offset_y)
    corners = hexagon.corners(cx, cy)

    if hexagon.revealed:
        if hexagon.is_mine:
            pygame.draw.polygon(screen, (255, 0, 0), corners)  # Draw mine in red
        else:
            pygame.draw.polygon(screen, (200, 200, 200), corners)  # Draw revealed hexagon in light gray
            if hexagon.adjacent_mines > 0:
                font = pygame.font.SysFont(None, 48)
                text = font.render(str(hexagon.adjacent_mines), True, (0, 0, 0))
                screen.blit(text, (cx - text.get_width() // 2, cy - text.get_height() // 2))
    else:
        pygame.draw.polygon(screen, hexagon.color, corners, 0)  # Default color
        pygame.draw.polygon(screen, (0, 0, 0), corners, 1)  # Border

    # In debug mode, draw mines
    if debug_mode and hexagon.is_mine:
        pygame.draw.circle(screen, (0, 0, 255), (int(cx), int(cy)), HEX_SIZE // 4)  # Draw bomb in blue for debug

def create_hex_grid(rings):
    """Create a filled grid of hexagons."""
    hex_set = []
    for q in range(-rings, rings + 1):
        for r in range(-rings, rings + 1):
            s = -q - r
            if -rings <= s <= rings:  # Valid hexagon position
                hex_set.append(Hex(q, r))
    return hex_set

def place_mines(hex_grid, num_mines):
    """Randomly place a specified number of mines on the hex grid."""
    mines_placed = 0
    while mines_placed < num_mines:
        hexagon = random.choice(hex_grid)
        if not hexagon.is_mine:
            hexagon.is_mine = True
            mines_placed += 1

def calculate_adjacent_mines(hex_grid):
    """Calculate adjacent mines for each hexagon."""
    for hexagon in hex_grid:
        if hexagon.is_mine:
            continue
        adjacent_count = 0
        for direction in Hex._directions:
            neighbor_q = hexagon.q + direction[0]
            neighbor_r = hexagon.r + direction[1]
            neighbor = next((h for h in hex_grid if h.q == neighbor_q and h.r == neighbor_r), None)
            if neighbor and neighbor.is_mine:
                adjacent_count += 1
        hexagon.adjacent_mines = adjacent_count

def reveal_hex(hexagon, hex_grid, sounds):
    """Reveal a hexagon and adjacent hexagons if it has no adjacent mines."""
    if hexagon.revealed:
        return
    hexagon.revealed = True
    if sounds["reveal"]:
        sounds["reveal"].play()  # Play reveal sound if it exists
    if hexagon.adjacent_mines == 0 and not hexagon.is_mine:
        for direction in Hex._directions:
            neighbor_q = hexagon.q + direction[0]
            neighbor_r = hexagon.r + direction[1]
            neighbor = next((h for h in hex_grid if h.q == neighbor_q and h.r == neighbor_r), None)
            if neighbor:
                reveal_hex(neighbor, hex_grid, sounds)

def game_over(screen, sounds):
    """Display Game Over message."""
    font = pygame.font.SysFont(None, 72)
    text = font.render("Game Over", True, (255, 0, 0))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.flip()
    if sounds["game_over"]:
        sounds["game_over"].play()  # Play game over sound if it exists
    time.sleep(2)  # Wait before quitting

def main():
    parser = argparse.ArgumentParser(description="Minesweeper Game")
    parser.add_argument('--debug', action='store_true', help="Show bomb locations for debugging")
    args = parser.parse_args()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    sounds = load_sounds()
    
    start_time = time.time()  # Start the timer
    offset_x, offset_y = WIDTH // 2, HEIGHT // 2
    hex_grid = create_hex_grid(5)  # Five rings of hexagons
    place_mines(hex_grid, NUM_MINES)
    calculate_adjacent_mines(hex_grid)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if event.button == 1:  # Left click
                    for hex in hex_grid:
                        cx, cy = hex.center(offset_x, offset_y)
                        if math.hypot(mouse_x - cx, mouse_y - cy) < HEX_SIZE:
                            if hex.is_mine:
                                game_over(screen, sounds)  # Trigger game over
                                running = False
                            else:
                                reveal_hex(hex, hex_grid, sounds)
                            break

        screen.fill((255, 255, 255))
        
        # Draw all hexagons
        for hexagon in hex_grid:
            draw_hexagon(screen, hexagon, offset_x, offset_y, debug_mode=args.debug)
        
        # Display timer
        elapsed_time = time.time() - start_time
        font = pygame.font.SysFont(None, 48)
        timer_text = font.render(f"Time: {int(elapsed_time)}s", True, (0, 0, 0))
        screen.blit(timer_text, (10, 10))  # Position timer at the top left corner
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.mixer.music.stop()  # Stop music when the game ends
    pygame.quit()

if __name__ == "__main__":
    main()
