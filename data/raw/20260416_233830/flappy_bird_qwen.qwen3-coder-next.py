import pygame
import sys
import random

# 初始化 pygame
pygame.init()

# 常量定义
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BIRD_WIDTH = 40
BIRD_HEIGHT = 30
BIRD_X = 160
BIRD_Y_START = 300
GRAVITY = 0.35
FLAP_STRENGTH = -7.5
PIPE_WIDTH = 80
PIPE_GAP = 170
PIPE_SPEED = 3
PIPE_SPAWN_RATE = 90
MIN_PIPE_Y = 100
MAX_PIPE_Y = SCREEN_HEIGHT - 100 - PIPE_GAP

# 颜色定义
BACKGROUND_COLOR = (135, 206, 235)  # 天蓝色
GROUND_COLOR = (139, 69, 19)      # 棕色
CLOUD_COLOR = (255, 255, 255)     # 白色
BIRD_COLOR = (255, 255, 0)        # 黄色
PIPE_COLOR = (34, 139, 34)        # 绿色（森林绿）
PIPE_BORDER_COLOR = (0, 100, 0)   # 深绿
TEXT_COLOR = (255, 255, 255)      # 白色

# 初始化屏幕
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird Easy")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont(None, 64)
font_small = pygame.font.SysFont(None, 32)

def create_text_surface(text, font, color):
    return font.render(text, True, color)

def draw_clouds(surface, x_offset):
    """绘制背景云朵装饰"""
    for i in range(5):
        x = (i * 200 + x_offset) % (SCREEN_WIDTH + 200) - 100
        y = 50 + i * 40
        cloud_radius = 30
        pygame.draw.circle(surface, CLOUD_COLOR, (x, y), cloud_radius)
        pygame.draw.circle(surface, CLOUD_COLOR, (x + 30, y - 10), cloud_radius)
        pygame.draw.circle(surface, CLOUD_COLOR, (x - 30, y - 10), cloud_radius)
        pygame.draw.circle(surface, CLOUD_COLOR, (x + 20, y + 20), cloud_radius)
        pygame.draw.circle(surface, CLOUD_COLOR, (x - 20, y + 20), cloud_radius)

