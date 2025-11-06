import pygame
import random
import math

# --- Initialize Pygame ---
pygame.init()
pygame.font.init()

# --- Game Constants ---
SCREEN_WIDTH = 1600 # Made screen wider
SCREEN_HEIGHT = 900 # Made screen taller
FPS = 60
GROUND_Y = 800 # Adjusted ground for new size
SKY_COLOR = (20, 20, 40)
GROUND_COLOR = (50, 50, 50)
GAME_DURATION_SECONDS = 60 # 1 minute timer
MAX_LEVEL = 10

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
LIGHT_GRAY = (170, 170, 170)
LIGHT_GREEN = (144, 238, 144)
LIGHT_RED = (240, 128, 128)
LIGHT_ORANGE = (255, 200, 100)

# --- Game Window ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Stickman Fighter")
clock = pygame.time.Clock()

# --- Fonts ---
try:
    # Try to use a more "game-like" font
    HEALTH_FONT = pygame.font.SysFont('Consolas', 24, bold=True)
    SPECIAL_FONT = pygame.font.SysFont('Consolas', 18, bold=True)
except:
    # Fallback to Arial
    HEALTH_FONT = pygame.font.SysFont('Arial', 22, bold=True)
    SPECIAL_FONT = pygame.font.SysFont('Arial', 16, bold=True)

GAME_OVER_FONT = pygame.font.SysFont('Arial', 75)
LEVEL_FONT = pygame.font.SysFont('Arial', 50)
TIMER_FONT = pygame.font.SysFont('Arial', 40, bold=True)
POWERUP_TITLE_FONT = pygame.font.SysFont('Arial', 60, bold=True)
POWERUP_DESC_FONT = pygame.font.SysFont('Arial', 28)

# --- Global Lists (will be reset each level) ---
projectiles = []
particles = []
text_animations = []
platforms = []
player = None
enemy = None

# --- Starry Sky (Static) ---
stars = []
for _ in range(100):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, GROUND_Y - 50) # Adjusted for new ground
    stars.append((x, y))

# --- Power-Up Definitions ---
all_powerups = [
    {'name': 'Health Boost', 'effect': 'max_health', 'value': 25, 'desc': '+25 Max HP'},
    {'name': 'Damage Up', 'effect': 'damage', 'value': 2, 'desc': '+2 Melee Damage'},
    {'name': 'Speed Up', 'effect': 'speed', 'value': 0.5, 'desc': '+ Move Speed'},
    {'name': 'Special Cooldown', 'effect': 'special_cd', 'value': -30, 'desc': 'Special Recharges Faster'},
    {'name': 'Dash Cooldown', 'effect': 'dash_cd', 'value': -15, 'desc': 'Dash Recharges Faster'},
    {'name': 'Teleport Cooldown', 'effect': 'teleport_cd', 'value': -20, 'desc': 'Teleport Recharges Faster'},
    {'name': 'Full Heal', 'effect': 'full_heal', 'value': 0, 'desc': 'Restores all HP (for next level)'},
    {'name': 'Critical Hit', 'effect': 'crit_chance', 'value': 0.1, 'desc': '+10% Crit Chance (2x Dmg)'},
    {'name': 'Fireball Damage', 'effect': 'fireball_damage', 'value': 10, 'desc': '+10 Fireball Damage'},
    {'name': 'Stomp Damage', 'effect': 'stomp_damage', 'value': 15, 'desc': '+15 Air Attack Damage'},
    {'name': 'Ultimate Charge', 'effect': 'ult_charge_rate', 'value': 5, 'desc': '+5 Bonus Ult Charge on Hit'},
    {'name': 'Air Dash', 'effect': 'max_air_dash', 'value': 1, 'desc': '+1 Max Air Dash'},
    {'name': 'Ultimate Aura', 'effect': 'ult_aura', 'value': 1, 'desc': '+Dmg/Speed when Ult is full'}
]
# Powerups the AI can receive
ai_powerups = [p for p in all_powerups if p['effect'] not in ['full_heal', 'ult_aura', 'ult_charge_rate']]

class Particle:
    """
    A simple particle for hit effects.
    """
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = random.uniform(-3, 3)
        self.vel_y = random.uniform(-5, 2)
        self.lifespan = 20 # Frames

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.4 # Gravity
        self.lifespan -= 1

    def draw(self, surface):
        if self.lifespan > 0:
            pygame.draw.rect(surface, self.color, (self.x, self.y, 4, 4))

class TextAnimation:
    """
    Displays floating, fading text for special moves.
    """
    def __init__(self, text, x, y, color, font=SPECIAL_FONT, lifespan=40):
        self.text = text
        self.x = int(x)
        self.y = int(y)
        self.color = color
        self.font = font
        self.lifespan = lifespan
        self.max_lifespan = lifespan

    def update(self):
        self.y -= 1 # Float up
        self.lifespan -= 1

    def draw(self, surface):
        # Calculate alpha for fading
        alpha = int(255 * (self.lifespan / self.max_lifespan))
        if alpha < 0: alpha = 0
        
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        surface.blit(text_surf, text_rect)

