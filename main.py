
import curses
# -*- coding: utf-8 -*-
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
    '0': [" XXX ", "X   X", "X   X", "X   X", "X   X", "X   X", " XXX "],
    '1': ["  X  ", " XX  ", "  X  ", "  X  ", "  X  ", "  X  ", " XXX "],
    '2': [" XXX ", "X   X", "    X", "   X ", "  X  ", " X   ", "XXXXX"],
    '3': [" XXX ", "X   X", "    X", " XXX ", "    X", "X   X", " XXX "],
    '4': ["X   X", "X   X", "X   X", "XXXXX", "    X", "    X", "    X"],
    '5': ["XXXXX", "X    ", "X    ", " XXX ", "    X", "X   X", " XXX "],
    '6': [" XXX ", "X    ", "X    ", "XXXXX", "X   X", "X   X", " XXX "],
    '7': ["XXXXX", "X   X", "    X", "   X ", "  X  ", "  X  ", "  X  "],
    '8': [" XXX ", "X   X", "X   X", " XXX ", "X   X", "X   X", " XXX "],
    '9': [" XXX ", "X   X", "X   X", "XXXXX", "    X", "    X", " XXX "],
    ':': ["     ", "  X  ", "     ", "     ", "     ", "  X  ", "     "],
}



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
        self.shape = random.choice(['circle', 'star', 'square', 'heart'])
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

    def explode(self):
        new_particles = []
        max_lifespan = 0
        num_particles = random.randint(100, 200)

        # Pre-calculate shape-specific parameters
        if self.shape == 'star':
            num_points = random.randint(5, 8)
            base_angle = random.uniform(0, 2 * math.pi)

        if self.shape == 'heart':
            heart_points_template = [
                (0, -2), (1, -3), (2, -2), (3, -1), (4, 0),
                (3, 1), (2, 2), (1, 3), (0, 4), (-1, 3),
                (-2, 2), (-3, 1), (-4, 0), (-3, -1), (-2, -2), (-1, -3)
            ]
            scale_heart = 0.5
            heart_points = [(int(p[0]*scale_heart), int(p[1]*scale_heart)) for p in heart_points_template]
            num_particles = random.randint(150, 250) # More particles for heart to be visible


        for _ in range(num_particles):
            if self.shape == 'circle':
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(0.5, 1.5)
                vx = math.cos(angle) * speed * 2.0 # Aspect ratio correction
                vy = math.sin(angle) * speed
                lifespan = random.randint(60, 120)
            elif self.shape == 'star':
                point = random.randint(0, num_points - 1)
                angle = base_angle + (2 * math.pi / num_points) * point + random.uniform(-0.1, 0.1)
                speed = random.uniform(1.0, 3.0) # Starbursts are faster
                vx = math.cos(angle) * speed * 2.0 # Aspect ratio correction
                vy = math.sin(angle) * speed
                lifespan = random.randint(60, 120)
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
                lifespan = random.randint(60, 120)
            elif self.shape == 'heart':
                px, py = random.choice(heart_points)
                
                dev_x = random.uniform(-0.8, 0.8)
                dev_y = random.uniform(-0.8, 0.8)
                
                # Use current firework position as base
                start_x = self.x + px + dev_x
                start_y = self.y + py + dev_y

                angle = math.atan2(py + dev_y, px + dev_x)
                angle_dev = random.uniform(-math.pi/8, math.pi/8)
                outward_speed = random.uniform(0.1, 0.6)
                
                vx = (px + dev_x) * 0.1 + math.cos(angle + angle_dev) * outward_speed * 2.0
                vy = (py + dev_y) * 0.1 + math.sin(angle + angle_dev) * outward_speed
                lifespan = random.randint(40, 80)
            
            char = random.choice(PARTICLE_CHARS)
            new_particles.append(Particle(self.x, self.y, vx, vy, self.color, char, lifespan))

        
        return new_particles


# --- Drawing Functions ---
def draw_digit(stdscr, num_char, x_offset, y_offset, color):
    """Draws a single 5x5 digit."""
    digit_matrix = _DIGITS.get(num_char, [])
    for r, row_str in enumerate(digit_matrix):
        for c, char in enumerate(row_str):
            if char != ' ':
                try:
                    stdscr.addch(y_offset + r, x_offset + c, char, color)
                except curses.error:
                    pass

def draw_time(stdscr, days, hours, mins, secs, x_offset, y_offset, color, sh, sw):
    """Draws the full time string, scaled to the window size."""
    time_str = f"{days:02d}:{hours:02d}:{mins:02d}:{secs:02d}"

    # --- Fixed Scaling ---
    digit_width = 5
    spacing = 1 # Adjusted spacing for 5x7 digits
    char_cell_width = digit_width + spacing
    total_width = len(time_str) * char_cell_width

    # Check if the terminal is too small to draw the numbers
    if sw < total_width or sh < 7: # Base digit is 7 high
        msg = "Terminal too small"
        try:
            stdscr.addstr(sh // 2, (sw - len(msg)) // 2, msg)
        except curses.error:
            pass
        return
    
    # Calculate starting position to center the clock horizontally
    start_x = x_offset - total_width // 2

    # Adjust y_offset to vertically center the 7-high digits
    y_offset = (sh - 7) // 2

    for i, char in enumerate(time_str):
        draw_digit(stdscr, char, start_x + i * char_cell_width, y_offset, color)


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
    explosion_texts_to_display = []
    
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
            new_particles_from_fw = fw.update(sh)
            particles.extend(new_particles_from_fw)
            if fw.lifespan <= 0:
                spawned_particles = fw.explode()
                particles.extend(spawned_particles)
                
                if spawned_particles: # Add explosion text if particles were spawned
                    explosion_texts_to_display.append({
                        'text': fw.shape,
                        'x': int(fw.x),
                        'y': int(fw.y),
                        'particles': spawned_particles, # Store particle references
                        'display_countdown': 10 # Display for approximately 1 second
                    })
                fireworks.remove(fw)

        # Update particles (existing logic)
        for p in particles[:]:
            p.update(sh)
            if p.lifespan <= 0:
                particles.remove(p)
        
        # Update explosion texts: filter out texts with no remaining active particles or expired countdown
        for text_obj in explosion_texts_to_display[:]:
            text_obj['particles'] = [p for p in text_obj['particles'] if p.lifespan > 0]
            text_obj['display_countdown'] -= 1
            
            if not text_obj['particles'] or text_obj['display_countdown'] <= 0:
                explosion_texts_to_display.remove(text_obj)


        # --- Draw Frame ---
        stdscr.clear()

        # Draw time
        draw_time(stdscr, days, hours, mins, secs, sw // 2, sh // 2 - 5, white_color, sh, sw)
        
        # Draw message
        msg = "Press escape twice to exit terminal"
        stdscr.addstr(sh // 2 + 10, sw // 2 - len(msg)//2, msg, curses.A_BOLD)


        # Draw fireworks and particles
        for fw in fireworks:
            fw.draw(stdscr)
        for p in particles:
            p.draw(stdscr)
        
        # Draw explosion texts
        for text_obj in explosion_texts_to_display:
            # The text is drawn if the object still exists in the list
            try:
                # Center the text around the explosion point
                text_x = text_obj['x'] - len(text_obj['text']) // 2
                stdscr.addstr(int(text_obj['y']), int(text_x), text_obj['text'], curses.A_BOLD | random.choice(colors))
            except curses.error:
                pass

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