def main():
    random.seed(42)
    
    # 游戏状态：'START', 'PLAYING', 'GAMEOVER'
    state = 'START'
    
    # 游戏变量
    bird_y = BIRD_Y_START
    bird_velocity = 0
    score = 0
    frame_count = 0
    pipes = []
    pipes_passed = set()  # 用于记录已计分的管道组别
    
    # 窗口主循环
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state = 'START'
                    bird_y = BIRD_Y_START
                    bird_velocity = 0
                    score = 0
                    frame_count = 0
                    pipes = []
                    pipes_passed = set()
                elif event.key in (pygame.K_SPACE, pygame.K_UP) and state == 'PLAYING':
                    bird_velocity = FLAP_STRENGTH
        
        if state == 'START':
            # 绘制开始画面
            screen.fill(BACKGROUND_COLOR)
            draw_clouds(screen, 0)
            
            # 绘制地面装饰条
            pygame.draw.rect(screen, GROUND_COLOR, (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
            
            # 绘制标题
            title_surf = create_text_surface("FLAPPY BIRD EASY", font_large, TEXT_COLOR)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            screen.blit(title_surf, title_rect)
            
            # 绘制提示
            prompt_surf = create_text_surface("Press SPACE or UP to Start", font_small, TEXT_COLOR)
            prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            screen.blit(prompt_surf, prompt_rect)
            
            # 绘制鸟（静态）
            bird_rect = pygame.Rect(BIRD_X, BIRD_Y_START, BIRD_WIDTH, BIRD_HEIGHT)
            pygame.draw.rect(screen, BIRD_COLOR, bird_rect)
            pygame.draw.rect(screen, (200, 200, 0), bird_rect, 2)
            
            pygame.display.flip()
            
            # 检测开始输入
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                state = 'PLAYING'
                frame_count = 0
                bird_y = BIRD_Y_START
                bird_velocity = FLAP_STRENGTH
                pipes = []
                pipes_passed = set()
        
        elif state == 'PLAYING':
            # 更新游戏状态
            frame_count += 1
            
            # 鸟物理更新
            bird_velocity += GRAVITY
            bird_y += bird_velocity
            
            # 检查鸟是否出界
            if bird_y < 0 or bird_y + BIRD_HEIGHT > SCREEN_HEIGHT - 30:
                state = 'GAMEOVER'
            
            # 管道生成
            if frame_count % PIPE_SPAWN_RATE == 0:
                center_y = random.randint(MIN_PIPE_Y, MAX_PIPE_Y)
                pipe_top = pygame.Rect(SCREEN_WIDTH, 0, PIPE_WIDTH, center_y - PIPE_GAP // 2)
                pipe_bottom = pygame.Rect(SCREEN_WIDTH, center_y + PIPE_GAP // 2, PIPE_WIDTH, SCREEN_HEIGHT - (center_y + PIPE_GAP // 2) - 30)
                pipes.append((pipe_top, pipe_bottom, frame_count // PIPE_SPAWN_RATE))
            
            # 更新管道位置和检测碰撞
            for i in range(len(pipes) - 1, -1, -1):
                pipe_top, pipe_bottom, pipe_id = pipes[i]
                
                # 移动管道
                pipe_top.x -= PIPE_SPEED
                pipe_bottom.x -= PIPE_SPEED
                
                # 移除出屏幕的管道
                if pipe_top.right < 0:
                    pipes.pop(i)
                    continue
                
                # 鸟与管道碰撞检测
                bird_rect = pygame.Rect(BIRD_X, bird_y, BIRD_WIDTH, BIRD_HEIGHT)
                
                if bird_rect.colliderect(pipe_top) or bird_rect.colliderect(pipe_bottom):
                    state = 'GAMEOVER'
                
                # 计分检测
                if pipe_id not in pipes_passed and bird_rect.left > pipe_bottom.right:
                    score += 1
                    pipes_passed.add(pipe_id)
            
            # 绘制画面
            screen.fill(BACKGROUND_COLOR)
            draw_clouds(screen, -frame_count * 0.5)
            
            # 绘制地面装饰条
            pygame.draw.rect(screen, GROUND_COLOR, (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
            
            # 绘制管道
            for pipe_top, pipe_bottom, pipe_id in pipes:
                # 上管道
                pygame.draw.rect(screen, PIPE_COLOR, pipe_top)
                pygame.draw.rect(screen, PIPE_BORDER_COLOR, pipe_top, 2)
                # 下管道
                pygame.draw.rect(screen, PIPE_COLOR, pipe_bottom)
                pygame.draw.rect(screen, PIPE_BORDER_COLOR, pipe_bottom, 2)
            
            # 绘制鸟
            bird_rect = pygame.Rect(BIRD_X, bird_y, BIRD_WIDTH, BIRD_HEIGHT)
            pygame.draw.rect(screen, BIRD_COLOR, bird_rect)
            pygame.draw.rect(screen, (200, 200, 0), bird_rect, 2)
            
            # 绘制 HUD
            score_surf = create_text_surface(f"Score: {score}", font_small, TEXT_COLOR)
            score_rect = score_surf.get_rect(topleft=(10, 10))
            screen.blit(score_surf, score_rect)
            
            pygame.display.flip()
        
        elif state == 'GAMEOVER':
            # 绘制游戏结束画面
            screen.fill(BACKGROUND_COLOR)
            draw_clouds(screen, 0)
            
            # 绘制地面装饰条
            pygame.draw.rect(screen, GROUND_COLOR, (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
            
            # 绘制管道残留
            for pipe_top, pipe_bottom, pipe_id in pipes:
                pygame.draw.rect(screen, PIPE_COLOR, pipe_top)
                pygame.draw.rect(screen, PIPE_BORDER_COLOR, pipe_top, 2)
                pygame.draw.rect(screen, PIPE_COLOR, pipe_bottom)
                pygame.draw.rect(screen, PIPE_BORDER_COLOR, pipe_bottom, 2)
            
            # 绘制鸟
            bird_rect = pygame.Rect(BIRD_X, bird_y, BIRD_WIDTH, BIRD_HEIGHT)
            pygame.draw.rect(screen, BIRD_COLOR, bird_rect)
            pygame.draw.rect(screen, (200, 200, 0), bird_rect, 2)
            
            # 绘制 Game Over 文本
            gameOver_surf = create_text_surface("GAME OVER", font_large, TEXT_COLOR)
            gameOver_rect = gameOver_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            screen.blit(gameOver_surf, gameOver_rect)
            
            # 绘制最终分数
            final_score_surf = create_text_surface(f"Final Score: {score}", font_small, TEXT_COLOR)
            final_score_rect = final_score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(final_score_surf, final_score_rect)
            
            # 绘制重试提示
            restart_surf = create_text_surface("Press R to Restart", font_small, TEXT_COLOR)
            restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
            screen.blit(restart_surf, restart_rect)
            
            pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()