class Projectile:
    """
    A fireball special move.
    """
    def __init__(self, x, y, direction, color, damage, is_player_projectile): # Added damage
        self.x = int(x)
        self.y = int(y)
        self.direction = direction
        self.color = color # This will be the "core" color
        self.vel = 12 * direction
        self.radius = 15 # Made it bigger
        self.damage = damage # Use passed-in damage
        self.is_player_projectile = is_player_projectile

    def update(self):
        self.x += self.vel

    def draw(self, surface):
        # Draw a "fiery" effect with multiple circles
        # Outer glow (Red)
        pygame.draw.circle(surface, RED, (self.x, self.y), self.radius)
        # Middle (Orange)
        pygame.draw.circle(surface, ORANGE, (self.x + random.randint(-2, 2), self.y + random.randint(-2, 2)), int(self.radius * 0.75))
        # Core (Yellow)
        pygame.draw.circle(surface, YELLOW, (self.x + random.randint(-1, 1), self.y + random.randint(-1, 1)), int(self.radius * 0.5))

    def get_hitbox(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

class Stickman:
    """
    Represents both the Player and the Enemy.
    Handles drawing, movement, attacking, and health.
    """
    def __init__(self, x, y, color, is_player):
        self.x = x
        self.y = y
        self.color = color
        self.is_player = is_player
        
        self.width = 50
        self.height = 100
        
        self.vel_x = 0
        self.vel_y = 0
        self.jump_power = 18
        self.gravity = 0.9
        self.on_ground = True
        
        # Stats that get modified by powerups
        self.health = 100
        self.max_health = 100
        self.base_damage = 10 # Store base stats for auras
        self.base_speed = 7
        self.damage = 10
        self.speed = 7
        self.speed_multiplier = 1.0 # For AI
        self.crit_chance = 0.0
        self.fireball_damage = 30
        self.stomp_damage = 15
        self.ultimate_damage = 75 # Player ult damage
        self.ult_charge_rate = 0 # Bonus ult charge
        self.has_ult_aura = False
        
        self.is_attacking = False
        self.attack_type = "punch"
        self.attack_frame = 0
        self.attack_cooldown = 0
        self.attack_hitbox = None
        
        self.combo_step = 0
        self.combo_timer = 0
        
        self.special_cooldown = 0
        self.max_special_cooldown = 180
        
        # New Ultimate stats
        self.ultimate_charge = 0
        self.max_ultimate_charge = 100
        self.is_ulting = False
        self.ult_step = 0 # 0: inactive, 1: rising/paused, 2: slamming
        self.ult_timer = 0
        self.ult_target_x = 0
        self.ult_hit_count = 0 # For enemy ult
        
        self.dodge_cooldown = 0
        
        self.hit_duration = 0 # Red flash
        self.is_alive = True
        
        self.is_dying = False 
        self.death_anim_timer = 0
        
        self.is_blocking = False
        self.is_stunned = 0
        
        self.is_hit = False # New state for hit animation
        self.hit_anim_timer = 0
        
        # Dash state
        self.dash_cooldown = 0
        self.max_dash_cooldown = 60
        self.dash_duration = 0
        self.is_dashing = False
        self.dash_invulnerability = 0
        self.max_air_dash = 1 # New Air Dash
        self.air_dash_count = 1
        
        # Teleport state
        self.teleport_cooldown = 0
        self.max_teleport_cooldown = 120
        
        self.walk_frame = 0
        self.direction = 1 if is_player else -1

    def draw(self, surface):
        """Draws the stickman on the screen."""
        if self.is_dying:
            self.draw_dying_animation(surface)
            return
        elif not self.is_alive:
            self.draw_death(surface)
            return
            
        # Change color if recently hit
        draw_color = RED if self.hit_duration > 0 else self.color
        if self.hit_duration > 0:
            self.hit_duration -= 1
            
        if self.is_stunned > 0:
            # Flash white when stunned
            draw_color = WHITE if (self.is_stunned // 4) % 2 == 0 else self.color
        
        # Ultimate "charging" flash
        if self.is_ulting and self.ult_step == 1:
            draw_color = YELLOW if (self.ult_timer // 3) % 2 == 0 else self.color
        
        # Enemy ult "shadow" flash
        if self.is_ulting and self.ult_step == 2 and not self.is_player:
            draw_color = PURPLE if (self.ult_timer // 2) % 2 == 0 else BLACK
            
        head_pos = (int(self.x), int(self.y - self.height * 0.9))
        body_start = head_pos
        body_end = (int(self.x), int(self.y - self.height * 0.4))
        
        # Legs
        leg1_end = (int(self.x - self.width * 0.25 * self.direction), int(self.y))
        leg2_end = (int(self.x + self.width * 0.25 * self.direction), int(self.y))
        
        # Arms
        arm1_start = (int(self.x), int(self.y - self.height * 0.7))
        arm2_start = arm1_start
        
        # Default arm positions
        arm1_end = (int(self.x - self.width * 0.4 * self.direction), int(self.y - self.height * 0.5))
        arm2_end = (int(self.x + self.width * 0.4 * self.direction), int(self.y - self.height * 0.5))

        # --- Animation Logic ---
        if self.is_hit:
            # --- New Hit Stun Pose ---
            # Jerk body and head back
            head_pos = (int(self.x - 5 * self.direction), int(self.y - self.height * 0.9))
            body_end = (int(self.x - 3 * self.direction), int(self.y - self.height * 0.4))
            # Pull arms and legs in
            arm1_end = (int(self.x - self.width * 0.2 * self.direction), int(self.y - self.height * 0.6))
            arm2_end = (int(self.x + self.width * 0.2 * self.direction), int(self.y - self.height * 0.6))
            leg1_end = (int(self.x - self.width * 0.1 * self.direction), int(self.y - 10))
            leg2_end = (int(self.x + self.width * 0.1 * self.direction), int(self.y - 10))
        elif self.is_dashing:
            # Dashing pose
            body_end = (int(self.x + self.width * 0.3 * self.direction), int(self.y - self.height * 0.4))
            arm1_end = (int(self.x - self.width * 0.2 * self.direction), int(self.y - self.height * 0.5))
            arm2_end = (int(self.x + self.width * 0.5 * self.direction), int(self.y - self.height * 0.5))
            leg1_end = (int(self.x - self.width * 0.1 * self.direction), int(self.y))
            leg2_end = (int(self.x + self.width * 0.1 * self.direction), int(self.y))
        elif self.is_blocking:
            # Blocking Pose
            body_end = (int(self.x), int(self.y - self.height * 0.4))
            arm1_end = (int(self.x + self.width * 0.4 * self.direction), int(self.y - self.height * 0.8))
            arm2_end = (int(self.x - self.width * 0.4 * self.direction), int(self.y - self.height * 0.8))
            leg1_end = (int(self.x - self.width * 0.2 * self.direction), int(self.y))
            leg2_end = (int(self.x + self.width * 0.2 * self.direction), int(self.y))
        elif not self.on_ground:
            # Jump pose (unless ulting)
            if not (self.is_ulting and self.ult_step == 1): # Don't do jump pose if charging ult
                leg1_end = (int(self.x - self.width * 0.1 * self.direction), int(self.y - self.height * 0.2))
                leg2_end = (int(self.x + self.width * 0.1 * self.direction), int(self.y - self.height * 0.2))
                arm1_end = (int(self.x - self.width * 0.3 * self.direction), int(self.y - self.height * 0.8))
                arm2_end = (int(self.x + self.width * 0.3 * self.direction), int(self.y - self.height * 0.8))
        elif self.vel_x != 0:
            # Walk cycle
            self.walk_frame += 0.5
            leg_offset = math.sin(self.walk_frame) * self.width * 0.3
            leg1_end = (int(self.x - leg_offset), int(self.y))
            leg2_end = (int(self.x + leg_offset), int(self.y))
        
        # Attacking animation
        if self.is_attacking:
            if self.attack_type == "punch":
                if self.direction == 1:
                    arm2_end = (int(self.x + self.width * 0.8 * self.direction), int(self.y - self.height * 0.7))
                else:
                    arm1_end = (int(self.x + self.width * 0.8 * self.direction), int(self.y - self.height * 0.7))
            elif self.attack_type == "kick":
                if self.direction == 1:
                    leg2_end = (int(self.x + self.width * 0.6 * self.direction), int(self.y - self.height * 0.2))
                else:
                    leg1_end = (int(self.x + self.width * 0.6 * self.direction), int(self.y - self.height * 0.2))
            elif self.attack_type == "fireball":
                arm1_end = (int(self.x + self.width * 0.6 * self.direction), int(self.y - self.height * 0.7))
                arm2_end = (int(self.x + self.width * 0.6 * self.direction), int(self.y - self.height * 0.7))
            elif self.attack_type == "air_kick":
                leg1_end = (int(self.x + self.width * 0.4 * self.direction), int(self.y - self.height * 0.3))
                leg2_end = (int(self.x - self.width * 0.1 * self.direction), int(self.y - self.height * 0.1))
                arm1_end = (int(self.x - self.width * 0.3 * self.direction), int(self.y - self.height * 0.8))
                arm2_end = (int(self.x + self.width * 0.3 * self.direction), int(self.y - self.height * 0.8))
            elif self.attack_type == "ground_pound":
                leg1_end = (int(self.x - self.width * 0.1 * self.direction), int(self.y - self.height * 0.2))
                leg2_end = (int(self.x + self.width * 0.1 * self.direction), int(self.y - self.height * 0.2))
                arm1_end = (int(self.x - self.width * 0.3 * self.direction), int(self.y - self.height * 0.3))
                arm2_end = (int(self.x + self.width * 0.3 * self.direction), int(self.y - self.height * 0.3))
            elif self.attack_type == "ultimate_pound":
                # Pose for meteor slam
                draw_color = ORANGE # Slam is fiery
                leg1_end = (int(self.x - self.width * 0.2 * self.direction), int(self.y - self.height * 0.1))
                leg2_end = (int(self.x + self.width * 0.2 * self.direction), int(self.y - self.height * 0.1))
                arm1_end = (int(self.x - self.width * 0.4 * self.direction), int(self.y - self.height * 0.3))
                arm2_end = (int(self.x + self.width * 0.4 * self.direction), int(self.y - self.height * 0.3))
            elif self.attack_type == "shadow_punch":
                # Rapid punch animation
                if self.direction == 1:
                    arm2_end = (int(self.x + self.width * 0.7 * self.direction), int(self.y - self.height * 0.7))
                else:
                    arm1_end = (int(self.x + self.width * 0.7 * self.direction), int(self.y - self.height * 0.7))
        
        # Ult charging pose
        if self.is_ulting and self.ult_step == 1:
            arm1_end = (int(self.x - self.width * 0.3 * self.direction), int(self.y - self.height * 0.8))
            arm2_end = (int(self.x + self.width * 0.3 * self.direction), int(self.y - self.height * 0.8))
            
        # --- Draw Ultimate Aura ---
        aura_color = None
        if self.has_ult_aura and self.ultimate_charge == self.max_ultimate_charge and not self.is_ulting:
            aura_color = YELLOW
        elif self.is_ulting and self.ult_step == 2 and not self.is_player: # Shadow Barrage aura
             aura_color = PURPLE
            
        if aura_color:
            aura_radius = 20 + abs(math.sin(pygame.time.get_ticks() * 0.01) * 10) # Pulsing radius
            aura_alpha = 100 + abs(math.sin(pygame.time.get_ticks() * 0.01) * 50) # Pulsing alpha
            aura_surf = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (aura_color[0], aura_color[1], aura_color[2], aura_alpha), (aura_radius, aura_radius), aura_radius)
            surface.blit(aura_surf, (self.x - aura_radius, self.y - self.height/2 - aura_radius/2))


        # Draw body parts
        pygame.draw.circle(surface, draw_color, head_pos, int(self.height * 0.1)) # Head
        pygame.draw.line(surface, draw_color, body_start, body_end, 5) # Body
        pygame.draw.line(surface, draw_color, body_end, leg1_end, 5) # Leg 1
        pygame.draw.line(surface, draw_color, body_end, leg2_end, 5) # Leg 2
        pygame.draw.line(surface, draw_color, arm1_start, arm1_end, 5) # Arm 1
        pygame.draw.line(surface, draw_color, arm2_start, arm2_end, 5) # Arm 2
        
        # --- Arm-end (Gloves / Hands) ---
        arm1_hand_pos = (arm1_end[0], arm1_end[1])
        arm2_hand_pos = (arm2_end[0], arm2_end[1])
        
        # --- "Skin" ---
        ult_ready_color = YELLOW if (self.has_ult_aura and self.ultimate_charge == self.max_ultimate_charge) else None

        if self.is_player:
            # Player headband
            headband_y = head_pos[1]
            headband_color = ult_ready_color if ult_ready_color else WHITE
            pygame.draw.line(surface, headband_color, 
                             (head_pos[0] - int(self.height * 0.1), headband_y), 
                             (head_pos[0] + int(self.height * 0.1), headband_y), 4)
            # Player cape
            cape_start = (int(self.x - (3 * self.direction)), int(self.y - self.height * 0.65))
            pygame.draw.rect(surface, BLUE, (cape_start[0], cape_start[1], 8, 30))
            # Player gloves
            glove_color = ult_ready_color if ult_ready_color else BLUE
            pygame.draw.circle(surface, glove_color, arm1_hand_pos, 8)
            pygame.draw.circle(surface, glove_color, arm2_hand_pos, 8)
            
        else:
            # Enemy "angry eyes"
            eye_y = head_pos[1] - int(self.height * 0.03)
            eye1_start = (head_pos[0] + (self.height * 0.02) * self.direction, eye_y)
            eye1_end = (head_pos[0] + (self.height * 0.07) * self.direction, eye_y + int(self.height * 0.02))
            eye2_start = (head_pos[0] - (self.height * 0.07) * self.direction, eye_y + int(self.height * 0.02))
            eye2_end = (head_pos[0] - (self.height * 0.02) * self.direction, eye_y)
            pygame.draw.line(surface, BLACK, eye1_start, eye1_end, 3)
            pygame.draw.line(surface, BLACK, eye2_start, eye2_end, 3)
            
            # Enemy "horns"
            head_center_x = head_pos[0]
            head_top_y = head_pos[1] - int(self.height * 0.1)
            horn1_base = (head_center_x + (5 * self.direction), head_top_y)
            horn1_tip = (head_center_x + (8 * self.direction), head_top_y - 10)
            horn2_base = (head_center_x - (5 * self.direction), head_top_y)
            horn2_tip = (head_center_x - (8 * self.direction), head_top_y - 10)
            pygame.draw.line(surface, RED, horn1_base, horn1_tip, 4)
            pygame.draw.line(surface, RED, horn2_base, horn2_tip, 4)
            
            # Enemy Belt
            belt_y = int(self.y - self.height * 0.4)
            pygame.draw.rect(surface, RED, (self.x - 10, belt_y - 3, 20, 6))
            
            # Enemy Shoulder Pads
            shoulder_y = int(self.y - self.height * 0.7)
            shoulder_x_off = int(self.width * 0.1) * self.direction
            pygame.draw.rect(surface, RED, (self.x - shoulder_x_off - 5, shoulder_y - 5, 10, 10))
            pygame.draw.rect(surface, RED, (self.x + shoulder_x_off - 5, shoulder_y - 5, 10, 10))
            
            # Enemy hands
            pygame.draw.circle(surface, RED, arm1_hand_pos, 8)
            pygame.draw.circle(surface, RED, arm2_hand_pos, 8)


    def draw_dying_animation(self, surface):
        """Draws the stickman collapsing."""
        # progress is 0.0 at start of death, 1.0 at end
        progress = (60 - self.death_anim_timer) / 60.0
        progress = min(max(progress, 0.0), 1.0) # Clamp

        draw_color = self.color
        
        # Head starts at y - 0.9*h and ends at y - 0.1*h (on the ground)
        head_y_offset = -self.height * 0.9 + (self.height * 0.8 * progress)
        head_pos = (int(self.x), int(self.y + head_y_offset))
        
        # Body starts at y - 0.4*h and ends at y - 0.2*h (collapsed)
        body_y_offset = -self.height * 0.4 + (self.height * 0.2 * progress)
        body_end = (int(self.x), int(self.y + body_y_offset))
        body_start = (head_pos[0], head_pos[1] + int(self.height * 0.1)) # Connect to head
        
        # Legs stay at y
        leg1_end = (int(self.x - self.width * 0.25 * self.direction), int(self.y))
        leg2_end = (int(self.x + self.width * 0.25 * self.direction), int(self.y))
        
        # Arms collapse
        arm_start_y_offset = -self.height * 0.7 + (self.height * 0.5 * progress)
        arm1_start = (int(self.x), int(self.y + arm_start_y_offset))
        arm2_start = arm1_start
        
        arm_end_y_offset = -self.height * 0.5 + (self.height * 0.3 * progress)
        arm1_end = (int(self.x - self.width * 0.4 * self.direction), int(self.y + arm_end_y_offset))
        arm2_end = (int(self.x + self.width * 0.4 * self.direction), int(self.y + arm_end_y_offset))

        # Draw body parts
        pygame.draw.circle(surface, draw_color, head_pos, int(self.height * 0.1)) # Head
        pygame.draw.line(surface, draw_color, body_start, body_end, 5) # Body
        pygame.draw.line(surface, draw_color, body_end, leg1_end, 5) # Leg 1
        pygame.draw.line(surface, draw_color, body_end, leg2_end, 5) # Leg 2
        pygame.draw.line(surface, draw_color, arm1_start, arm1_end, 5) # Arm 1
        pygame.draw.line(surface, draw_color, arm2_start, arm2_end, 5) # Arm 2

    def draw_death(self, surface):
        """Draws a 'collapsed' stickman."""
        head_x = int(self.x)
        head_y = int(GROUND_Y - self.height * 0.1)
        
        # Draw collapsed parts on the ground
        pygame.draw.circle(surface, self.color, (head_x, head_y), int(self.height * 0.1)) # Head
        pygame.draw.line(surface, self.color, (head_x, head_y), (head_x, head_y - 20), 5) # Body
        pygame.draw.line(surface, self.color, (head_x, head_y - 20), (head_x - 15, head_y), 5) # Leg 1
        pygame.draw.line(surface, self.color, (head_x, head_y - 20), (head_x + 15, head_y), 5) # Leg 2
        pygame.draw.line(surface, self.color, (head_x, head_y - 15), (head_x - 20, head_y - 15), 5) # Arm 1
        pygame.draw.line(surface, self.color, (head_x, head_y - 15), (head_x + 20, head_y - 15), 5) # Arm 2

    def move(self, keys):
        """Handles player movement based on key presses."""
        if not self.is_alive or self.is_dying or self.is_stunned > 0 or self.is_dashing or self.is_hit or self.is_ulting:
            self.vel_x = 0
            return
            
        # --- DASH LOGIC ---
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        if keys[pygame.K_LSHIFT] and self.dash_cooldown == 0:
            if self.on_ground:
                self.is_dashing = True
                self.dash_duration = 10 # 1/6th of a second dash
                self.dash_cooldown = self.max_dash_cooldown
                self.dash_invulnerability = 10 # Invulnerable during dash
                particles.extend([Particle(self.x, self.y - 50, WHITE) for _ in range(10)]) # Dash effect
                return
            elif self.air_dash_count > 0: # --- NEW AIR DASH ---
                self.air_dash_count -= 1
                self.is_dashing = True
                self.dash_duration = 10
                self.dash_cooldown = self.max_dash_cooldown
                self.dash_invulnerability = 10
                self.vel_y = 0 # Stop falling
                particles.extend([Particle(self.x, self.y - 50, WHITE) for _ in range(10)]) # Dash effect
                return
            
        # --- TELEPORT LOGIC ---
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
        
        if keys[pygame.K_t] and self.teleport_cooldown == 0 and self.on_ground:
            self.teleport_cooldown = self.max_teleport_cooldown
            # Poof effect at old location
            for _ in range(20):
                particles.append(Particle(self.x, self.y - 50, PURPLE))
            
            self.x += 250 * self.direction # Teleport distance
            
            # Poof effect at new location
            for _ in range(20):
                particles.append(Particle(self.x, self.y - 50, PURPLE))
            return

        # --- BLOCKING & MOVEMENT ---
        self.is_blocking = False # Default to not blocking
        if keys[pygame.K_s] and self.on_ground:
            self.is_blocking = True

        # --- NORMAL MOVEMENT ---
        self.vel_x = 0
        if keys[pygame.K_a]:
            self.vel_x = -self.speed # Use speed stat
            self.direction = -1
        if keys[pygame.K_d]:
            self.vel_x = self.speed # Use speed stat
            self.direction = 1
        
        # Reduce speed if blocking
        if self.is_blocking:
            self.vel_x *= 0.5 # Half speed
            
        # Jump
        if keys[pygame.K_w] and self.on_ground and not self.is_blocking: # Can't jump while blocking
            self.vel_y = -self.jump_power
            self.on_ground = False

    def attack(self, keys, enemy_x): # Pass enemy_x for ult
        """Handles player attacks."""
        # --- ULTIMATE ATTACK ---
        if self.is_player and keys[pygame.K_u] and self.ultimate_charge == self.max_ultimate_charge and not self.is_ulting:
            self.is_ulting = True
            self.ult_step = 1
            self.ult_timer = 20 # Pause duration in air
            self.ultimate_charge = 0
            self.dash_invulnerability = 120 # Invulnerable for 2 seconds
            self.ult_target_x = enemy_x
            self.x = self.ult_target_x
            self.y = 100 # Teleport high
            self.vel_x = 0
            self.vel_y = 0
            self.is_attacking = False
            self.is_blocking = False
            text_animations.append(TextAnimation("METEOR SLAM!", self.x, self.y + 50, ORANGE, font=LEVEL_FONT, lifespan=60))
            return

        if self.attack_cooldown == 0 and self.is_alive and not self.is_dying and not self.is_blocking and self.is_stunned == 0 and not self.is_hit and not self.is_ulting:
            # --- GROUND POUND ---
            if not self.on_ground and keys[pygame.K_s]:
                self.is_attacking = True
                self.attack_type = "ground_pound"
                self.attack_frame = 30 # Active until hits ground
                self.attack_cooldown = 30
                self.vel_y = 25 # Rocket downwards
                self.vel_x = 0 # Stop horizontal movement
            # Air Kick
            elif not self.on_ground and keys[pygame.K_k]:
                self.is_attacking = True
                self.attack_type = "air_kick"
                self.attack_frame = 20 # Duration of attack
                self.attack_cooldown = 40 # Cooldown
                self.vel_y = 15 # Go down fast
                self.vel_x = 3 * self.direction
            # Ground attacks
            elif self.on_ground and keys[pygame.K_j]: # Punch
                self.is_attacking = True
                self.attack_type = "punch"
                self.attack_frame = 15 # Duration of attack
                self.attack_cooldown = 30 # Cooldown
                
                # Combo logic
                if self.combo_step == 0:
                    self.combo_step = 1
                    self.combo_timer = 30 # 0.5 seconds to press next key
            elif self.on_ground and keys[pygame.K_k]: # Kick
                self.is_attacking = True
                self.attack_type = "kick"
                self.attack_frame = 20 # Duration of attack
                self.attack_cooldown = 40 # Cooldown
                
                # Combo logic
                if self.combo_step == 1 and self.combo_timer > 0:
                    # COMBO SUCCESS!
                    self.special_cooldown = 0 # Instantly fill special
                    self.combo_step = 0
                    self.combo_timer = 0
                    text_animations.append(TextAnimation("COMBO!", self.x, self.y - 150, YELLOW))
                else:
                    # Reset combo if kick is pressed out of sequence
                    self.combo_step = 0
                    self.combo_timer = 0
                    
            elif self.on_ground and keys[pygame.K_l] and self.special_cooldown == 0: # Fireball
                self.is_attacking = True
                self.attack_type = "fireball"
                self.attack_frame = 10 # Short casting animation
                self.attack_cooldown = 20
                self.special_cooldown = self.max_special_cooldown
                # Spawn projectile in main loop
                text_animations.append(TextAnimation("FIREBALL!", self.x + (50 * self.direction), self.y - 150, PURPLE))
            
            # Reset combo if any other key is pressed
            if not keys[pygame.K_j] and not keys[pygame.K_k]:
                if self.combo_step == 1 and not self.is_attacking:
                    self.combo_step = 0 # Allows non-attack keys to not break combo
                    
    def update_ai(self, player):
        """Controls the enemy AI."""
        if not self.is_alive or self.is_dying or self.is_stunned > 0 or self.is_dashing or self.is_hit or self.is_ulting:
            self.vel_x = 0
            return
        
        # --- AI ULTIMATE ---
        if self.ultimate_charge == self.max_ultimate_charge and self.on_ground:
            self.is_ulting = True
            self.ult_step = 1 # Teleport step
            self.ultimate_charge = 0
            self.dash_invulnerability = 60 # Invulnerable for 1 sec
            self.is_attacking = False # Stop other attacks
            self.is_blocking = False
            text_animations.append(TextAnimation("SHADOW BARRAGE!", self.x, self.y - 150, PURPLE, font=LEVEL_FONT, lifespan=60))
        
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
            
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
            
        # Stop moving if blocking
        if self.is_blocking:
            self.vel_x = 0
            # AI will auto-stop blocking
            if self.attack_cooldown > 0: # Cooldown is used to time the block
                self.attack_cooldown -= 1
            else:
                self.is_blocking = False
            return
            
        # --- AI Dodge Logic ---
        if self.dodge_cooldown == 0 and self.on_ground:
            # 1. Dodge Projectiles
            for p in projectiles:
                if p.is_player_projectile: # Player's projectile
                    proj_dist = self.x - p.x
                    if 0 < proj_dist < 300 and abs(self.y - p.y) < 50:
                        if random.random() < 0.9: # 90% dodge chance
                            self.vel_y = -self.jump_power * 0.8 # Smaller dodge jump
                            self.on_ground = False
                            self.dodge_cooldown = 60
                            break
            # 2. Dodge/Block Melee
            distance = abs(player.x - self.x)
            if (player.is_attacking or (player.is_ulting and player.ult_step == 2)) and distance < 120 and self.dodge_cooldown == 0: # Also dodge meteor
                roll = random.random()
                if roll < 0.4: # 40% chance to block
                    self.is_blocking = True
                    self.vel_x = 0
                    self.attack_cooldown = 30 # How long to hold block
                    self.dodge_cooldown = 40
                elif roll < 0.8: # 40% chance to dodge
                    # New: 50/50 chance to dash or jump back
                    if random.random() < 0.5:
                        self.vel_x = -7 * self.direction # Dash back
                        self.dodge_cooldown = 40
                    elif self.dash_cooldown == 0: # AI Dash
                        self.is_dashing = True
                        self.dash_duration = 10 
                        self.dash_cooldown = self.max_dash_cooldown
                        self.dash_invulnerability = 10
                        self.vel_x = 25 * -self.direction # Dash away
                # 20% chance to do nothing and get hit
        
        # If dodging, don't do other logic
        if self.dodge_cooldown > 0:
            return
            
        # Face the player
        if player.x < self.x:
            self.direction = -1
            self.vel_x = -self.speed * self.speed_multiplier
        else:
            self.direction = 1
            self.vel_x = self.speed * self.speed_multiplier
            
        # Stop moving if too close or too far
        distance = abs(player.x - self.x)
        
        # --- AI Platform Logic ---
        player_on_platform = any(player.y == plat.top for plat in platforms)
        ai_on_platform = any(self.y == plat.top for plat in platforms)
        
        if player_on_platform and not ai_on_platform and self.on_ground:
            # Find closest platform to player
            closest_plat = min(platforms, key=lambda plat: abs(plat.centerx - player.x))
            if abs(self.x - closest_plat.centerx) < 50:
                if random.random() < 0.05:
                    self.vel_y = -self.jump_power
                    self.on_ground = False
            else:
                # Move towards that platform
                if closest_plat.centerx < self.x:
                    self.vel_x = -self.speed * self.speed_multiplier
                else:
                    self.vel_x = self.speed * self.speed_multiplier

        elif not player_on_platform and ai_on_platform and distance > 100:
            # If player is not on platform, just walk off
            pass
        
        # --- AI Air Kick / Ground Pound ---
        if not self.on_ground and self.y < player.y - 50 and abs(self.x - player.x) < 100 and self.attack_cooldown == 0:
            roll = random.random()
            if roll < 0.05: # 5% chance for Air Kick
                self.is_attacking = True
                self.attack_type = "air_kick"
                self.attack_frame = 20
                self.attack_cooldown = 40
                self.vel_y = 15
            elif roll < 0.10: # 5% chance for Ground Pound
                self.is_attacking = True
                self.attack_type = "ground_pound"
                self.attack_frame = 30
                self.attack_cooldown = 30
                self.vel_y = 25
                self.vel_x = 0
        
        # --- AI Teleport ---
        if self.teleport_cooldown == 0 and self.on_ground and distance > 400 and random.random() < 0.02:
            self.teleport_cooldown = self.max_teleport_cooldown
            for _ in range(20): particles.append(Particle(self.x, self.y - 50, PURPLE))
            self.x += 250 * self.direction # Teleport towards player
            for _ in range(20): particles.append(Particle(self.x, self.y - 50, PURPLE))
        
        # AI Special Move Logic
        if self.special_cooldown == 0 and player.is_alive and distance > 200 and distance < 500 and self.on_ground:
            self.is_attacking = True
            self.attack_type = "fireball"
            self.attack_frame = 10
            self.attack_cooldown = 20
            self.special_cooldown = self.max_special_cooldown # AI has same cooldown
            text_animations.append(TextAnimation("FIREBALL!", self.x + (50 * self.direction), self.y - 150, RED))
        
        # AI Melee Logic
        elif distance < 80 and self.on_ground:
            self.vel_x = 0
            # AI attack logic
            if self.attack_cooldown == 0 and player.is_alive:
                self.is_attacking = True
                self.attack_type = "punch" if random.random() < 0.7 else "kick"
                self.attack_frame = 15 if self.attack_type == "punch" else 20
                self.attack_cooldown = 50 # Slower attack rate for AI
        elif distance > 400 and distance < 600: # Stay in this "mid-range"
            self.vel_x = 0
        elif distance >= 600: # Only move if very far
            self.vel_x = 0
        

    def update(self):
        """Updates the stickman's state each frame."""
        global player, enemy # Add this line to access the global player/enemy
        
        # Handle stun
        if self.is_stunned > 0:
            self.is_stunned -= 1
            self.vel_x = 0
            self.is_attacking = False
            return
            
        # Handle hit stun
        if self.is_hit:
            self.hit_anim_timer -= 1
            self.vel_x = -2 * self.direction # Knockback
            if self.hit_anim_timer <= 0:
                self.is_hit = False
            return # Stop other logic
            
        # --- AURA BUFFS (Player only) ---
        if self.is_player:
            if self.has_ult_aura and self.ultimate_charge == self.max_ultimate_charge:
                self.damage = self.base_damage + 2
                self.speed = self.base_speed + 0.5
            else:
                self.damage = self.base_damage
                self.speed = self.base_speed
        
        # --- DASH UPDATE ---
        if self.dash_invulnerability > 0:
            self.dash_invulnerability -= 1

        if self.is_dashing:
            self.dash_duration -= 1
            self.vel_x = 25 * self.direction # Maintain dash speed
            self.vel_y = 0 # No gravity during dash
            if self.dash_duration % 2 == 0: # Leave a trail
                particles.append(Particle(self.x, self.y - 30, GRAY))
            if self.dash_duration <= 0:
                self.is_dashing = False
                self.vel_x = 0
        # --- END DASH UPDATE ---
        
        # --- ULTIMATE UPDATE ---
        if self.is_ulting:
            self.dash_invulnerability = 10 # Stay invulnerable
            
            if self.is_player:
                # --- Player Ult: Meteor Slam ---
                if self.ult_step == 1: # Paused in air
                    self.vel_x = 0
                    self.vel_y = 0
                    self.x = self.ult_target_x
                    self.y = 100
                    self.ult_timer -= 1
                    # Spawn charging particles
                    if self.ult_timer % 5 == 0:
                        particles.append(Particle(self.x + random.randint(-20, 20), self.y, YELLOW))
                    if self.ult_timer <= 0:
                        self.ult_step = 2
                elif self.ult_step == 2: # Slamming down
                    self.is_attacking = True
                    self.attack_type = "ultimate_pound"
                    self.attack_frame = 2 # Keep it active
                    self.vel_y = 40 # Rocket down
                    self.vel_x = 0
            
            else:
                # --- Enemy Ult: Shadow Barrage ---
                if self.ult_step == 1: # Teleporting
                    # Find player
                    enemy = [s for s in [player, enemy] if not s.is_player][0]
                    player = [s for s in [player, enemy] if s.is_player][0]
                    # Teleport behind player
                    self.x = player.x - (player.direction * 60)
                    self.y = player.y
                    self.direction = player.direction
                    self.vel_x = 0
                    self.vel_y = 0
                    self.ult_step = 2
                    self.ult_timer = 40 # Duration of the barrage
                    self.ult_hit_count = 5 # 5 hits
                
                elif self.ult_step == 2: # Barraging
                    self.vel_x = 0
                    self.vel_y = 0
                    self.ult_timer -= 1
                    # At specific frames, do an attack
                    if self.ult_timer % 8 == 0 and self.ult_hit_count > 0:
                        self.is_attacking = True
                        self.attack_type = "shadow_punch"
                        self.attack_frame = 5
                        self.ult_hit_count -= 1
                        # Create purple particles for shadow effect
                        for _ in range(5):
                            particles.append(Particle(self.x, self.y - 50, PURPLE))
                    
                    if self.ult_timer <= 0:
                        self.is_ulting = False
                        self.ult_step = 0
                        self.is_attacking = False
        # --- END ULTIMATE UPDATE ---
            
        # Handle dying animation first
        if self.is_dying:
            self.death_anim_timer -= 1
            # Keep applying gravity
            self.vel_y += self.gravity
            self.y += self.vel_y
            # Ground collision
            if self.y > GROUND_Y:
                self.y = GROUND_Y
                self.vel_y = 0
            
            if self.death_anim_timer <= 0:
                self.is_dying = False # Switch from "dying" to "dead"
            return # Don't do any other logic
            
        # If dead and not dying, do nothing
        if not self.is_alive:
            return
            
        # Update combo timer
        if self.combo_timer > 0:
            self.combo_timer -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
            
        # Apply gravity (only if not dashing or ulting)
        if not self.is_dashing and not self.is_ulting:
            self.vel_y += self.gravity
        
        # Don't apply gravity if ground pounding
        if self.is_attacking and self.attack_type == "ground_pound":
            self.vel_y = 25
        
        if not (self.is_ulting and (self.ult_step == 1 or (not self.is_player and self.ult_step == 2))): # Don't apply y vel if charging or shadow barraging
            self.y += self.vel_y
        
        # Apply horizontal movement
        # vel_x is set by move() or by is_dashing block
        if not (self.is_ulting): # Don't apply x vel if ulting
            self.x += self.vel_x
        
        # --- Platform Collision ---
        on_platform = False
        if self.vel_y > 0 and not self.is_dashing: # Only check if falling, not dashing
            stick_rect = pygame.Rect(self.x - self.width * 0.25, self.y - self.height, self.width * 0.5, self.height)
            
            for plat in platforms:
                if stick_rect.colliderect(plat):
                    # Check if the stickman's *bottom* from last frame was *above* the platform's *top*
                    last_stick_rect = pygame.Rect(self.x - self.vel_x - self.width * 0.25, self.y - self.vel_y - self.height, self.width * 0.5, self.height)
                    if last_stick_rect.bottom <= plat.top:
                        self.y = plat.top # Set feet to platform top
                        self.vel_y = 0
                        self.on_ground = True
                        on_platform = True
                        self.air_dash_count = self.max_air_dash # Reset air dash
                        break
        
        # Ground collision
        if not on_platform and self.y > GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0
            self.on_ground = True
            self.air_dash_count = self.max_air_dash # Reset air dash
            
        # Screen boundaries
        if self.x < self.width / 2:
            self.x = self.width / 2
        if self.x > SCREEN_WIDTH - self.width / 2:
            self.x = SCREEN_WIDTH - self.width / 2
            
        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Update special cooldown
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
            
        # Update attack animation
        self.attack_hitbox = None
        if self.is_attacking:
            self.attack_frame -= 1
            
            # Define attack hitbox
            if self.attack_type == "punch":
                hitbox_x = self.x + (self.width * 0.5 * self.direction)
                hitbox_y = self.y - self.height * 0.7
                self.attack_hitbox = pygame.Rect(hitbox_x, hitbox_y, self.width * 0.6, self.height * 0.2)
            elif self.attack_type == "kick":
                hitbox_x = self.x + (self.width * 0.3 * self.direction)
                hitbox_y = self.y - self.height * 0.2
                self.attack_hitbox = pygame.Rect(hitbox_x, hitbox_y, self.width * 0.7, self.height * 0.2)
            elif self.attack_type == "air_kick":
                self.vel_y = 15 # Keep moving down
                hitbox_y = self.y - self.height * 0.3
                self.attack_hitbox = pygame.Rect(self.x - self.width * 0.2, hitbox_y, self.width * 0.4, self.height * 0.3)
            elif self.attack_type == "ground_pound":
                self.vel_y = 25 # Keep moving down fast
                # Hitbox is a small area around the feet
                self.attack_hitbox = pygame.Rect(self.x - 30, self.y - 20, 60, 40)
            elif self.attack_type == "ultimate_pound":
                self.vel_y = 40 # Keep moving down fast
                # Hitbox is a LARGE area around the feet
                self.attack_hitbox = pygame.Rect(self.x - 80, self.y - 40, 160, 60)
            elif self.attack_type == "shadow_punch":
                hitbox_x = self.x + (self.width * 0.5 * self.direction)
                hitbox_y = self.y - self.height * 0.7
                self.attack_hitbox = pygame.Rect(hitbox_x, hitbox_y, self.width * 0.6, self.height * 0.2)
            # No hitbox for fireball, it creates a projectile
            
            # End attack
            if self.attack_frame <= 0 and not self.is_ulting: # Don't end ult attack prematurely
                self.is_attacking = False
                self.attack_hitbox = None
            
            # End air kick / ground pound / ult on landing
            if (self.attack_type == "air_kick" or self.attack_type == "ground_pound" or self.attack_type == "ultimate_pound") and self.on_ground:
                self.is_attacking = False
                self.attack_hitbox = None
                
                # Add a shockwave effect
                if self.attack_type == "ground_pound" or self.attack_type == "ultimate_pound":
                    pound_size = 15 if self.attack_type == "ground_pound" else 40
                    pound_text = "STOMP!" if self.attack_type == "ground_pound" else "METEOR!"
                    text_animations.append(TextAnimation(pound_text, self.x, self.y - 50, ORANGE))
                    
                    for _ in range(pound_size):
                        p = Particle(self.x, self.y, ORANGE)
                        p.vel_x = random.uniform(-5, 5)
                        p.vel_y = random.uniform(-3, 0) # Only go up/out
                        particles.append(p)
                
                # Reset ult state AFTER landing
                if self.attack_type == "ultimate_pound":
                    self.is_ulting = False
                    self.ult_step = 0
                
    def get_hitbox(self):
        """Returns the main body hitbox."""
        if not self.is_alive or self.is_dying or self.is_dashing or self.is_hit:
            return pygame.Rect(0, 0, 0, 0)
        return pygame.Rect(self.x - self.width * 0.25, self.y - self.height, self.width * 0.5, self.height)

    def take_damage(self, damage, attacker_x):
        """Reduces health when hit. Attacker_x is the x-coord of the attacker."""
        if (self.is_alive and not self.is_dying) and self.dash_invulnerability == 0:
            
            # Check for Block
            if self.is_blocking:
                # Check if the hit is from the front
                is_hit_from_front = (attacker_x < self.x and self.direction == -1) or \
                                    (attacker_x > self.x and self.direction == 1)
                
                if is_hit_from_front:
                    self.health -= damage * 0.2 # Blocked, take 20% damage
                    self.hit_duration = 5
                    text_animations.append(TextAnimation("Blocked", self.x, self.y - 150, GRAY))
                    # Spawn block sparks
                    for _ in range(3):
                        particles.append(Particle(self.x + 20 * self.direction, self.y - 50, WHITE))
                    return # Successfully blocked
                else:
                    # Hit from behind while blocking! Fall through to normal hit.
                    pass
                
            # Normal hit (or hit from behind)
            self.health -= damage
            self.hit_duration = 10 # Frames to flash red
            self.is_hit = True # Trigger hit animation
            self.hit_anim_timer = 15 # 0.25 seconds
            self.is_attacking = False # Cancel current attack
            text_animations.append(TextAnimation("Hit!", self.x, self.y - 150, RED)) # Added Hit text
            if self.health <= 0:
                self.health = 0
                self.is_alive = False
                self.is_dying = True
                self.death_anim_timer = 60 # 1 second animation
                self.vel_x = 0 # Stop moving
                # Added Dead text
                text_animations.append(TextAnimation("Dead", self.x, self.y - 150, RED, font=LEVEL_FONT, lifespan=60))

def draw_background(surface):
    """Draws the sky, stars, and ground."""
    global platforms
    surface.fill(SKY_COLOR)
    for x, y in stars:
        pygame.draw.rect(surface, WHITE, (x, y, 2, 2))
    # Draw all platforms
    for plat in platforms:
        pygame.draw.rect(surface, GRAY, plat)
    # Draw ground
    pygame.draw.rect(surface, GROUND_COLOR, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))

def draw_health_bars(player, enemy):
    """Draws health bars for both fighters."""
    
    # --- Helper Function for UI Pod ---
    def draw_player_pod(x, y, player_obj, is_enemy):
        # Container
        pod_width = 400
        pod_height = 130
        pod_rect = pygame.Rect(x, y, pod_width, pod_height)
        
        # Semi-transparent background
        s = pygame.Surface((pod_width, pod_height), pygame.SRCALPHA)
        s.fill((GRAY[0], GRAY[1], GRAY[2], 80))
        screen.blit(s, (x, y))
        pygame.draw.rect(screen, WHITE, pod_rect, 2) # Frame
        
        # --- Head Icon ---
        head_x = x + 35 if not is_enemy else x + pod_width - 35
        head_pos = (head_x, y + 40)
        pygame.draw.circle(screen, player_obj.color, head_pos, 20)
        # Skin
        if player_obj.is_player:
            pygame.draw.line(screen, WHITE, (head_pos[0] - 12, head_pos[1]), (head_pos[0] + 12, head_pos[1]), 5)
        else:
            pygame.draw.line(screen, BLACK, (head_pos[0] - 7, head_pos[1] + 2), (head_pos[0] - 2, head_pos[1] - 2), 3) # Left eye
            pygame.draw.line(screen, BLACK, (head_pos[0] + 2, head_pos[1] - 2), (head_pos[0] + 7, head_pos[1] + 2), 3) # Right eye

        # --- Health Bar ---
        bar_width = 300
        bar_height = 25
        bar_x = x + 80 if not is_enemy else x + 20
        bar_y = y + 20
        
        health_text = HEALTH_FONT.render(f"HP: {int(player_obj.health)}/{int(player_obj.max_health)}", True, WHITE)
        text_rect = health_text.get_rect(left = bar_x, centery = bar_y + bar_height/2) if not is_enemy \
                    else health_text.get_rect(right = bar_x + bar_width, centery = bar_y + bar_height/2)
        
        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height))
        
        health_fill = (player_obj.health / player_obj.max_health) * bar_width
        health_rect = pygame.Rect(bar_x, bar_y, health_fill, bar_height) if not is_enemy \
                      else pygame.Rect(bar_x + (bar_width - health_fill), bar_y, health_fill, bar_height)
        # Gradient Fill
        if health_fill > 0:
            health_color_top = GREEN
            health_color_bottom = (0, 150, 0)
            pygame.draw.rect(screen, health_color_top, (health_rect.left, health_rect.top, health_rect.width, health_rect.height/2))
            pygame.draw.rect(screen, health_color_bottom, (health_rect.left, health_rect.centery, health_rect.width, health_rect.height/2))
            
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        screen.blit(health_text, text_rect)

        # --- Special & Ult Bars ---
        sub_bar_width = 280
        sub_bar_height = 15
        sub_bar_x = x + 80 if not is_enemy else x + 40
        
        # Special Bar
        special_y = y + 70
        special_charge = (player_obj.max_special_cooldown - player_obj.special_cooldown) / player_obj.max_special_cooldown
        special_text = SPECIAL_FONT.render('SPECIAL', True, GRAY if special_charge < 1.0 else YELLOW)
        
        pygame.draw.rect(screen, BLACK, (sub_bar_x, special_y, sub_bar_width, sub_bar_height))
        special_fill = sub_bar_width * special_charge
        special_rect = pygame.Rect(sub_bar_x, special_y, special_fill, sub_bar_height) if not is_enemy \
                       else pygame.Rect(sub_bar_x + (sub_bar_width - special_fill), special_y, special_fill, sub_bar_height)
        pygame.draw.rect(screen, PURPLE, special_rect)
        pygame.draw.rect(screen, WHITE, (sub_bar_x, special_y, sub_bar_width, sub_bar_height), 1)
        
        text_rect_spec = special_text.get_rect(right=sub_bar_x - 10, centery=special_y + sub_bar_height/2) if not is_enemy \
                         else special_text.get_rect(left=sub_bar_x + sub_bar_width + 10, centery=special_y + sub_bar_height/2)
        screen.blit(special_text, text_rect_spec)
        
        # Ultimate Bar
        ult_y = y + 95
        ult_charge = player_obj.ultimate_charge / player_obj.max_ultimate_charge
        ult_text = SPECIAL_FONT.render('ULTIMATE', True, GRAY if ult_charge < 1.0 else ORANGE)
        
        pygame.draw.rect(screen, BLACK, (sub_bar_x, ult_y, sub_bar_width, sub_bar_height))
        ult_fill = sub_bar_width * ult_charge
        ult_rect = pygame.Rect(sub_bar_x, ult_y, ult_fill, sub_bar_height) if not is_enemy \
                   else pygame.Rect(sub_bar_x + (sub_bar_width - ult_fill), ult_y, ult_fill, sub_bar_height)
        pygame.draw.rect(screen, YELLOW, ult_rect)
        pygame.draw.rect(screen, WHITE, (sub_bar_x, ult_y, sub_bar_width, sub_bar_height), 1)
        
        text_rect_ult = ult_text.get_rect(right=sub_bar_x - 10, centery=ult_y + sub_bar_height/2) if not is_enemy \
                        else ult_text.get_rect(left=sub_bar_x + sub_bar_width + 10, centery=ult_y + sub_bar_height/2)
        screen.blit(ult_text, text_rect_ult)
        
    # Draw Player Pod (Left)
    draw_player_pod(15, 15, player, is_enemy=False)
    # Draw Enemy Pod (Right)
    draw_player_pod(SCREEN_WIDTH - 415, 15, enemy, is_enemy=True)


