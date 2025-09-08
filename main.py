# Complete your game here

import pygame
import random

# --- Below is the GameObject class from which other classes will
# --- inherit things like movement and collision logic, health, etc.

class Physics:
    def __init__(self, pos, vel=None, acc=None, facing=0, mass=1, spin_speed=0):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel) if vel else pygame.math.Vector2()
        self.acc = pygame.math.Vector2(acc) if acc else pygame.math.Vector2()
        self.facing = facing
        self.mass = mass
        self.spin_speed = spin_speed
        self.spin = 0

    def move(self):
        self.vel += self.acc
        self.pos += self.vel
        self.physics.current_rotation = (self.physics.current_rotation + self.physics.rotation) % 360

class GameObject:
    def __init__(self, pos, vel=None, acc=None, angle=0, mass=1, rotation=0, sprite=None):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel) if vel else pygame.math.Vector2()
        self.acc = pygame.math.Vector2(acc) if acc else pygame.math.Vector2()
        self.angle = angle
        self.mass = mass
        self.rotation = rotation
        self.current_rotation = 0
        self.cycles = 0
        self.wrap = True
        self.sprite = sprite

    def update(self):
        self.vel += self.acc
        self.pos += self.vel

    def draw(self, surface):
        if self.sprite:
            rotated = pygame.transform.rotate(self.sprite, -self.angle)
            rect = rotated.get_rect(center=(self.pos.x, self.pos.y))
            surface.blit(rotated, rect.topleft)

    def wrap_position(self, surface):


    def get_radius(self):
        if self.sprite:
            return self.sprite.get_width() // 2
        return 0
    
    def handle_collision(self, other: "GameObject"):
        if self.mass == 0 or other.mass == 0:
            return

        if isinstance(self, Laser):
            if not isinstance(other, Player):
                dir = other.pos - self.pos
                if dir.length() == 0:
                    dir = pygame.Vector2(random.uniform(-1,1), random.uniform(-1,1))
                dir = dir.normalize()
                other.vel += dir * self.vel.length() * self.mass
            return

        if isinstance(other, Laser):
            if not isinstance(self, Player):
                dir = self.pos - other.pos
                if dir.length() == 0:
                    dir = pygame.Vector2(random.uniform(-1,1), random.uniform(-1,1))
                dir = dir.normalize()
                self.vel += dir * other.vel.length() * other.mass
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

    def is_expired(self):
        pass

    def collides_with(self, other):
        pass

# --- Rock (Asteroid) ---

class Rock(GameObject):
    def __init__(self, pos):
        sprite = pygame.image.load("door.png")
        angle = random.uniform(0, 360)
        speed = random.uniform(1, 2.5)
        dir = pygame.Vector2(1, 0).rotate(angle) * speed
        mass = random.uniform(0.5, 1.5)
        super().__init__(pos, vel=dir, angle=angle, sprite=sprite, mass=mass)
        self.rotation = random.uniform(-2, 2)
        self.current_rotation = 0
        self.cycles = 0

    def update(self):
        super().update()
        self.current_rotation = (self.current_rotation + self.rotation) % 360

        wrapped = False
        if self.pos.x < -50:
            self.pos.x = 1330
            wrapped = True
        elif self.pos.x > 1330:
            self.pos.x = -50
            wrapped = True
        if self.pos.y < -50:
            self.pos.y = 770
            wrapped = True
        elif self.pos.y > 770:
            self.pos.y = -50
            wrapped = True

        if wrapped:
            self.cycles += 1

    def draw(self, surface):
        resized = pygame.transform.scale_by(self.sprite, self.mass)
        rotated = pygame.transform.rotate(resized, self.current_rotation)
        rect = rotated.get_rect(center=(self.pos.x, self.pos.y))
        surface.blit(rotated, rect.topleft)

    def is_expired(self):
        return self.cycles >= 2
    
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

# ~~~ LASER ~~~

class Laser(GameObject):
    def __init__(self, pos, angle):
        self.dir = pygame.Vector2(1, 0).rotate(angle)
        super().__init__(pos, vel=self.dir * 10, angle=angle, mass=0.005)
        self.range = 200
        self.distance_travelled = 0

    def update(self):
        super().update()
        self.distance_travelled += self.vel.length()

    def draw(self, surface):
        pygame.draw.line(surface, (255,0,0), self.pos, self.pos + self.dir * 20, 3)

    def is_expired(self):
        return self.distance_travelled >= self.range
    
    def get_radius(self):
        return 5


# --- Game Controller ---

class GameCtrl:
    def __init__(self):
        pygame.init()

        self.game_font = pygame.font.SysFont("Lucida Sans", 24)
        self.clock = pygame.time.Clock()

        self.player = Player()
        self.lasers = []
        self.rocks = []
        self.enemies = []
        self.background = pygame.image.load("background.png")
        self.window = pygame.display.set_mode((1280, 720))
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
                    self.lasers.append(Laser(self.player.pos, self.player.angle))

    def update(self):
        self.player.update()
        self.update_lasers()
        self.update_rocks()
        self.check_collisions()
        
    def update_lasers(self):
        for laser in self.lasers:
            laser.update()
        self.lasers = [l for l in self.lasers if not l.is_expired()]

    def update_rocks(self):
        for rock in self.rocks:
            rock.update()
        self.rocks = [r for r in self.rocks if not r.is_expired()]
        self.spawner()

    def spawner(self):
        self.spawn_timer += 1
        if self.spawn_timer > 120:
            self.spawn_timer = 0
            Rock.spawn_random(self.rocks)

    def check_collisions(self):
        all_objects = [self.player] + self.rocks + self.lasers
        for i, obj1 in enumerate(all_objects):
            for obj2 in all_objects[i+1:]:
                if obj1.get_radius() and obj2.get_radius():
                    if obj1.pos.distance_to(obj2.pos) < obj1.get_radius() + obj2.get_radius():
                        obj1.handle_collision(obj2)
                        obj2.handle_collision(obj1)

    def draw_window(self):
        self.window.blit(self.background, (0,0))
        self.player.draw(self.window)
        for laser in self.lasers:
            laser.draw(self.window)
        for rock in self.rocks:
            rock.draw(self.window)
        pygame.display.flip()

class Player(GameObject):
    def __init__(self):
        sprite = pygame.image.load("robot.png")
        super().__init__((640,360), sprite=sprite, mass=2)
        self.thrust = 0.05


    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.angle -= 3
        if keys[pygame.K_RIGHT]:
            self.angle += 3

        dir = pygame.Vector2(1, 0).rotate(self.angle)
        self.acc = pygame.Vector2(0, 0)
        if keys[pygame.K_UP]:
            self.acc += dir * self.thrust        
        if keys[pygame.K_DOWN]:
            self.acc -= dir * self.thrust

        super().update()

        self.pos.x = max(0, min(1280, self.pos.x))
        self.pos.y = max(0, min(720, self.pos.y))
        
if __name__ == "__main__":
    GameCtrl()