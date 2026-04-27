import pygame
import random
import sys

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SIZE = 60
PLAYER_Y = SCREEN_HEIGHT - 40 - PLAYER_SIZE
PLAYER_SPEED = 7
OBSTACLE_SIZE = 40
OBSTACLE_MIN_SPEED = 4
OBSTACLE_MAX_SPEED = 8
OBSTACLE_SPAWN_RATE = 40  # frames between spawns
COLOR_BG = (30, 30, 40)
COLOR_PLAYER = (0, 180, 255)
COLOR_OBSTACLE = (255, 50, 50)
COLOR_TEXT = (255, 255, 255)
COLOR_HUD = (200, 200, 200)

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dodge Blocks Easy")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

# Set random seed
random.seed(42)

def main():
    # Game state variables
    running = True
    game_over = False
    score = 0
    frames = 0
    
    # Player initialization
    player_x = (SCREEN_WIDTH - PLAYER_SIZE) // 2
    keys = pygame.key.get_pressed()
    
    # Obstacles list
    obstacles = []
    
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game_over:
                    # Restart game
                    main()
                    return
        
        # Clear screen
        screen.fill(COLOR_BG)
        
        # Handle input
        keys = pygame.key.get_pressed()
        if not game_over:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= PLAYER_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += PLAYER_SPEED
                
            # Clamp player position
            player_x = max(0, min(SCREEN_WIDTH - PLAYER_SIZE, player_x))
            
            # Spawn obstacles
            frames += 1
            if frames % OBSTACLE_SPAWN_RATE == 0:
                obst_x = random.randint(0, SCREEN_WIDTH - OBSTACLE_SIZE)
                obst_y = -OBSTACLE_SIZE
                obst_speed = random.randint(OBSTACLE_MIN_SPEED, OBSTACLE_MAX_SPEED)
                obstacles.append([obst_x, obst_y, obst_speed])
                
            # Update obstacles
            for obst in obstacles:
                obst[1] += obst[2]
                
            # Remove off-screen obstacles
            obstacles = [obst for obst in obstacles if obst[1] < SCREEN_HEIGHT]
            
            # Update score
            score = frames // FPS
            
            # Collision detection
            player_rect = pygame.Rect(player_x, PLAYER_Y, PLAYER_SIZE, PLAYER_SIZE)
            for obst in obstacles:
                obst_rect = pygame.Rect(obst[0], obst[1], OBSTACLE_SIZE, OBSTACLE_SIZE)
                if player_rect.colliderect(obst_rect):
                    game_over = True
                    break
            
            # Draw player
            pygame.draw.rect(screen, COLOR_PLAYER, (player_x, PLAYER_Y, PLAYER_SIZE, PLAYER_SIZE))
            
            # Draw obstacles
            for obst in obstacles:
                pygame.draw.rect(screen, COLOR_OBSTACLE, (obst[0], obst[1], OBSTACLE_SIZE, OBSTACLE_SIZE))
        else:
            # Draw game over screen
            pass
        
        # Draw HUD
        score_text = font.render(f"Score: {score}", True, COLOR_HUD)
        screen.blit(score_text, (20, 20))
        
        # Draw game over screen if needed
        if game_over:
            game_over_text = font.render("Game Over", True, COLOR_TEXT)
            final_score_text = font.render(f"Final Score: {score}", True, COLOR_TEXT)
            restart_text = small_font.render("Press R to Restart", True, COLOR_TEXT)
            
            # Center the text
            screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60)))
            screen.blit(final_score_text, final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20)))
            screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)))
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()