def draw_level_start(level):
    """Displays the current level number before the round starts."""
    screen.fill(GRAY)
    level_text = LEVEL_FONT.render(f'Level {level}', True, WHITE)
    text_rect = level_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(level_text, text_rect)
    pygame.display.flip()
    pygame.time.wait(1500) # Pause for 1.5 seconds

def draw_timer(time_left):
    """Draws the round timer at the top center."""
    # Simple frame for the timer
    timer_text = TIMER_FONT.render(f"{time_left}", True, WHITE)
    text_rect = timer_text.get_rect(center=(SCREEN_WIDTH / 2, 40))
    frame_rect = text_rect.inflate(20, 10)
    
    s = pygame.Surface(frame_rect.size, pygame.SRCALPHA)
    s.fill((GRAY[0], GRAY[1], GRAY[2], 80))
    screen.blit(s, frame_rect.topleft)
    pygame.draw.rect(screen, WHITE, frame_rect, 2)
    
    screen.blit(timer_text, text_rect)

def draw_game_over_screen(message):
    """Displays the game over message."""
    screen.fill(BLACK)
    
    # Determine color based on message
    color = GREEN
    if "Lose" in message:
        color = RED
    elif "Draw" in message:
        color = WHITE
    elif "Beat The Game" in message:
        color = YELLOW
        
    message_text = GAME_OVER_FONT.render(message, True, color)
    text_rect = message_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
    screen.blit(message_text, text_rect)
    
    restart_text = HEALTH_FONT.render("Press 'R' to Restart", True, WHITE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
    screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()

def draw_powerup_screen(selected_powerups, mouse_pos):
    """Draws the power-up selection screen."""
    screen.fill(BLACK)
    
    title_text = POWERUP_TITLE_FONT.render("Choose a Power-Up!", True, YELLOW)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, 100))
    screen.blit(title_text, title_rect)
    
    key_text = HEALTH_FONT.render("Press (1), (2), or (3) to choose", True, WHITE)
    key_rect = key_text.get_rect(center=(SCREEN_WIDTH / 2, 160))
    screen.blit(key_text, key_rect)
    
    # Draw the 3 options
    for i, powerup in enumerate(selected_powerups):
        box_width = 300
        box_height = 200
        x_pos = (SCREEN_WIDTH / 2) + (i - 1) * (box_width + 50) # Center the 3 boxes
        y_pos = SCREEN_HEIGHT / 2 - 50
        
        box_rect = pygame.Rect(x_pos - box_width/2, y_pos - box_height/2, box_width, box_height)
        
        # Hover effect
        if box_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, LIGHT_GRAY, box_rect, 5)
        else:
            pygame.draw.rect(screen, GRAY, box_rect, 5)
        
        # Key number
        key_num_text = LEVEL_FONT.render(f"({i+1})", True, WHITE)
        key_num_rect = key_num_text.get_rect(center=(box_rect.centerx, box_rect.top + 40))
        screen.blit(key_num_text, key_num_rect)
        
        # Power-up name
        name_text = SPECIAL_FONT.render(powerup['name'], True, GREEN)
        name_rect = name_text.get_rect(center=(box_rect.centerx, box_rect.centery - 20))
        screen.blit(name_text, name_rect)
        
        # Power-up description
        desc_text = POWERUP_DESC_FONT.render(powerup['desc'], True, WHITE)
        desc_rect = desc_text.get_rect(center=(box_rect.centerx, box_rect.centery + 30))
        screen.blit(desc_text, desc_rect)

