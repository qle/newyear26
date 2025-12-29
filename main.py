
import curses
import time
import random
import math
import datetime

# --- Constants ---
TARGET_DATE = datetime.datetime(2026, 1, 1, 0, 0, 0)
GRAVITY = 0.05
PARTICLE_CHARS = ['*', '.', '+', '·']

# --- Digital Clock Font ---
# 5x5 square matrix for each digit
_DIGITS = {
    '0': ["XXXXXXXXXX", "XX      XX", "XX      XX", "XX      XX", "XXXXXXXXXX"],
    '1': ["    XX    ", "    XX    ", "    XX    ", "    XX    ", "    XX    "],
    '2': ["XXXXXXXXXX", "        XX", "XXXXXXXXXX", "XX        ", "XXXXXXXXXX"],
    '3': ["XXXXXXXXXX", "        XX", "XXXXXXXXXX", "        XX", "XXXXXXXXXX"],
    '4': ["XX      XX", "XX      XX", "XXXXXXXXXX", "        XX", "        XX"],
    '5': ["XXXXXXXXXX", "XX        ", "XXXXXXXXXX", "        XX", "XXXXXXXXXX"],
    '6': ["XXXXXXXXXX", "XX        ", "XXXXXXXXXX", "XX      XX", "XXXXXXXXXX"],
    '7': ["XXXXXXXXXX", "        XX", "        XX", "        XX", "        XX"],
    '8': ["XXXXXXXXXX", "XX      XX", "XXXXXXXXXX", "XX      XX", "XXXXXXXXXX"],
    '9': ["XXXXXXXXXX", "XX      XX", "XXXXXXXXXX", "        XX", "XXXXXXXXXX"],
    ':': ["          ", "    XX    ", "          ", "    XX    ", "          "],
}

def create_tall_digits(scale_factor):
    """Scales the digits vertically."""
    scaled_digits = {}
    for digit, matrix in _DIGITS.items():
        scaled_matrix = []
        for row in matrix:
            scaled_matrix.extend([row] * scale_factor)
        scaled_digits[digit] = scaled_matrix
    return scaled_digits

DIGITS = create_tall_digits(2)

# --- Classes ---
class Particle:
    """A single particle for the firework explosion."""
    def __init__(self, x, y, vx, vy, color, char, lifespan):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.char = char
        self.lifespan = lifespan

    def update(self, sh):
        self.x += self.vx
        self.y += self.vy
        self.vy += GRAVITY
        self.lifespan -= 1
        return []

    def draw(self, stdscr):
        if self.lifespan > 0:
            try:
                stdscr.addch(int(self.y), int(self.x), self.char, self.color)
            except curses.error:
                pass


class Firework(Particle):
    """A firework rocket that explodes."""
    def __init__(self, x, y, color):
        super().__init__(x, y, random.uniform(-1.5, 1.5), -random.uniform(2.0, 3.0), color, '^', 1000)
        self.has_reached_apex = False
        self.descent_counter = 0
        self.shape = random.choice(['circle', 'star', 'square'])
        self.has_reached_apex = False # New state variable
        self.descent_counter = 0     # New counter for descent

    def update(self, sh):
        newly_created_trail_particles = []
        num_trail_particles = random.randint(4, 7) # Increased number of particles for thicker trajectory
        for _ in range(num_trail_particles):
            trail_lifespan = random.randint(5, 15)
            trail_char = random.choice(['.', '`'])
            # Small random offsets for thickness
            offset_x = random.uniform(-0.5, 0.5)
            offset_y = random.uniform(-0.2, 0.2) # y-offset smaller due to terminal aspect ratio
            trail_particle = Particle(self.x + offset_x, self.y + offset_y, 0, 0, self.color | curses.A_BOLD, trail_char, trail_lifespan)
            newly_created_trail_particles.append(trail_particle)

        # Now, move the firework to its new position.
        super().update(sh)
        
        # Position apex just above the numbers
        min_apex_y = sh // 2 - 10 
        if self.y < min_apex_y:
            self.y = min_apex_y
            if self.vy < 0: # If it was still moving upwards, force explosion
                self.vy = 0 
        
        # Explode on the way down logic
        if not self.has_reached_apex:
            if self.vy >= 0: # Apex reached
                self.has_reached_apex = True
                self.descent_counter = random.randint(3, 10) # Shorter descent duration before explosion
        else: # Already descending
            self.descent_counter -= 1
            if self.descent_counter <= 0:
                self.lifespan = 0 # Mark for removal (explosion)

        return newly_created_trail_particles

    def explode(self, particles):
        num_particles = random.randint(100, 200)

        # Pre-calculate shape-specific parameters
        if self.shape == 'star':
            num_points = random.randint(5, 8)
            base_angle = random.uniform(0, 2 * math.pi)

        for _ in range(num_particles):
            if self.shape == 'circle':
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(0.5, 1.5)
                vx = math.cos(angle) * speed * 2.0 # Aspect ratio correction
                vy = math.sin(angle) * speed
            elif self.shape == 'star':
                point = random.randint(0, num_points - 1)
                angle = base_angle + (2 * math.pi / num_points) * point + random.uniform(-0.1, 0.1)
                speed = random.uniform(1.0, 3.0) # Starbursts are faster
                vx = math.cos(angle) * speed * 2.0 # Aspect ratio correction
                vy = math.sin(angle) * speed
            elif self.shape == 'square':
                side = random.randint(0, 3)
                speed = random.uniform(0.5, 1.5)
                if side == 0:   # Top
                    vx = random.uniform(-1, 1) * speed
                    vy = -speed
                elif side == 1: # Bottom
                    vx = random.uniform(-1, 1) * speed
                    vy = speed
                elif side == 2: # Left
                    vx = -speed
                    vy = random.uniform(-1, 1) * speed
                else:           # Right
                    vx = speed
                    vy = random.uniform(-1, 1) * speed
                vx *= 2.0 # Aspect ratio correction

            lifespan = random.randint(30, 60)
            char = random.choice(PARTICLE_CHARS)
            particles.append(Particle(self.x, self.y, vx, vy, self.color, char, lifespan))


