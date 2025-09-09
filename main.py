# Complete your game here

import pygame
import random

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

### --- GRAPHICS --- ###
class Graphics:
    def __init__(self, img_path=None, scale=1.0):
        self.img = pygame.image.load(img_path) if img_path else None
        self.scale = scale

    def get_width(self):
        if self.img:
            return int(self.img.get_width() * self.scale)
    
    def get_height(self):
        if self.img:
            return int(self.img.get_height() * self.scale)
    
    def get_radius(self):
        if self.img:
            return self.get_width() // 2
    
    def draw(self, surface, pos, angle=0):
        if self.img:
            sprite = pygame.transform.rotozoom(self.img, -angle, self.scale)
            rect = sprite.get_rect(center=(pos.x, pos.y))
            surface.blit(sprite, rect.topleft)

### --- PHYSICS --- ###
class Physics:
    def __init__(self, pos, vel=None, acc=None, mass=1, facing=0, spin_speed=0):
        self.pos = pygame.math.Vector2(pos)
        if isinstance(vel, pygame.math.Vector2):
            self.vel = vel
        elif isinstance(vel, (tuple, list)):
            self.vel = pygame.math.Vector2(vel)
        elif isinstance(vel, (int, float)):
            self.vel = pygame.math.Vector2(vel, 0)
        elif vel is None:
            self.vel = pygame.math.Vector2()
        else:
            raise TypeError(f"Invalid type for vel: {type(vel)}")
        self.acc = pygame.math.Vector2(acc) if acc else pygame.math.Vector2()
        self.mass = mass
        self.facing = facing
        self.spin_speed = spin_speed
        self.spin = 0

    def move(self):
        self.vel += self.acc
        self.pos += self.vel
        self.spin = (self.spin + self.facing) % 360

    def handle_collision(self, other: "Physics"):
        if self.mass == 0 or other.mass == 0:
            return

        dir = self.pos - other.pos
        if dir.length() == 0:
            dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        dir = dir.normalize()

        rel_vel = self.vel - other.vel
        vel_along_normal = rel_vel.dot(dir)

        # Only bounce if moving towards each other
        if vel_along_normal > 0:
            return

        # Elastic collision formula (simplified, with "softness" factor)
        softness = 0.5  # Lower = softer bounce
        m1, m2 = self.mass, other.mass
        impulse = (-(1 + softness) * vel_along_normal) / (1/m1 + 1/m2)

        self.vel += (impulse / m1) * dir
        other.vel -= (impulse / m2) * dir

    def collides_with(self, other: "Physics", radius_self, radius_other):
        return self.pos.distance_to(other.pos) < radius_self + radius_other
    
    def wrap_position(self, radius):
        w = WINDOW_WIDTH
        h = WINDOW_HEIGHT
        if self.pos.x < -radius:
            self.pos.x = w + radius
        elif self.pos.x > w + radius:
            self.pos.x = -radius
        if self.pos.y < -radius:
            self.pos.y = h + radius
        elif self.pos.y > h + radius:
            self.pos.y = -radius