def run_game(difficulty):
    """Main game loop."""
    global projectiles, particles, text_animations, platforms, player, enemy # Make player/enemy global for AI Ult

    # Player stats that persist between levels
    player_stats = {
        'max_health': 100,
        'damage': 10,
        'speed': 7,
        'special_cd': 180,
        'dash_cd': 60,
        'teleport_cd': 120,
        'crit_chance': 0.0,
        'fireball_damage': 30,
        'stomp_damage': 15,
        'ultimate_damage': 75,
        'ult_charge_rate': 0,
        'ultimate_charge': 0,
        'max_ultimate_charge': 100,
        'full_heal_next_level': False,
        'max_air_dash': 1,
        'has_ult_aura': False
    }
    
    current_level = 1
    game_state = 'START_LEVEL' # Possible states: START_LEVEL, PLAYING, POWERUP, GAME_OVER, GAME_WON
    
    player = None
    enemy = None
    selected_powerups = []
    
    round_start_time = 0
    time_remaining = 0
    
    game_over_timer = 0
    game_over_pending = ""
    
    mouse_pos = (0, 0) # For powerup screen hover

    # This loop handles level progression
    while True:
        
        # --- Event Handling (Global) ---
        mouse_pos = pygame.mouse.get_pos() # Get mouse pos every frame
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return # Exit the function entirely
            
            # State-specific event handling
            if game_state == 'GAME_OVER' or game_state == 'GAME_WON':
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # Exit the game loop and return to main menu
                    return
            
            elif game_state == 'POWERUP':
                if event.type == pygame.KEYDOWN:
                    chosen_index = -1
                    if event.key == pygame.K_1: chosen_index = 0
                    elif event.key == pygame.K_2: chosen_index = 1
                    elif event.key == pygame.K_3: chosen_index = 2
                    
                    if chosen_index != -1:
                        # Apply power-up
                        choice = selected_powerups[chosen_index]
                        effect = choice['effect']
                        value = choice['value']
                        
                        if effect == 'full_heal':
                            player_stats['full_heal_next_level'] = True
                        elif effect == 'ult_aura':
                            player_stats['has_ult_aura'] = True
                        else:
                            player_stats[effect] += value
                            # Ensure cooldowns don't go below a minimum
                            if 'cd' in effect and player_stats[effect] < 30:
                                player_stats[effect] = 30
                        
                        current_level += 1
                        game_state = 'START_LEVEL'
                
                # Allow clicking powerups
                if event.type == pygame.MOUSEBUTTONDOWN:
                    chosen_index = -1
                    for i in range(3):
                        box_width = 300
                        box_height = 200
                        x_pos = (SCREEN_WIDTH / 2) + (i - 1) * (box_width + 50)
                        y_pos = SCREEN_HEIGHT / 2 - 50
                        box_rect = pygame.Rect(x_pos - box_width/2, y_pos - box_height/2, box_width, box_height)
                        if box_rect.collidepoint(mouse_pos):
                            chosen_index = i
                            break
                    
                    if chosen_index != -1:
                        # Apply power-up (same as above)
                        choice = selected_powerups[chosen_index]
                        effect = choice['effect']
                        value = choice['value']
                        
                        if effect == 'full_heal':
                            player_stats['full_heal_next_level'] = True
                        elif effect == 'ult_aura':
                            player_stats['has_ult_aura'] = True
                        else:
                            player_stats[effect] += value
                            if 'cd' in effect and player_stats[effect] < 30:
                                player_stats[effect] = 30
                        
                        current_level += 1
                        game_state = 'START_LEVEL'

        # --- Game State Machine ---

        if game_state == 'START_LEVEL':
            # --- Setup Level ---
            draw_level_start(current_level)
            
            # Reset lists
            projectiles = []
            particles = []
            text_animations = []
            platforms = []
            
            # Create platforms
            platforms.append(pygame.Rect(SCREEN_WIDTH * 0.2 - 75, GROUND_Y - 120, 150, 30))
            platforms.append(pygame.Rect(SCREEN_WIDTH * 0.5 - 100, GROUND_Y - 200, 200, 30))
            platforms.append(pygame.Rect(SCREEN_WIDTH * 0.8 - 75, GROUND_Y - 120, 150, 30))
            
            # Create Player
            player = Stickman(200, GROUND_Y, BLUE, is_player=True)
            # Apply all stats from player_stats
            player.max_health = player_stats['max_health']
            if player_stats['full_heal_next_level']:
                player.health = player_stats['max_health']
                player_stats['full_heal_next_level'] = False # Consume buff
            else:
                player.health = player_stats['max_health'] # Heal to new max
            player.base_damage = player_stats['damage'] # Set base stats
            player.base_speed = player_stats['speed']
            player.damage = player_stats['damage']
            player.speed = player_stats['speed']
            player.max_special_cooldown = player_stats['special_cd']
            player.max_dash_cooldown = player_stats['dash_cd']
            player.max_teleport_cooldown = player_stats['teleport_cd']
            player.crit_chance = player_stats['crit_chance']
            player.fireball_damage = player_stats['fireball_damage']
            player.stomp_damage = player_stats['stomp_damage']
            player.ultimate_damage = player_stats['ultimate_damage']
            player.ult_charge_rate = player_stats['ult_charge_rate']
            player.ultimate_charge = player_stats['ultimate_charge'] # Carry over ult charge
            player.max_ultimate_charge = player_stats['max_ultimate_charge']
            player.max_air_dash = player_stats['max_air_dash']
            player.air_dash_count = player.max_air_dash
            player.has_ult_aura = player_stats['has_ult_aura']

            
            # Create Enemy
            level_stats = {
                1: (100, 1.0, 5), 2: (120, 1.0, 7), 3: (140, 1.1, 9),
                4: (160, 1.1, 11), 5: (200, 1.2, 13), 6: (220, 1.2, 15),
                7: (250, 1.3, 16), 8: (280, 1.3, 17), 9: (320, 1.4, 18),
                10: (400, 1.5, 20) # Boss level
            }
            stats = level_stats.get(current_level, level_stats[10]) # Get stats or default to max
            base_health, base_speed_mult, base_damage = stats
            
            # --- Apply Difficulty Modifiers ---
            if difficulty == "Easy":
                enemy_health = base_health * 0.75
                enemy_damage = base_damage * 0.8
                enemy_speed = base_speed_mult * 0.9
            elif difficulty == "Hard":
                enemy_health = base_health * 1.3
                enemy_damage = base_damage * 1.25
                enemy_speed = base_speed_mult * 1.15
            else: # Medium
                enemy_health = base_health
                enemy_damage = base_damage
                enemy_speed = base_speed_mult
            
            enemy = Stickman(SCREEN_WIDTH - 200, GROUND_Y, RED, is_player=False)
            enemy.max_health = enemy_health
            enemy.health = enemy_health
            enemy.speed_multiplier = enemy_speed
            enemy.base_damage = enemy_damage # Set base stats
            enemy.base_speed = 7
            enemy.damage = enemy_damage
            enemy.speed = 7
            enemy.stomp_damage = 10 * (enemy_damage / 5) # Scale stomp too
            
            # --- Apply Enemy Powerups (Hard Mode) ---
            if difficulty == "Hard" and current_level > 1 and (current_level - 1) % 3 == 0:
                choice = random.choice(ai_powerups)
                effect = choice['effect']
                value = choice['value']
                
                if effect == 'max_health':
                    enemy.max_health += value
                    enemy.health = enemy.max_health
                elif effect == 'damage':
                    enemy.damage += value
                elif effect == 'speed':
                    enemy.speed_multiplier += 0.1 # AI speed is a multiplier
                elif effect == 'special_cd':
                    enemy.max_special_cooldown = max(30, enemy.max_special_cooldown + value)
                elif effect == 'dash_cd':
                    enemy.max_dash_cooldown = max(30, enemy.max_dash_cooldown + value)
                elif effect == 'teleport_cd':
                    enemy.max_teleport_cooldown = max(30, enemy.max_teleport_cooldown + value)
                # Other powerups are fine to add
                
                text_animations.append(TextAnimation(f"Enemy {choice['name']}!", enemy.x, enemy.y - 150, RED, font=LEVEL_FONT, lifespan=60))


            # Reset timers
            round_start_time = pygame.time.get_ticks()
            time_remaining = GAME_DURATION_SECONDS
            game_over_timer = 0
            game_over_pending = ""
            
            game_state = 'PLAYING'
            
        elif game_state == 'PLAYING':
            clock.tick(FPS)
            # --- Main Update Loop ---
            
            # --- Timer Update ---
            elapsed_time = (pygame.time.get_ticks() - round_start_time) // 1000
            time_remaining = max(0, GAME_DURATION_SECONDS - elapsed_time)
            
            # --- Get Key Presses ---
            keys = pygame.key.get_pressed()
            
            # --- Update ---
            if game_over_timer == 0:
                player.move(keys)
                player.attack(keys, enemy.x) # Pass enemy_x for ult
            
            player.update()
            
            if game_over_timer == 0:
                enemy.update_ai(player)
            
            enemy.update()
            
            # --- Handle Projectile Spawning ---
            if game_over_timer == 0:
                if player.is_attacking and player.attack_type == "fireball" and player.attack_frame == 5:
                    projectiles.append(Projectile(player.x, player.y - player.height * 0.7, player.direction, PURPLE, player.fireball_damage, True))
                
                if enemy.is_attacking and enemy.attack_type == "fireball" and enemy.attack_frame == 5:
                    projectiles.append(Projectile(enemy.x, enemy.y - enemy.height * 0.7, enemy.direction, RED, enemy.fireball_damage, False))

            # --- Update Effects ---
            for p in projectiles[:]:
                p.update()
                if not (0 < p.x < SCREEN_WIDTH):
                    if p in projectiles:
                        projectiles.remove(p)
            
            for p in particles[:]:
                p.update()
                if p.lifespan <= 0:
                    if p in particles:
                        particles.remove(p)
            
            for ta in text_animations[:]:
                ta.update()
                if ta.lifespan <= 0:
                    if ta in text_animations:
                        text_animations.remove(ta)

            # --- Check Collisions ---
            if game_over_timer == 0:
                player_hitbox = player.get_hitbox()
                enemy_hitbox = enemy.get_hitbox()

                # Player melee attacks enemy
                if player.attack_hitbox and enemy_hitbox.colliderect(player.attack_hitbox):
                    # Check for crit
                    is_crit = random.random() < player.crit_chance
                    crit_bonus_ult = 5 if is_crit else 0
                    
                    # Check for attack type
                    if player.attack_type == "punch" or player.attack_type == "kick":
                        dmg = player.damage * 2 if is_crit else player.damage
                        enemy.take_damage(dmg, player.x)
                        player.ultimate_charge += (10 + player.ult_charge_rate + crit_bonus_ult)
                        if is_crit:
                            text_animations.append(TextAnimation("CRIT!", player.attack_hitbox.centerx, player.attack_hitbox.centery, YELLOW, font=LEVEL_FONT, lifespan=30))
                    
                    elif player.attack_type == "air_kick" or player.attack_type == "ground_pound":
                        dmg = player.stomp_damage * 2 if is_crit else player.stomp_damage
                        enemy.take_damage(dmg, player.x)
                        player.ultimate_charge += (15 + player.ult_charge_rate + crit_bonus_ult)
                        if is_crit:
                            text_animations.append(TextAnimation("CRIT!", player.attack_hitbox.centerx, player.attack_hitbox.centery, YELLOW, font=LEVEL_FONT, lifespan=30))
                    
                    elif player.attack_type == "ultimate_pound":
                        enemy.take_damage(player.ultimate_damage, player.x) # Ult damage
                        player.ultimate_charge += 20 # Bonus for landing
                        # Knockback (Increased)
                        enemy.is_hit = True
                        enemy.hit_anim_timer = 45
                        enemy.vel_y = -25
                        enemy.vel_x = 25 * -player.direction
                    
                    for _ in range(5):
                        particles.append(Particle(player.attack_hitbox.centerx, player.attack_hitbox.centery, YELLOW))
                    player.attack_hitbox = None 
                    
                # Enemy melee attacks player
                if enemy.attack_hitbox and player_hitbox.colliderect(enemy.attack_hitbox):
                    dmg = enemy.damage
                    if enemy.attack_type == "air_kick" or enemy.attack_type == "ground_pound":
                        dmg = enemy.stomp_damage
                    elif enemy.attack_type == "shadow_punch":
                        dmg = enemy.damage * 0.75 # Ult hits are fast but weaker
                    
                    player.take_damage(dmg, enemy.x)
                    enemy.ultimate_charge = min(enemy.ultimate_charge + 15, enemy.max_ultimate_charge)
                    
                    for _ in range(5):
                        particles.append(Particle(enemy.attack_hitbox.centerx, enemy.attack_hitbox.centery, YELLOW))
                    enemy.attack_hitbox = None
                
                # --- Projectile Collisions ---
                
                # Projectile vs Projectile (Clash)
                for p1 in projectiles[:]:
                    for p2 in projectiles[:]:
                        if p1 == p2:
                            continue
                        if p1.is_player_projectile != p2.is_player_projectile:
                            if p1.get_hitbox().colliderect(p2.get_hitbox()):
                                # CLASH
                                for _ in range(15):
                                    particles.append(Particle(p1.x, p1.y, ORANGE))
                                text_animations.append(TextAnimation("CLASH!", p1.x, p1.y, WHITE, lifespan=20))
                                if p1 in projectiles:
                                    projectiles.remove(p1)
                                if p2 in projectiles:
                                    projectiles.remove(p2)
                                break # Move to next p1
                
                # Projectile vs Stickman
                for p in projectiles[:]:
                    proj_hitbox = p.get_hitbox()
                    if p.is_player_projectile and enemy_hitbox.colliderect(proj_hitbox): # Player's fireball
                        enemy.take_damage(p.damage, p.x)
                        player.ultimate_charge += (15 + player.ult_charge_rate)
                        for _ in range(10): particles.append(Particle(p.x, p.y, p.color))
                        if p in projectiles: projectiles.remove(p)
                    elif not p.is_player_projectile and player_hitbox.colliderect(proj_hitbox): # Enemy's fireball
                        player.take_damage(p.damage, p.x)
                        enemy.ultimate_charge = min(enemy.ultimate_charge + 15, enemy.max_ultimate_charge)
                        for _ in range(10): particles.append(Particle(p.x, p.y, p.color))
                        if p in projectiles: projectiles.remove(p)
                
                # Cap ultimate charge
                player.ultimate_charge = min(player.ultimate_charge, player.max_ultimate_charge)
                enemy.ultimate_charge = min(enemy.ultimate_charge, enemy.max_ultimate_charge)

            # --- Check for Game Over Conditions ---
            if game_over_timer == 0:
                if not player.is_alive:
                    game_over_timer = 60 # 1 second death animation
                    game_over_pending = "You Lose!"
                elif not enemy.is_alive:
                    game_over_timer = 60 # 1 second death animation
                    game_over_pending = "You Win!"
                elif time_remaining == 0:
                    game_over_timer = 1 # 1 frame delay to show message
                    if player.health > enemy.health:
                        game_over_pending = "You Win!"
                    elif enemy.health > player.health:
                        game_over_pending = "You Lose!"
                    else:
                        game_over_pending = "Draw!"
        
            # --- Handle Game Over Animation Timer ---
            if game_over_timer > 0:
                game_over_timer -= 1
                if game_over_timer == 0:
                    # Transition to the correct end state
                    if game_over_pending == "You Win!":
                        # Save ult charge for next level
                        player_stats['ultimate_charge'] = player.ultimate_charge
                        if current_level == MAX_LEVEL:
                            game_state = 'GAME_WON'
                        else:
                            # Get 3 unique powerups
                            selected_powerups = []
                            available_powerups = all_powerups[:]
                            while len(selected_powerups) < 3 and available_powerups:
                                choice = random.choice(available_powerups)
                                selected_powerups.append(choice)
                                available_powerups.remove(choice)
                                
                            game_state = 'POWERUP'
                    elif game_over_pending == "You Lose!" or game_over_pending == "Draw!":
                        game_state = 'GAME_OVER'

            # --- Drawing ---
            draw_background(screen)
            if player: player.draw(screen)
            if enemy: enemy.draw(screen)
            for p in projectiles: p.draw(screen)
            for p in particles: p.draw(screen)
            for ta in text_animations: ta.draw(screen)
            if player and enemy: draw_health_bars(player, enemy)
            draw_timer(time_remaining)
            pygame.display.flip()

        elif game_state == 'POWERUP':
            draw_powerup_screen(selected_powerups, mouse_pos)
            pygame.display.flip()
            
        elif game_state == 'GAME_OVER':
            draw_game_over_screen("You Lose!")
            pygame.display.flip()
            
        elif game_state == 'GAME_WON':
            draw_game_over_screen("You Beat The Game!")
            pygame.display.flip()