# --- Drawing Functions ---
def draw_digit(stdscr, num_char, x_offset, y_offset, color):
    """Draws a single 5x5 digit."""
    digit_matrix = DIGITS.get(num_char, [])
    for r, row_str in enumerate(digit_matrix):
        for c, char in enumerate(row_str):
            if char != ' ':
                try:
                    stdscr.addch(y_offset + r, x_offset + c, char, color)
                except curses.error:
                    pass

def draw_time(stdscr, days, hours, mins, secs, x_offset, y_offset, color):
    """Draws the full time string."""
    time_str = f"{days:02d}:{hours:02d}:{mins:02d}:{secs:02d}"
    char_width = 12  # 10 for digit, 2 for space
    
    # Calculate starting position to center the clock
    total_width = len(time_str) * char_width
    start_x = x_offset - total_width // 2

    for i, char in enumerate(time_str):
        draw_digit(stdscr, char, start_x + i * char_width, y_offset, color)


# --- Main Application ---
def main(stdscr):
    """Main application loop."""
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    # Colors: ID, Foreground, Background (-1 for default)
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_BLUE, -1)
    
    colors = [curses.color_pair(i) for i in range(2, 8)]
    white_color = curses.color_pair(1)

    fireworks = []
    particles = []
    
    last_esc_press = 0

    while True:
        # --- Handle Input ---
        key = stdscr.getch()
        if key == 27: # ESC key
            current_time = time.time()
            if current_time - last_esc_press < 0.25:
                break # Exit on double press
            last_esc_press = current_time
        elif key == curses.KEY_RESIZE:
            stdscr.clear()


        # --- Update State ---
        sh, sw = stdscr.getmaxyx()

        # Update countdown
        now = datetime.datetime.now()
        delta = TARGET_DATE - now
        
        if delta.total_seconds() <= 0:
            # Happy New Year!
            days, hours, mins, secs = 0, 0, 0, 0
        else:
            days = delta.days
            secs = delta.seconds
            hours = secs // 3600
            mins = (secs % 3600) // 60
            secs = secs % 60
        
        # Randomly launch a new firework
        if random.random() < 0.02:
            fireworks.append(Firework(random.randint(sw//4, 3*sw//4), sh-1, random.choice(colors)))

        # Update fireworks
        for fw in fireworks[:]:
            new_particles = fw.update(sh)
            particles.extend(new_particles)
            if fw.lifespan <= 0:
                fw.explode(particles)
                fireworks.remove(fw)

        # Update particles
        for p in particles[:]:
            new_particles = p.update(sh)
            particles.extend(new_particles)
            if p.lifespan <= 0:
                particles.remove(p)

        # --- Draw Frame ---
        stdscr.clear()

        # Draw time
        draw_time(stdscr, days, hours, mins, secs, sw // 2, sh // 2 - 7, white_color)
        
        # Draw message
        msg = "Press escape twice to exit terminal"
        stdscr.addstr(sh // 2 + 10, sw // 2 - len(msg)//2, msg, curses.A_BOLD)


        # Draw fireworks and particles
        for fw in fireworks:
            fw.draw(stdscr)
        for p in particles:
            p.draw(stdscr)

        stdscr.refresh()
        
        if delta.total_seconds() <= 0:
            time.sleep(1)
            # Display Happy New Year message
            stdscr.clear()
            h_msg = "Happy New Year 2026!"
            stdscr.addstr(sh // 2, sw // 2 - len(h_msg)//2, h_msg, curses.A_BOLD | random.choice(colors))
            stdscr.refresh()
            time.sleep(5)
            break

    # End message
    stdscr.clear()
    end_msg = "Fireworks simulation ended."
    stdscr.addstr(sh // 2, sw // 2 - len(end_msg)//2, end_msg)
    stdscr.refresh()
    time.sleep(2)


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except curses.error as e:
        print(f"Error running curses application: {e}")
        print("Your terminal may not support this animation.")

