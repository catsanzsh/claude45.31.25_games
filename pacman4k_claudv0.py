# --------------------------------------------
# Enhanced Pac-Man Arcade Game - test.py
# Faithful recreation with programmatic audio
# --------------------------------------------
import pygame
import random
import math
import numpy as np

# Initialize Pygame and audio
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Game Constants
TILE_SIZE = 20
MAZE_COLS = 28
MAZE_ROWS = 31
SCREEN_WIDTH = TILE_SIZE * MAZE_COLS
SCREEN_HEIGHT = TILE_SIZE * MAZE_ROWS + 100
FPS = 60

# Colors (matching original arcade)
BLACK = (0, 0, 0)
BLUE = (33, 33, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
WHITE = (255, 255, 255)
BLUE_GHOST = (33, 33, 222)
WALL_BLUE = (0, 0, 255)

# Game Settings
START_LIVES = 3
DOT_SCORE = 10
POWER_DOT_SCORE = 50
GHOST_EAT_SCORES = [200, 400, 800, 1600]
FRUIT_VALUES = [100, 300, 500, 700, 1000, 2000, 3000, 5000]
POWER_PELLET_TIME = 6 * FPS  # 6 seconds
READY_TIME = 2 * FPS  # 2 seconds ready screen

# Maze layout
maze_layout = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "######.##### ## #####.######",
    "######.##          ##.######",
    "######.## ###--### ##.######",
    "######.## #      # ##.######",
    "       ## #      # ##       ",
    "######.## #      # ##.######",
    "######.## ######## ##.######",
    "######.##          ##.######",
    "######.## ######## ##.######",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##................##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################"
]

