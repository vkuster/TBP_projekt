import pygame, sys
from settings import *
from ZODB import FileStorage, DB
from persistent import Persistent
import transaction

levelChange = False

class GameState(Persistent):
    def __init__(self):
        self.level = 1
        self.life = 3
        self.score = 0
        self.highScore = 0

    def reset(self):
        self.level = 1
        self.life = 3
        self.score = 0

def load_game_state(root):
    if 'game_state' not in root:
        root['game_state'] = GameState()
    game_state = root['game_state']

    if not hasattr(game_state, 'level'):
        game_state.level = 1
    if not hasattr(game_state, 'life'):
        game_state.life = 3
    if not hasattr(game_state, 'score'):
        game_state.score = 0
    if not hasattr(game_state, 'highScore'):
        game_state.highScore = 0
    if not hasattr(game_state, 'score') or game_state.score is None:
        game_state.score = 0
    return game_state

def open_fs(zdatoteka):
    storage = FileStorage.FileStorage(zdatoteka)
    db = DB(storage)
    connection = db.open()
    return connection

c = open_fs( 'dbfile.fs' )
root = c.root()
game_state = load_game_state(root)

pygame.init()

screen = pygame.display.set_mode((WIDTH, NAV_THICKNESS + HEIGHT))
pygame.display.set_caption("Space Intruders")