### --- HEALTH --- ###
class Health:
    def __init__(self, max_hp, is_visible):
        self.max_hp = max_hp
        self.hp = max_hp
        self.is_visible = is_visible

    def __str__(self):
        return f"{self.hp:>3.0f} / {self.max_hp:<3.0f}"
    
    def __repr__(self):
        return f"max hp: {self.max_hp}\ncurrent hp: {self.hp}\nis health bar visible: {self.is_visible}"

    def draw_bar(self, surface, object: "GameObject"):
        bar_width = self.max_hp
        bar_height = 6

        x = int(object.phys.pos.x - bar_width // 2)
        y = int(object.phys.pos.y - object.get_radius() - 16)

        hp_ratio = max(0, min(1, self.hp / self.max_hp))
        fill_width = int(bar_width * hp_ratio)

        pygame.draw.rect(surface, (60,60,60), (x, y, bar_width, bar_height))
        pygame.draw.rect(surface, (0,220,0), (x, y, fill_width, bar_height))
        pygame.draw.rect(surface, (0,0,0), (x, y, bar_width, bar_height), 1)

### --- GAMEOBJECT --- ###
class GameObject:
    def __init__(self, pos, vel, mass, img_path, scale=1.0, facing=0, spin_speed=0, max_hp=100, hp_visible=False):
        self.phys = Physics(pos, vel, mass=mass, facing=facing, spin_speed=spin_speed)
        self.graphics = Graphics(img_path, scale)
        self.health = Health(max_hp, hp_visible)

    def update(self):
        self.phys.move()
        if self.graphics.img:
            self.phys.wrap_position(self.graphics.get_radius())

    def draw(self, surface):
        self.graphics.draw(surface, self.phys.pos, self.phys.facing)
        if self.health.is_visible:
            self.health.draw_bar(surface, self)

    def get_radius(self):
        return self.graphics.get_radius()
    
    def collides_with(self, other: "GameObject"):
        return self.phys.collides_with(other.phys, self.get_radius(), other.get_radius())

    def take_damage(self, amount):
        self.health.hp -= amount
        if self.health.hp < 0:
            self.health.hp = 0

    def is_dead(self):
        return self.health.hp <= 0

### --- ROCK / ASTEROID --- ###
class Rock(GameObject):
    def __init__(self, pos):
        angle = random.uniform(0, 360)
        speed = random.uniform(1, 2.5)
        dir = pygame.Vector2(1, 0).rotate(angle) * speed
        mass = random.uniform(0.5, 1.5)
        spin_speed = random.uniform(-2, 2)
        super().__init__(pos, vel=dir, mass=mass, img_path="door.png", scale=mass, facing=angle, spin_speed=spin_speed)
        self.health.max_hp = mass*50
        self.health.hp = mass*50

        self.is_breaking = False
        self.break_timer = 0
        self.break_duration = 20

    def update(self):
        if self.is_breaking:
            self.break_timer += 1
            self.graphics.scale *= 0.9
        else:
            super().update()
            self.phys.facing = (self.phys.facing + self.phys.spin_speed) % 360

    def draw(self, surface):
        if self.is_breaking:
            self.graphics.draw(surface, self.phys.pos, self.phys.facing)
        else:
            super().draw(surface)

    def is_dead(self):
        return self.is_breaking and self.break_timer >= self.break_duration
    
    def start_breaking(self):
        self.is_breaking = True
        self.break_timer = 0

    @classmethod
    def spawn_random(cls, rocks: list):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            pos = (random.randint(0, 1280), -40)
        elif edge == 'bottom':
            pos = (random.randint(0, 1280), 760)
        elif edge == 'left':
            pos = (-40, random.randint(0, 720))
        else:
            pos = (1320, random.randint(0, 720))
        rocks.append(cls(pos))

### --- DEBRIS --- ###
class Debris(GameObject):
    def __init__(self, pos, colour=(180,180,180)):
        angle = random.uniform(0,360)
        speed = random.uniform(2,6)
        vel = pygame.Vector2(1,0).rotate(angle) * speed
        super().__init__(pos, vel=vel, mass=0.01, img_path=None, scale=1.0)
        self.lifetime = random.randint(15,30)
        self.age = 0
        self.colour = colour
        self.radius = random.randint(2,6)

    def update(self):
        super().update()
        self.age+=1

    def draw(self,surface):
        alpha = max(0, 255 - int(255 * (self.age / self.lifetime)))
        debris_colour = (*self.colour, alpha)
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, debris_colour, (self.radius, self.radius), self.radius)
        surface.blit(s, (self.phys.pos.x - self.radius, self.phys.pos.y - self.radius))

    def is_expired(self):
        return self.age >= self.lifetime
    
    def get_radius(self):
        return self.radius

### --- LASER --- ###
class Laser(GameObject):
    def __init__(self, pos, angle):
        dir = pygame.Vector2(1, 0).rotate(angle)
        super().__init__(pos, vel=dir * 20, mass=0.005, img_path=None, scale=1.0, facing=angle)
        self.dir = dir
        self.range = 200
        self.distance_travelled = 0
        self.damage = 20

    def update(self):
        super().update()
        self.distance_travelled += self.phys.vel.length()

    def draw(self, surface):
        pygame.draw.line(surface, (255,0,0), self.phys.pos, self.phys.pos + self.dir * 20, 5)

    def is_expired(self):
        return self.distance_travelled >= self.range

    def is_dead(self):
        return super().is_dead() or self.is_expired()
    
    def get_radius(self):
        return 5