# Audio Generation Functions
def generate_tone(frequency, duration, sample_rate=22050, amplitude=0.1):
    """Generate a pure tone"""
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2))
    arr[:, 0] = amplitude * np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
    arr[:, 1] = arr[:, 0]
    arr = (arr * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(arr)
    return sound

def generate_waka_sound():
    """Generate the classic Pac-Man waka sound"""
    sample_rate = 22050
    duration = 0.1
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2))
    
    # Create a frequency sweep from 400 to 200 Hz
    freqs = np.linspace(400, 200, frames)
    for i in range(frames):
        arr[i, 0] = 0.1 * np.sin(2 * np.pi * freqs[i] * i / sample_rate)
    arr[:, 1] = arr[:, 0]
    arr = (arr * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(arr)

def generate_chomp_sound():
    """Generate pellet eating sound"""
    return generate_tone(800, 0.05, amplitude=0.08)

def generate_power_pellet_sound():
    """Generate power pellet sound"""
    sample_rate = 22050
    duration = 0.3
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2))
    
    # Create ascending tone sequence
    for i in range(frames):
        freq = 400 + (i / frames) * 400
        arr[i, 0] = 0.1 * np.sin(2 * np.pi * freq * i / sample_rate)
    arr[:, 1] = arr[:, 0]
    arr = (arr * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(arr)

def generate_ghost_eaten_sound():
    """Generate ghost eaten sound"""
    return generate_tone(1000, 0.2, amplitude=0.1)

def generate_death_sound():
    """Generate Pac-Man death sound"""
    sample_rate = 22050
    duration = 1.0
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2))
    
    # Descending frequency sweep
    freqs = np.linspace(500, 50, frames)
    for i in range(frames):
        amplitude = 0.1 * (1 - i / frames)  # Fade out
        arr[i, 0] = amplitude * np.sin(2 * np.pi * freqs[i] * i / sample_rate)
    arr[:, 1] = arr[:, 0]
    arr = (arr * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(arr)

# Initialize sounds
sounds = {
    'chomp': generate_chomp_sound(),
    'power_pellet': generate_power_pellet_sound(),
    'ghost_eaten': generate_ghost_eaten_sound(),
    'death': generate_death_sound(),
    'waka': generate_waka_sound()
}

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PAC-MAN")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.state = "READY"  # "READY", "PLAYING", "DYING", "GAME_OVER"
        self.state_timer = READY_TIME
        self.score = 0
        self.high_score = 0
        self.lives = START_LIVES
        self.level = 1
        self.pellets_eaten = 0
        self.total_pellets = self.count_pellets()
        self.ghost_eat_count = 0
        self.power_mode = False
        self.power_timer = 0
        
        # Animation
        self.power_pellet_blink = 0
        self.waka_timer = 0
        
        # Initialize maze
        self.maze = [list(row) for row in maze_layout]
        self.original_maze = [list(row) for row in maze_layout]
        
        # Initialize entities
        self.reset_level()
    
    def count_pellets(self):
        count = 0
        for row in maze_layout:
            count += row.count('.') + row.count('o')
        return count
    
    def reset_level(self):
        # Reset maze
        self.maze = [list(row) for row in self.original_maze]
        
        # Initialize Pac-Man
        self.pacman = Pacman((13, 23))
        # Remove pellet at start position
        if self.maze[23][13] in '.o':
            self.maze[23][13] = ' '
        
        # Initialize ghosts
        self.blinky = Ghost("blinky", (13, 11), RED, (25, 0))
        self.pinky = Ghost("pinky", (13, 14), PINK, (2, 0))
        self.inky = Ghost("inky", (11, 14), CYAN, (27, 29))
        self.clyde = Ghost("clyde", (15, 14), ORANGE, (0, 29))
        
        self.ghosts = [self.blinky, self.pinky, self.inky, self.clyde]
        
        # Reset counters
        self.pellets_eaten = 0
        self.ghost_eat_count = 0
        self.power_mode = False
        self.power_timer = 0
        
        # Ghost release timing
        self.ghost_release_timer = 0
        self.ghosts_released = set()
        
    def reset_positions(self):
        """Reset positions after death"""
        self.pacman.reset()
        for ghost in self.ghosts:
            ghost.reset()
        self.ghost_release_timer = 0
        self.ghosts_released = set()
        self.power_mode = False
        self.power_timer = 0
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        if self.state == "PLAYING":
            if keys[pygame.K_UP]:
                self.pacman.set_direction(0, -1)
            elif keys[pygame.K_DOWN]:
                self.pacman.set_direction(0, 1)
            elif keys[pygame.K_LEFT]:
                self.pacman.set_direction(-1, 0)
            elif keys[pygame.K_RIGHT]:
                self.pacman.set_direction(1, 0)
    
    def update(self):
        if self.state == "READY":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.state = "PLAYING"
        
        elif self.state == "PLAYING":
            self.update_game()
        
        elif self.state == "DYING":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = "GAME_OVER"
                    if self.score > self.high_score:
                        self.high_score = self.score
                else:
                    self.reset_positions()
                    self.state = "READY"
                    self.state_timer = READY_TIME
    
    def update_game(self):
        # Update animations
        self.power_pellet_blink = (self.power_pellet_blink + 1) % 20
        self.waka_timer = (self.waka_timer + 1) % 10
        
        # Update Pac-Man
        self.pacman.update(self.maze)
        
        # Check pellet eating
        col, row = self.pacman.get_tile()
        if self.maze[row][col] == '.':
            self.maze[row][col] = ' '
            self.score += DOT_SCORE
            self.pellets_eaten += 1
            sounds['chomp'].play()
            
        elif self.maze[row][col] == 'o':
            self.maze[row][col] = ' '
            self.score += POWER_DOT_SCORE
            self.pellets_eaten += 1
            self.power_mode = True
            self.power_timer = POWER_PELLET_TIME
            self.ghost_eat_count = 0
            sounds['power_pellet'].play()
            
            # Frighten all active ghosts
            for ghost in self.ghosts:
                if ghost.mode != "dead" and ghost.mode != "entering":
                    ghost.frighten()
        
        # Update power mode
        if self.power_mode:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.power_mode = False
                for ghost in self.ghosts:
                    if ghost.frightened:
                        ghost.unfrighten()
        
        # Release ghosts from pen
        self.ghost_release_timer += 1
        if "pinky" not in self.ghosts_released and (self.pellets_eaten >= 7 or self.ghost_release_timer > 4 * FPS):
            self.pinky.release()
            self.ghosts_released.add("pinky")
        if "inky" not in self.ghosts_released and (self.pellets_eaten >= 17 or self.ghost_release_timer > 8 * FPS):
            self.inky.release()
            self.ghosts_released.add("inky")
        if "clyde" not in self.ghosts_released and (self.pellets_eaten >= 32 or self.ghost_release_timer > 12 * FPS):
            self.clyde.release()
            self.ghosts_released.add("clyde")
        
        # Update ghosts
        for ghost in self.ghosts:
            ghost.update(self.pacman, self.blinky)
        
        # Check collisions
        pac_rect = pygame.Rect(self.pacman.x - 8, self.pacman.y - 8, 16, 16)
        for ghost in self.ghosts:
            if ghost.mode == "dead":
                continue
            ghost_rect = pygame.Rect(ghost.x - 8, ghost.y - 8, 16, 16)
            if pac_rect.colliderect(ghost_rect):
                if ghost.frightened:
                    # Eat ghost
                    ghost.die()
                    score_gain = GHOST_EAT_SCORES[min(self.ghost_eat_count, 3)]
                    self.score += score_gain
                    self.ghost_eat_count += 1
                    sounds['ghost_eaten'].play()
                else:
                    # Pac-Man dies
                    self.state = "DYING"
                    self.state_timer = FPS * 2
                    sounds['death'].play()
                    return
        
        # Check level completion
        if self.pellets_eaten >= self.total_pellets:
            self.level += 1
            self.reset_level()
            self.state = "READY"
            self.state_timer = READY_TIME
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw maze
        for row in range(MAZE_ROWS):
            for col in range(MAZE_COLS):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                cell = self.maze[row][col]
                
                if cell == '#':
                    pygame.draw.rect(self.screen, WALL_BLUE, (x, y, TILE_SIZE, TILE_SIZE))
                elif cell == '.':
                    pygame.draw.circle(self.screen, YELLOW, 
                                     (x + TILE_SIZE//2, y + TILE_SIZE//2), 2)
                elif cell == 'o':
                    if self.power_pellet_blink < 10:  # Blinking effect
                        pygame.draw.circle(self.screen, YELLOW, 
                                         (x + TILE_SIZE//2, y + TILE_SIZE//2), 6)
        
        # Draw entities
        if self.state != "DYING":
            self.pacman.draw(self.screen)
        
        for ghost in self.ghosts:
            ghost.draw(self.screen)
        
        # Draw UI
        score_text = self.font.render(f"SCORE: {self.score:06d}", True, YELLOW)
        self.screen.blit(score_text, (10, SCREEN_HEIGHT - 90))
        
        high_score_text = self.font.render(f"HIGH SCORE: {self.high_score:06d}", True, YELLOW)
        self.screen.blit(high_score_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 90))
        
        level_text = self.small_font.render(f"LEVEL {self.level}", True, WHITE)
        self.screen.blit(level_text, (10, SCREEN_HEIGHT - 60))
        
        # Draw lives
        for i in range(self.lives - 1):
            x = 10 + i * 25
            y = SCREEN_HEIGHT - 35
            pygame.draw.circle(self.screen, YELLOW, (x, y), 8)
        
        # Draw state messages
        if self.state == "READY":
            ready_text = self.font.render("READY!", True, YELLOW)
            text_rect = ready_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(ready_text, text_rect)
        
        elif self.state == "GAME_OVER":
            game_over_text = self.font.render("GAME OVER", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(game_over_text, text_rect)
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.state == "GAME_OVER":
                        # Restart game
                        self.score = 0
                        self.lives = START_LIVES
                        self.level = 1
                        self.reset_level()
                        self.state = "READY"
                        self.state_timer = READY_TIME
            
            self.handle_input()
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

class Pacman:
    def __init__(self, start_tile):
        self.start_tile = start_tile
        self.reset()
        self.mouth_angle = 0
        self.mouth_opening = 0
    
    def reset(self):
        self.x = self.start_tile[0] * TILE_SIZE + TILE_SIZE//2
        self.y = self.start_tile[1] * TILE_SIZE + TILE_SIZE//2
        self.dir = (0, 0)
        self.next_dir = (0, 0)
        self.speed = 1.5
    
    def set_direction(self, dx, dy):
        self.next_dir = (dx, dy)
    
    def get_tile(self):
        return (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
    
    def update(self, maze):
        col, row = self.get_tile()
        
        # Try to turn if centered on tile
        if abs(self.x - (col * TILE_SIZE + TILE_SIZE//2)) < 2 and \
           abs(self.y - (row * TILE_SIZE + TILE_SIZE//2)) < 2:
            if self.next_dir != (0, 0):
                next_col = col + self.next_dir[0]
                next_row = row + self.next_dir[1]
                if 0 <= next_col < MAZE_COLS and 0 <= next_row < MAZE_ROWS:
                    if maze[next_row][next_col] not in ['#', '-']:
                        self.dir = self.next_dir
                        self.next_dir = (0, 0)
        
        # Move in current direction
        if self.dir != (0, 0):
            next_x = self.x + self.dir[0] * self.speed
            next_y = self.y + self.dir[1] * self.speed
            
            # Check for walls
            next_col = int(next_x // TILE_SIZE)
            next_row = int(next_y // TILE_SIZE)
            
            if 0 <= next_col < MAZE_COLS and 0 <= next_row < MAZE_ROWS:
                if maze[next_row][next_col] not in ['#', '-']:
                    self.x = next_x
                    self.y = next_y
                else:
                    self.dir = (0, 0)
            
            # Tunnel wrapping
            if next_row == 14:  # Tunnel row
                if next_x < 0:
                    self.x = SCREEN_WIDTH - TILE_SIZE//2
                elif next_x >= SCREEN_WIDTH:
                    self.x = TILE_SIZE//2
        
        # Update mouth animation
        if self.dir != (0, 0):
            self.mouth_opening = (self.mouth_opening + 0.3) % (2 * math.pi)
        else:
            self.mouth_opening = 0
    
    def draw(self, screen):
        # Draw Pac-Man with animated mouth
        center = (int(self.x), int(self.y))
        radius = 8
        
        # Determine mouth direction
        if self.dir == (1, 0):    # Right
            start_angle = 0.5
        elif self.dir == (-1, 0): # Left
            start_angle = 3.5
        elif self.dir == (0, -1): # Up
            start_angle = 2
        elif self.dir == (0, 1):  # Down
            start_angle = 5
        else:
            start_angle = 0.5
        
        mouth_size = abs(math.sin(self.mouth_opening)) * 0.8
        
        if mouth_size > 0.1:
            # Draw Pac-Man with mouth open
            angles = []
            for i in range(32):
                angle = i * 2 * math.pi / 32
                if not (start_angle - mouth_size < angle < start_angle + mouth_size):
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                    angles.append((x, y))
            
            if len(angles) > 2:
                angles.append(center)
                pygame.draw.polygon(screen, YELLOW, angles)
        else:
            # Draw full circle
            pygame.draw.circle(screen, YELLOW, center, radius)

class Ghost:
    def __init__(self, name, start_tile, color, scatter_target):
        self.name = name
        self.color = color
        self.original_color = color
        self.scatter_target = scatter_target
        self.start_tile = start_tile
        self.reset()
    
    def reset(self):
        self.x = self.start_tile[0] * TILE_SIZE + TILE_SIZE//2
        self.y = self.start_tile[1] * TILE_SIZE + TILE_SIZE//2
        self.dir = (0, -1) if self.name == "blinky" else (0, 1)
        self.speed = 1.2
        self.mode = "scatter" if self.name == "blinky" else "pen"
        self.frightened = False
        self.frightened_timer = 0
        self.target = self.scatter_target
        self.pen_timer = 0
    
    def release(self):
        if self.mode == "pen":
            self.mode = "leaving"
            self.dir = (0, -1)
    
    def frighten(self):
        if self.mode not in ["dead", "entering", "pen", "leaving"]:
            self.frightened = True
            self.frightened_timer = POWER_PELLET_TIME
            self.dir = (-self.dir[0], -self.dir[1])  # Reverse direction
            self.speed = 0.8
    
    def unfrighten(self):
        self.frightened = False
        self.speed = 1.2
    
    def die(self):
        self.mode = "dead"
        self.frightened = False
        self.speed = 2.0
        self.target = (13, 11)  # Ghost house entrance
    
    def get_tile(self):
        return (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
    
    def update(self, pacman, blinky):
        col, row = self.get_tile()
        
        # Update frightened timer
        if self.frightened:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.unfrighten()
        
        # State machine
        if self.mode == "pen":
            # Bounce in pen
            self.pen_timer += 1
            if self.pen_timer % 60 == 0:  # Change direction every second
                self.dir = (0, -self.dir[1])
            self.move_in_direction()
        
        elif self.mode == "leaving":
            # Move to exit
            if row > 11:
                self.dir = (0, -1)
                self.move_in_direction()
            else:
                self.mode = "scatter"
                self.dir = (-1, 0)
        
        elif self.mode == "dead":
            # Return to ghost house
            if col == 13 and row == 11:
                self.mode = "entering"
                self.dir = (0, 1)
            else:
                self.seek_target()
        
        elif self.mode == "entering":
            # Enter ghost house
            if row >= 14:
                self.mode = "leaving"
                self.reset()
            else:
                self.dir = (0, 1)
                self.move_in_direction()
        
        else:
            # Normal AI (scatter/chase)
            if self.frightened:
                self.move_randomly()
            else:
                self.update_target(pacman, blinky)
                self.seek_target()
    
    def update_target(self, pacman, blinky):
        pac_col, pac_row = pacman.get_tile()
        pac_dir = pacman.dir
        
        if self.mode == "scatter":
            self.target = self.scatter_target
        else:  # chase mode
            if self.name == "blinky":
                self.target = (pac_col, pac_row)
            elif self.name == "pinky":
                # Target 4 tiles ahead of Pac-Man
                target_col = pac_col + pac_dir[0] * 4
                target_row = pac_row + pac_dir[1] * 4
                self.target = (target_col, target_row)
            elif self.name == "inky":
                # Complex targeting involving Blinky
                blinky_col, blinky_row = blinky.get_tile()
                ahead_col = pac_col + pac_dir[0] * 2
                ahead_row = pac_row + pac_dir[1] * 2
                target_col = ahead_col + (ahead_col - blinky_col)
                target_row = ahead_row + (ahead_row - blinky_row)
                self.target = (target_col, target_row)
            elif self.name == "clyde":
                # If close to Pac-Man, scatter; otherwise chase
                distance = math.hypot(pac_col - math.cos, pac_row - pow)
                if distance < 8:
                    self.target = self.scatter_target
                else:
                    self.target = (pac_col, pac_row)
    
    def seek_target(self):
        col, row = self.get_tile()
        
        # If at intersection, choose best direction
        if abs(self.x - (col * TILE_SIZE + TILE_SIZE//2)) < 2 and \
           abs(self.y - (row * TILE_SIZE + TILE_SIZE//2)) < 2:
            
            best_dir = self.dir
            best_dist = float('inf')
            
            for direction in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                # Don't reverse unless necessary
                if direction == (-self.dir[0], -self.dir[1]):
                    continue
                
                next_col = col + direction[0]
                next_row = row + direction[1]
                
                # Check if valid move (simplified wall checking)
                if 0 <= next_col < MAZE_COLS and 0 <= next_row < MAZE_ROWS:
                    # Calculate distance to target
                    dist = math.hypot(self.target[0] - next_col, self.target[1] - next_row)
                    if dist < best_dist:
                        best_dist = dist
                        best_dir = direction
            
            self.dir = best_dir
        
        self.move_in_direction()
    
    def move_randomly(self):
        col, row = self.get_tile()
        
        if abs(self.x - (col * TILE_SIZE + TILE_SIZE//2)) < 2 and \
           abs(self.y - (row * TILE_SIZE + TILE_SIZE//2)) < 2:
            
            # Choose random direction (not reverse)
            possible_dirs = []
            for direction in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                if direction != (-self.dir[0], -self.dir[1]):
                    possible_dirs.append(direction)
            
            if possible_dirs:
                self.dir = random.choice(possible_dirs)
        
        self.move_in_direction()
    
    def move_in_direction(self):
        self.x += self.dir[0] * self.speed
        self.y += self.dir[1] * self.speed
        
        # Tunnel wrapping
        row = int(self.y // TILE_SIZE)
        if row == 14:
            if self.x < 0:
                self.x = SCREEN_WIDTH - TILE_SIZE//2
            elif self.x >= SCREEN_WIDTH:
                self.x = TILE_SIZE//2
    
    def draw(self, screen):
        center = (int(self.x), int(self.y))
        
        if self.mode == "dead":
            # Draw eyes only
            pygame.draw.circle(screen, WHITE, (center[0] - 3, center[1] - 2), 3)
            pygame.draw.circle(screen, WHITE, (center[0] + 3, center[1] - 2), 3)
            pygame.draw.circle(screen, BLACK, (center[0] - 3, center[1] - 2), 1)
            pygame.draw.circle(screen, BLACK, (center[0] + 3, center[1] - 2), 1)
        else:
            # Draw ghost body
            color = BLUE_GHOST if self.frightened else self.original_color
            pygame.draw.circle(screen, color, center, 8)
            
            # Draw eyes
            pygame.draw.circle(screen, WHITE, (center[0] - 3, center[1] - 2), 2)
            pygame.draw.circle(screen, WHITE, (center[0] + 3, center[1] - 2), 2)
            pygame.draw.circle(screen, BLACK, (center[0] - 3, center[1] - 2), 1)
            pygame.draw.circle(screen, BLACK, (center[0] + 3, center[1] - 2), 1)

if __name__ == "__main__":
    game = Game()
    game.run()
