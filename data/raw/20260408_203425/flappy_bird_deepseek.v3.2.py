import pygame
import random

# 初始化pygame
pygame.init()
pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.mixer.init()
pygame.init()

# 屏幕尺寸
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

class Bird:
    def __init__(self):
        self.radius = 20
        self.x = SCREEN_WIDTH // 4
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.5
        self.lift = -10  # 上升
        self.is_alive = True
        
    def update(self):
        self.velocity += self.gravity
        if self.velocity > 10:
            self.velocity = 10
        self.y += self.velocity
        
        if self.y <= 0:
            self.y = 0
        if self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.is_alive = False
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.velocity = 0

    def flap(self):
        self.velocity = -10

    def draw(self):
        center = (int(self.x), int(self.y))
        pygame.draw.circle(screen, (255, 255, 0), center, self.radius)  # 鸟（黄色）
        pygame.draw.circle(screen, (0, 0, 0), center, self.radius, 3)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                          self.radius*2, self.radius*2)

class Pipe:
    def __init__(self, x):
        self.gap_height = 200
        self.gap_y = random.randint(120, SCREEN_HEIGHT - 120)
        self.width = 80
        self.x = x
        self.scored = False  # 玩家是否已经得分

    def update(self, speed=2):
        self.x -= speed  # 使用参数传入的速度
        return
        # 为性能考虑，在这一层不更新，在主循环更新x

    def draw(self):
        # 上管道
        pygame.draw.rect(screen, (0, 180, 0), (self.x, 0, self.width, self.gap_y - self.gap_height//2))
        # 下管道
        pygame.draw.rect(screen, (0, 180, 0), (
            self.x, 
            self.gap_y + self.gap_height//2, 
            self.width, 
            SCREEN_HEIGHT - (self.gap_y + self.gap_height//2)
        ))
        # 用简单碰撞盒
        top_pipe = pygame.Rect(self.x, 0, self.width, self.gap_y - self.gap_height//2)
        bottom_pipe = pygame.Rect(self.x, self.gap_y + self.gap_height//2, self.width, SCREEN_HEIGHT)

        # 返回两个碰撞盒
        return top_pipe, bottom_pipe

    def get_rects(self):
        top = pygame.Rect(self.x, 0, self.width, self.gap_y - self.gap_height//2)
        bottom_y = self.gap_y + self.gap_height // 2
        bottom_height = SCREEN_HEIGHT - bottom_y
        bottom = pygame.Rect(self.x, bottom_y, self.width, bottom_height)
        return top, bottom

    @property
    def gap_y(self):
        # 中心点位置
        return (self.gap_y_top + self.gap_y_bottom) // 2

class Game:
    def __init__(self):
        self.bird = Bird()
        self.pipes = []
        self.pipe_spawn_timer = 0
        self.score = 0
        self.pipe_speed = 3
        self.game_over = False
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)

    def spawn_pipe(self):
        gap_y = random.randint(150, SCREEN_HEIGHT - 150)
        pipe = Pipe(SCREEN_WIDTH, gap_y)
        self.pipes.append(pipe)

    def reset(self):
        self.bird = Bird()
        self.pipes.clear()
        self.pipe_spawn_timer = 0
        self.score = 0
        self.pipe_spawn_timer = 0
        self.game_over = False
        # 一个简单的初始化，移除无用的spawn_object变量
        for i in range(3):
            pipe = Pipe(SCREEN_WIDTH + i*220)  # 三个等距管道
            self.pipes.append(pipe)

game = Game()
clock = pygame.time.Clock()
FPS = 30  # 降低帧数以方便控制

def draw_background():
    sky_blue = (135, 206, 235)  # 浅天蓝色
    screen.fill(sky_blue)
    pygame.draw.rect(screen, (126, 200, 80), (0, 500, SCREEN_WIDTH, SCREEN_HEIGHT-500))
    # 绘制草地
    pygame.draw.rect(screen, (100, 200, 100), (0, 500, SCREEN_WIDTH, 100))  # 绿草

def show_game_over(score):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # 半透明黑色层
    screen.blit(overlay, (0, 0))
    
    # 最终的文本，包含分数提示
    game_over_font = pygame.font.Font(None, 72)
    text_surface = game_over_font.render('游戏结束', True, (255, 0, 0))
    screen.blit(text_surface, (SCREEN_WIDTH//2 - text_surface.get_width()//2, SCREEN_HEIGHT//2 - 100))
    
    final_score_font = pygame.font.Font(None, 48)
    score_text1 = final_score_font.render(f"最终得分: {game.score}", 1, (0, 200, 255))
    final_score_rect = score_text1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200))
    
    screen.blit(score_text1, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))

    instruction_font = pygame.font.Font(None, 36)
    inst1 = instruction_font.render("按R键重新开始", True, (200, 255, 255))
    screen.blit(inst1, (SCREEN_WIDTH//2 - inst1.get_width()//2, 450))
    inst2 = instruction_font.render("按Q键退出", True, (200, 255, 255))
    screen.blit(inst2, (SCREEN_WIDTH//2 - inst2.get_width()//2, 500))
    
    game_over = True
    while game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False, True  # 退出游戏
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True, False  # 重新开始
                elif event.key == pygame.K_q:
                    return False, True  # 退出
        # 短暂睡眠避免高CPU占用
        pygame.time.delay(50)  # 避免游戏循环空转
        pygame.event.pump()
    return False, True  # 默认继续

def main():
    global screen
    global game
    # 初始化游戏
    game = Game()
    
    # 添加三根管道
    for i in range(3):
        pipe = Pipe((SCREEN_WIDTH+200) + i*220)  # 分布
        game.pipes.append(pipe)
    
    while True:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_SPACE):
                    game.bird.velocity = -10  # 点击后立即上升
            if event.key == pygame.K_q:
                pygame.quit()
                return
        
        # 按下W键盘
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            # 如果连续按的话，应当设定一个频率限制
            game.bird.velocity = min(game.bird.velocity, -8)  # or some logic
            # 实际上，为了支持鸟的自然下落，我们可能需要重新设计游戏机制
        game.bird.velocity = min(game.bird.velocity, 10)
        

        # 更新小鸟
        game.bird.update()

        # 生成新障碍(计时器)
        game.pipe_spawn_timer += 1
        if game.pipe_spawn_timer >= 120:  # 每120帧生成一根柱子
            pipe = Pipe(SCREEN_WIDTH)
            # 可以加个变化，比如高度或速度
            game.pipes.append(pipe)
            game.pipe_spawn_timer = 0  # 重置计时器

        # 更新管道
        for pipe in game.pipes:
            pipe.x -= game.pipe_speed

            # 检测小鸟与柱子的碰撞（可能是矩形实体周边判断）
            bird_rect = game.bird.get_rect()
            pipe_rect_top = pygame.Rect(pipe.x, 0, 80, pipe.gap_y - game.gap_height // 2)
            pipe_rect_bottom = pygame.Rect(pipe.x, pipe.gap_y + game.gap_height // 2,
                                           80, SCREEN_HEIGHT)

            if (pipe_rect_top.colliderect(bird_rect) or pipe_rect_bottom.colliderect(bird_rect)):
                # 碰到水管
                game.game_over = True
                return  # 你也可以处理游戏结束，这里只是示例，结束游戏

            if not pipe.passed and pipe.x + 80 < game.bird.x:
                game.score += 1
                pipe.passed = True

        # 画背景
        draw_background()

        # 绘制障碍物（从pipes列表）
        for pipe in game.pipes:
            pygame.draw.rect(screen, (0, 200, 0), (pipe.x, 0, 80, pipe.gap_top))
            pygame.draw.rect(screen, (0, 200, 0), (
                pipe.x,
                pipe.gap_y + game.gap_height,  # 从中间分割到下边
                80,
                SCREEN_HEIGHT - (pipe.gap_y + game.gap_height)
            ))

        # 绘制小鸟
        pygame.draw.circle(screen, (255, 255, 0), (40, int(game.bird.y)), 15)
        # 暂停，等待游戏开始：空格
        # ...剩下的绘制和更新逻辑可以补充完整

        game.bird.draw()
        for pipe in game.pipes.copy():
            if pipe.x < -100:
                game.pipes.remove(pipe)  # 移出屏幕
                # 这里可以调整难度，每5关pipe速度加一
                if game.score > 0 and game.score % 5 == 0:
                    game.pipe_speed += 0.2  # 速度少量增加

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    # bird.jump()
                    pass  # later implement
                if event.key == K_r:
                    reset_game()
                if event.key == K_ESCAPE:
                    running = False

        pygame.display.flip()
        clock.tick(FPS)
        if game_is_over:
            display_game_over()
            return


def play_game():
    global alive

    # 画出背景色
    screen.blit(background, (0,0))

    # 小鸟移动
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            alive = False
        if event.type == KEYDOWN and (event.key == K_UP or event.key == K_SPACE):
            bird.update(screen, -jump_strength)
        elif event.type == KEYUP:
            pass

    # 更新小鸟位置（受重力影响）
    bird.update(screen, gravity)

    # 更新移动并画出障碍
    for obs in pipes:
        obs.update(screen, pipe_speed)

    # 检测碰撞
    if collision_detection(bird, pipes):
        game_over()
        # 可以设置 game_state = "GAME_OVER"

    #在屏幕更新区域...
    pygame.display.flip()

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    main_loop()