### --- PLAYER --- ###
class Player(GameObject):
    def __init__(self):
        super().__init__((640,360), vel=(0,0), mass=2, img_path="robot.png", scale=1.0, facing=-90)
        self.health.is_visible = True
        self.max_speed = 5
        self.thrust = 0.18
        self.turn_vel = 0
        self.turn_friction = 0.85
        self.max_turn_speed = 6

    def update(self):
        # every frame, check which keys are pressed
        keys = pygame.key.get_pressed()

        # turning logic
        TURN_ACC = 0.6
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.turn_vel -= TURN_ACC
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.turn_vel += TURN_ACC

        self.turn_vel *= self.turn_friction

        if abs(self.turn_vel) > self.max_turn_speed:
            self.turn_vel = self.max_turn_speed * (1 if self.turn_vel > 0 else -1)

        self.phys.facing += self.turn_vel

        # thrust logic - forward, backward, and strafing side-to-side dependent on the facing direction
        dir = pygame.Vector2(1, 0).rotate(self.phys.facing)
        side = dir.rotate(90)
        self.phys.acc = pygame.Vector2(0, 0)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.phys.acc += dir * self.thrust        
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.phys.acc -= dir * self.thrust
        if keys[pygame.K_q]:
            self.phys.acc -= side * self.thrust
        if keys[pygame.K_e]:
            self.phys.acc += side * self.thrust

        super().update()

        # clamp position to window
        self.phys.pos.x = max(0, min(1280, self.phys.pos.x))
        self.phys.pos.y = max(0, min(720, self.phys.pos.y))

        friction = 0.99
        self.phys.vel *= friction

        if self.phys.vel.length() > self.max_speed:
            self.phys.vel.scale_to_length(self.max_speed)

### --- SCRAP --- ###
class Scrap(GameObject):
    def __init__(self, pos, vel, point_value=1, timer=10):
        super().__init__(pos, vel, mass=0.1, img_path="coin.png")
        self.point_value = point_value
        self.timer = timer
        self.age = 0

        self.health.is_visible = False

    def update(self):
        super().update()
        friction = 0.98
        if self.phys.vel.length() > 0.1:
            self.phys.vel *= friction
        else:
            self.phys.vel = pygame.math.Vector2(0,0)
        
        self.age += 1

    def is_expired(self):
        return self.age >= self.timer * 60
    
    def get_radius(self):
        return 12 # <<< placeholder value

### --- ENEMY --- ###
class Enemy(GameObject):
    def __init__(self, pos):
        super().__init__(pos)
        

### --- COLLISION HANDLER --- ###
class CollisionHandler:
    def __init__(self, game_ctrl: "GameCtrl"):
        self.game = game_ctrl
    
    # combined collision handling method
    def handle(self, a: GameObject, b: GameObject, to_remove: set):
        if self.laser_player_ignore(a, b):
            return
        if self.scrap_player(a, b):
            return
        if self.laser_other(a, b, to_remove):
            return
        
        self.default_collision(a, b)

    # laser + player = ignore collision
    def laser_player_ignore(self, a, b):
        if (isinstance(a, Laser) and isinstance(b, Player)) or \
           (isinstance(b, Laser) and isinstance(a, Player)):
            return True
        return False
    
    # scrap + player = remove scrap, increment points
    def scrap_player(self, a, b):
        if isinstance(a, Scrap) and isinstance(b, Player):
            self.game.points += getattr(a, "point_value", 1)
            a.timer = 0
            return True
        if isinstance(b, Scrap) and isinstance(a, Player):
            self.game.points += getattr(b, "point_value", 1)
            b.timer = 0
            return True
        return False
    
    # laser + other = deal laser damage
    def laser_other(self, a, b, to_remove):
        if isinstance(a, Laser) and not isinstance(b, (Laser, Player)):
            b.take_damage(a.damage)
            to_remove.add(a)
            return True
        if isinstance(b, Laser) and not isinstance(a, (Laser, Player)):
            a.take_damage(b.damage)
            to_remove.add(b)
            return True
        return False

    # default collision
    def default_collision(self, a, b):
        a.phys.handle_collision(b.phys)
        b.phys.handle_collision(a.phys)

        rel_vel = (a.phys.vel - b.phys.vel).length()
        if a.phys.mass > 0.1 and b.phys.mass > 0.1 and rel_vel > 0:
            dmg_mltplr = 2.0    # damage multiplier
            dmg1 = rel_vel * (b.phys.mass / a.phys.mass) * dmg_mltplr
            dmg2 = rel_vel * (a.phys.mass / b.phys.mass) * dmg_mltplr
            a.take_damage(dmg1)
            b.take_damage(dmg2)

