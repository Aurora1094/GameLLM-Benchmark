import pygame
import random
import sys

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Roguelike Dungeon Hard")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont('Arial', 20)

class Entity:
    def __init__(self, x, y, char, color, hp=None, attack=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.hp = hp
        self.attack = attack

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x * 32, self.y * 32, 32, 32))
        text_surface = FONT.render(self.char, True, (255, 255, 255))
        surface.blit(text_surface, (self.x * 32 + 10, self.y * 32 + 10))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, '@', (255, 255, 0), hp=100, attack=10)
        self.level = 1
        self.exp = 0
        self.next_level_exp = 100

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 'E', (255, 0, 0), hp=20, attack=5)

class Item(Entity):
    def __init__(self, x, y, char, color):
        super().__init__(x, y, char, color)

def generate_dungeon(width, height, num_rooms):
    map = [['#' for _ in range(height)] for _ in range(width)]
    rooms = []
    for _ in range(num_rooms):
        w = random.randint(5, 10)
        h = random.randint(5, 10)
        x = random.randint(1, width - w - 1)
        y = random.randint(1, height - h - 1)
        for i in range(w):
            for j in range(h):
                map[x + i][y + j] = '.'
        rooms.append((x, y, w, h))
    connect_rooms(map, rooms)
    return map

def connect_rooms(map, rooms):
    for i in range(len(rooms) - 1):
        rx1, ry1, rw1, rh1 = rooms[i]
        rx2, ry2, rw2, rh2 = rooms[i + 1]
        cx1, cy1 = rx1 + rw1 // 2, ry1 + rh1 // 2
        cx2, cy2 = rx2 + rw2 // 2, ry2 + rh2 // 2
        while cx1!= cx2 or cy1!= cy2:
            if cx1 < cx2:
                cx1 += 1
            elif cx1 > cx2:
                cx1 -= 1
            elif cy1 < cy2:
                cy1 += 1
            elif cy1 > cy2:
                cy1 -= 1
            map[cx1][cy1] = '.'

def draw_map(map, entities):
    screen.fill((0, 0, 0))
    for y in range(len(map)):
        for x in range(len(map[y])):
            if map[x][y] == '.':
                pygame.draw.rect(screen, (50, 50, 50), (x * 32, y * 32, 32, 32))
    for entity in entities:
        entity.draw(screen)

def main():
    map = generate_dungeon(25, 20, 5)
    player = Player(5, 5)
    entities = [player]
    for _ in range(10):
        entities.append(Enemy(random.randint(1, 24), random.randint(1, 19)))
    for _ in range(5):
        entities.append(Item(random.randint(1, 24), random.randint(1, 19), 'I', (0, 255, 0)))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if map[player.x][player.y - 1] == '.':
                        player.y -= 1
                elif event.key == pygame.K_DOWN:
                    if map[player.x][player.y + 1] == '.':
                        player.y += 1
                elif event.key == pygame.K_LEFT:
                    if map[player.x - 1][player.y] == '.':
                        player.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if map[player.x + 1][player.y] == '.':
                        player.x += 1

        for entity in entities:
            if isinstance(entity, Enemy) and abs(entity.x - player.x) < 2 and abs(entity.y - player.y) < 2:
                entity.hp -= player.attack
                if entity.hp <= 0:
                    entities.remove(entity)
                    player.exp += 50
                    if player.exp >= player.next_level_exp:
                        player.level += 1
                        player.next_level_exp *= 2
                        player.hp += 20

        draw_map(map, entities)
        text_surface = FONT.render(f'HP: {player.hp} Level: {player.level} Floor: 1', True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()