def draw_main_menu(start_button, mouse_pos):
    """Draws the main title screen and start button."""
    screen.fill(SKY_COLOR)
    title_text = GAME_OVER_FONT.render("Stickman Fighter", True, YELLOW)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 150))
    screen.blit(title_text, title_rect)
    
    # Draw Start Button
    button_color = GREEN
    if start_button.collidepoint(mouse_pos):
        button_color = LIGHT_GREEN # Hover effect
        
    pygame.draw.rect(screen, button_color, start_button, border_radius=10)
    pygame.draw.rect(screen, WHITE, start_button, 4, border_radius=10) # Border
    start_text = LEVEL_FONT.render("START", True, BLACK)
    start_rect = start_text.get_rect(center=start_button.center)
    screen.blit(start_text, start_rect)

def draw_difficulty_select(easy_rect, medium_rect, hard_rect, mouse_pos):
    """Draws the difficulty selection screen."""
    screen.fill(SKY_COLOR)
    title_text = POWERUP_TITLE_FONT.render("Choose Difficulty", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, 150))
    screen.blit(title_text, title_rect)
    
    # Easy
    easy_color = GREEN
    if easy_rect.collidepoint(mouse_pos):
        easy_color = LIGHT_GREEN
    pygame.draw.rect(screen, easy_color, easy_rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, easy_rect, 4, border_radius=10)
    easy_text = LEVEL_FONT.render("Easy", True, BLACK)
    screen.blit(easy_text, easy_text.get_rect(center=easy_rect.center))
    
    # Medium
    medium_color = ORANGE
    if medium_rect.collidepoint(mouse_pos):
        medium_color = LIGHT_ORANGE
    pygame.draw.rect(screen, medium_color, medium_rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, medium_rect, 4, border_radius=10)
    medium_text = LEVEL_FONT.render("Medium", True, BLACK)
    screen.blit(medium_text, medium_text.get_rect(center=medium_rect.center))
    
    # Hard
    hard_color = RED
    if hard_rect.collidepoint(mouse_pos):
        hard_color = LIGHT_RED
    pygame.draw.rect(screen, hard_color, hard_rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, hard_rect, 4, border_radius=10)
    hard_text = LEVEL_FONT.render("Hard", True, BLACK)
    screen.blit(hard_text, hard_text.get_rect(center=hard_rect.center))