### --- GAME CONTROL --- ###
class GameCtrl:
    def __init__(self):
        pygame.init()
        self.game_font = pygame.font.SysFont("Lucida Sans", 24)
        self.clock = pygame.time.Clock()
        self.background = pygame.image.load("background.png")
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.collision = CollisionHandler(self)

        self.points = 0
        self.player = Player()
        self.lasers = []
        self.rocks = []
        self.debris = []
        self.scrap = []
        self.enemies = []
        
        self.spawn_timer = 0

        self.main_loop()

    def main_loop(self):
        while True:
            self.check_events()
            self.update()
            self.draw_window()
            self.clock.tick(60)

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Shoot laser from player's position and angle
                    self.lasers.append(Laser(self.player.phys.pos, self.player.phys.facing))

    def update(self):
        self.player.update()
        self.update_lasers()
        self.update_rocks()
        self.update_debris()
        self.update_scrap()
        self.check_collisions()
        
    def update_lasers(self):
        for laser in self.lasers:
            laser.update()
        self.lasers = [l for l in self.lasers if not l.is_expired()]

    def update_rocks(self):
        for rock in self.rocks:
            if rock.health.hp <= 0 and not rock.is_breaking:
                rock.start_breaking()
                for _ in range(random.randint(8,16)):
                    self.debris.append(Debris(rock.phys.pos))
                if random.random() < 0.5:
                    value = random.randint(1,10)
                    self.scrap.append(Scrap(rock.phys.pos, rock.phys.vel, value))
            rock.update()
        self.rocks = [r for r in self.rocks if not r.is_dead()]
        self.spawner()

    def update_debris(self):
        for d in self.debris:
            d.update()
        self.debris = [d for d in self.debris if not d.is_expired()]

    def update_scrap(self):
        for s in self.scrap:
            s.update()
        self.scrap = [s for s in self.scrap if not s.is_expired()]

    def spawner(self):
        self.spawn_timer += 1
        if self.spawn_timer > 120 and len(self.rocks) <= 10:
            self.spawn_timer = 0
            Rock.spawn_random(self.rocks)

    def check_collisions(self):
        to_remove = set()
        all_objects = [self.player] + self.rocks + self.lasers + self.scrap + self.enemies
        for i, obj1 in enumerate(all_objects):
            for obj2 in all_objects[i+1:]:
                if obj1.get_radius() and obj2.get_radius():
                    if obj1.collides_with(obj2):
                        self.collision.handle(obj1, obj2, to_remove)
        
        # remove marked lasers
        self.lasers = [l for l in self.lasers if l not in to_remove]

    def draw_window(self):
        # parallax the background based on player position
        parallax_factor = 0.2
        bg_width, bg_height = self.background.get_width(), self.background.get_height()
        offset_x = int(self.player.phys.pos.x * parallax_factor)
        offset_y = int(self.player.phys.pos.y * parallax_factor)
        max_x = bg_width - WINDOW_WIDTH
        max_y = bg_height - WINDOW_HEIGHT
        offset_x = max(0, min(offset_x, max_x))
        offset_y = max(0, min(offset_y, max_y))
        self.window.blit(self.background, (-offset_x, -offset_y))

        # draw all existing game objects - keeping the layer order sensible (e.g. scrap below rocks)
        for laser in self.lasers:
            laser.draw(self.window)
        self.player.draw(self.window)
        for scrap in self.scrap:
            scrap.draw(self.window)
        for debr in self.debris:
            debr.draw(self.window)
        for rock in self.rocks:
            rock.draw(self.window)

        self.draw_text()

        pygame.display.flip()

    # draw all in-game text
    def draw_text(self):
        # points display
        points_text = self.game_font.render(f"Points: {self.points}", True, (255,255,255))
        self.window.blit(points_text, (16,16))

        # player hp
        hp_text = self.game_font.render(f"{self.player.health}", True, (255,255,255))
        hp_x = WINDOW_WIDTH // 2 - hp_text.get_width() // 2
        hp_y = WINDOW_HEIGHT - hp_text.get_height() - 30
        self.window.blit(hp_text, (hp_x, hp_y))

if __name__ == "__main__":
    GameCtrl()