class Player(pygame.sprite.Sprite):
    def __init__(self, position, size):
        super().__init__()
        self.x = position[0]
        self.x = position[1]
        img_path = 'assets/player/SpaceShip.png'
        self.image = pygame.image.load(img_path)
        self.image = pygame.transform.scale(self.image, (size, size))
        self.rect = self.image.get_rect(topleft = position)
        self.mask = pygame.mask.from_surface(self.image)
        self.ship_speed = PLAYER_SPEED
         
        self.life = game_state.life
        self.player_bullets = pygame.sprite.Group()
    
    def move_left(self):
        self.rect.x -= self.ship_speed

    def move_right(self):
        self.rect.x += self.ship_speed

    def _shoot(self):
        specific_pos = (self.rect.centerx - (BULLET_SIZE_PLAYER // 2), self.rect.y)
        self.player_bullets.add(Bullet(specific_pos, BULLET_SIZE_PLAYER, "player"))
        
class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, size, row_num):
        super().__init__()
        self.x = position[0]
        self.y = position[1]

        img_path = f'assets/enemies/{row_num}.png'
        self.image = pygame.image.load(img_path)
        self.image = pygame.transform.scale(self.image, (size, size))
        self.rect = self.image.get_rect(topleft=(position[0], position[1] + NAV_THICKNESS))
        self.mask = pygame.mask.from_surface(self.image)
        self.move_speed = 5
        self.to_direction = "right"
        self.bullets = pygame.sprite.GroupSingle()

    def move_left(self):
        self.rect.x -= self.move_speed

    def move_right(self):
        self.rect.x += self.move_speed

    def _shoot(self):
        specific_pos = (self.rect.centerx - (BULLET_SIZE // 2), self.rect.centery)
        self.bullets.add(Bullet(specific_pos, BULLET_SIZE, "enemy"))

    def update(self):
        if self.to_direction == "right" and self.rect.right < WIDTH:
            self.move_right()
        elif self.to_direction == "left" and self.rect.left > 0:
            self.move_left()
        else:
            self.to_direction = "left" if self.to_direction == "right" else "right"
        
class Bullet(pygame.sprite.Sprite):
    def __init__(self, position, size, side):
        super().__init__()
        self.x = position[0]
        self.y = position[1]

        img_path = f'assets/bullet/{side}.png'
        self.image = pygame.image.load(img_path)
        self.image = pygame.transform.scale(self.image, (size, size))
        self.rect = self.image.get_rect(topleft = position)
        self.mask = pygame.mask.from_surface(self.image)
        if side == "enemy":
            self.move_speed = BULLET_SPEED
        elif side == "player":
            self.move_speed = (- BULLET_SPEED)

    def _move_bullet(self):
        self.rect.y += self.move_speed
    
    def update(self):
        self._move_bullet()
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        if self.rect.bottom <= 0 or self.rect.top >= HEIGHT:
            self.kill()

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        img_path = "assets/obstacles/obstacle_large.png"
        self.image = pygame.image.load(img_path)  
        self.image = pygame.transform.scale(self.image, (size, size)) 
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 5 
        self.initial_size = size

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()
        else:
            new_size = self.initial_size - (self.initial_size * (5 - self.health) // 5)
            self.image = pygame.transform.scale(self.image, (new_size, new_size))

pygame.font.init()

class Display:
    def __init__(self, screen):
        self.screen = screen
        self.score_font = pygame.font.SysFont("monospace", FONT_SIZE)
        self.level_font = pygame.font.SysFont("impact", FONT_SIZE)
        self.event_font = pygame.font.SysFont("impact", EVENT_FONT_SIZE)
        self.text_color = pygame.Color("white")
        self.event_color = pygame.Color("blue")

    def show_life(self, life):
        life_size = 45
        img_path = "assets/life/life.png"
        life_image = pygame.image.load(img_path)
        life_image = pygame.transform.scale(life_image, (life_size, life_size))
        life_x = SPACE // 2
        life_y = (NAV_THICKNESS - life_size) // 2
        if life != 0:
           for life in range(life):
               self.screen.blit(life_image, (life_x, life_y))
               life_x += life_size + 5

    def show_score(self, score):
        score_x = WIDTH // 3 + 40
        score_y = (NAV_THICKNESS - FONT_SIZE) // 2
        score = self.score_font.render(f'score: {score}', True, self.text_color)
        self.screen.blit(score, (score_x, score_y))

    def show_level(self, level):
        level_x = WIDTH - (WIDTH // 5)
        level_y = (NAV_THICKNESS - FONT_SIZE) // 2
        level = self.level_font.render(f'Level {level}', True, self.text_color)
        self.screen.blit(level, (level_x, level_y))

    def game_over_message(self):
        message = self.event_font.render('GAME OVER!!', True, self.event_color)
        self.screen.blit(message, ((WIDTH // 3) - (EVENT_FONT_SIZE // 2), (HEIGHT // 2) - (EVENT_FONT_SIZE // 2)))

    def display_highscore(self):
        global highscore
        highscore_text = f'Highscore: {game_state.highScore}'
        highscore_message = self.event_font.render(highscore_text, True, self.event_color)
    
        x_pos = (WIDTH // 3) - (EVENT_FONT_SIZE // 2)
        y_pos = (HEIGHT // 2) - (EVENT_FONT_SIZE // 2) + EVENT_FONT_SIZE + 10 
        self.screen.blit(highscore_message, (x_pos, y_pos))

class World:
    def __init__(self, screen):
        self.screen = screen
        self.player = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.display = Display(self.screen)
        self.game_over = False
        self.player_score = game_state.score
        self.game_level = game_state.level
        self._generate_world()

    def _generate_enemies(self):
        enemy_cols = (WIDTH // CHARACTER_SIZE) // 2
        enemy_rows = 4
        for y in range(enemy_rows):
            for x in range(enemy_cols):
                my_x = CHARACTER_SIZE * x
                my_y = CHARACTER_SIZE * y
                specific_pos = (my_x, my_y)
                self.enemies.add(Enemy(specific_pos, CHARACTER_SIZE, y))

    def _generate_obstacles(self):
        start_x = 100  
        start_y = HEIGHT - 200  
        spacing = 150
        size = 100

        for i in range(4):
            obstacle = Obstacle(start_x, start_y, size)
            self.obstacles.add(obstacle)
            start_x += spacing

    def _generate_world(self):
        player_x, player_y = WIDTH // 2, HEIGHT - CHARACTER_SIZE
        center_size = CHARACTER_SIZE // 2
        player_pos = (player_x - center_size, player_y)
        self.player.add(Player(player_pos, CHARACTER_SIZE))
        self._generate_enemies()
        self._generate_obstacles()

    def add_additionals(self):
        nav = pygame.Rect(0, 0, WIDTH, NAV_THICKNESS)
        self.display.show_life(self.player.sprite.life)
        self.display.show_score(self.player_score)
        self.display.show_level(self.game_level)

    def player_move(self, attack = False):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and not self.game_over or keys[pygame.K_LEFT] and not self.game_over:
            if self.player.sprite.rect.left > 0:
                self.player.sprite.move_left()
        if keys[pygame.K_d] and not self.game_over or keys[pygame.K_RIGHT] and not self.game_over:
            if self.player.sprite.rect.right < WIDTH:
                self.player.sprite.move_right()
            
        if keys[pygame.K_r]:
            self.game_over = False
            self.player_score = 0
            self.game_level = 1
            for enemy in self.enemies.sprites():
                enemy.kill()
            self._generate_world()
            
        if attack and not self.game_over:
            self.player.sprite._shoot()

    def _detect_collisions(self):
        player_attack_collision = pygame.sprite.groupcollide(self.enemies, self.player.sprite.player_bullets, True, True)
        if player_attack_collision:
            self.player_score += 10
        for enemy in self.enemies.sprites():
            enemy_attack_collision = pygame.sprite.groupcollide(enemy.bullets, self.player, True, False)
            if enemy_attack_collision:
                self.player.sprite.life -= 1
                break
        
        enemy_to_player_collision = pygame.sprite.groupcollide(self.enemies, self.player, True, False)
        if enemy_to_player_collision:
            self.player.sprite.life -= 1
        
        for obstacle in self.obstacles.sprites():
            player_obstacle_collision = pygame.sprite.groupcollide( pygame.sprite.Group(obstacle), self.player.sprite.player_bullets, False, True)
            if player_obstacle_collision:
                self.player_score += 10
                obstacle.take_damage()
    
    def _enemy_movement(self):
        for enemy in self.enemies.sprites():
            if enemy.to_direction == "right" and enemy.rect.right < WIDTH:
                enemy.move_right()
            elif enemy.to_direction == "left" and enemy.rect.left > 0:
                enemy.move_left()
            else:
                enemy.to_direction = "left" if enemy.to_direction == "right" else "right"

    def _enemy_shoot(self):
        for enemy in self.enemies.sprites():
            if (WIDTH - enemy.rect.x) // CHARACTER_SIZE == (WIDTH - self.player.sprite.rect.x) // CHARACTER_SIZE:
                enemy._shoot()
                break

    def _check_game_state(self):
        if self.player.sprite.life <= 0:
            if self.player_score > game_state.highScore:
                game_state.highScore = self.player_score
                transaction.commit()
            self.game_over = True
            self.display.game_over_message()
            self.display.display_highscore()
            game_state.reset()
        for enemy in self.enemies.sprites():
            if enemy.rect.top >= HEIGHT:
                self.game_over = True
                self.display.game_over_message()
                break
        if len(self.enemies) == 0 and len(self.obstacles) == 0 and self.player.sprite.life > 0:
            levelChange = True
            self.game_level += 1
            self._generate_obstacles()
            self._generate_enemies()
            for enemy in self.enemies.sprites():
                enemy.move_speed += self.game_level - 1
    
    def update(self):
        self._detect_collisions()
        self._enemy_movement()
        self._enemy_shoot()
        self.player.sprite.player_bullets.update()
        self.player.sprite.player_bullets.draw(self.screen)
        [enemy.bullets.update() for enemy in self.enemies.sprites()]
        [enemy.bullets.draw(self.screen) for enemy in self.enemies.sprites()]
        self.player.draw(self.screen)
        self.enemies.draw(self.screen)
        self.obstacles.draw(self.screen)
        self.add_additionals()
        self._check_game_state()

class Main:
    def __init__(self, screen):
        self.screen = screen
        self.FPS = pygame.time.Clock()

    def main(self):
        world = World(self.screen)
        background = pygame.image.load('assets/background/background.png')
        background = pygame.transform.scale(background, (WIDTH, HEIGHT + NAV_THICKNESS))
        while True:
            self.screen.blit(background, (0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if not world.game_over:
                        transaction.begin()
                        game_state.level = world.game_level
                        game_state.life = world.player.sprite.life
                        game_state.score = world.player_score
                        transaction.commit()
                    else:
                        transaction.begin()
                        game_state.reset()
                        transaction.commit()
                    c.close()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        world.player_move(attack = True)
            world.player_move()
            world.update()
            pygame.display.update()
            self.FPS.tick(30)

if __name__ == "__main__":
    play = Main(screen)
    play.main()