def main():
    """Main application loop."""
    app_state = 'MAIN_MENU' # MAIN_MENU, DIFFICULTY_SELECT
    
    # --- Button Rects for Menus (Adjusted for 1600x900) ---
    start_button_rect = pygame.Rect(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 - 40, 300, 80)
    
    easy_button_rect = pygame.Rect(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 - 100, 300, 80)
    medium_button_rect = pygame.Rect(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 + 10, 300, 80)
    hard_button_rect = pygame.Rect(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 + 120, 300, 80)

    while True:
        clock.tick(FPS)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # --- Event Handling (Menus) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    if app_state == 'MAIN_MENU':
                        if start_button_rect.collidepoint(mouse_pos):
                            app_state = 'DIFFICULTY_SELECT'
                            
                    elif app_state == 'DIFFICULTY_SELECT':
                        difficulty = None
                        if easy_button_rect.collidepoint(mouse_pos):
                            difficulty = "Easy"
                        elif medium_button_rect.collidepoint(mouse_pos):
                            difficulty = "Medium"
                        elif hard_button_rect.collidepoint(mouse_pos):
                            difficulty = "Hard"
                            
                        if difficulty:
                            # Start the game. run_game will loop until game over.
                            run_game(difficulty)
                            # When game is over, return to main menu
                            app_state = 'MAIN_MENU'

        # --- Drawing (Menus) ---
        screen.fill(SKY_COLOR)
        if app_state == 'MAIN_MENU':
            draw_main_menu(start_button_rect, mouse_pos)
        elif app_state == 'DIFFICULTY_SELECT':
            draw_difficulty_select(easy_button_rect, medium_button_rect, hard_button_rect, mouse_pos)
        
        pygame.display.flip()

if __name__ == "__main__":
    main()