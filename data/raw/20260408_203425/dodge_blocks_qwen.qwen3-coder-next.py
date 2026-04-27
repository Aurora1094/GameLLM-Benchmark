import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dodge Blocks Easy")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
BLUE = (50, 100, 220)
GREEN = (50, 220, 50)
YELLOW = (220, 220, 50)

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60

# Player settings
player_width = 50
player_height = 50
player_speed = 7

# Block settings
block_width = 40
block_height = 40
block_speed = 4  # Initial block falling speed

# Font for text
font_large = pygame.font.SysFont(None, 72)
font_small = pygame.font.SysFont(None, 36)

def show_message(text, font, color, y_offset=0):
    message = font.render(text, True, color)
    rect = message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
    screen.blit(message, rect)
    return rect

def reset_game():
    # Player position
    player_x = SCREEN_WIDTH // 2 - player_width // 2
    player_y = SCREEN_HEIGHT - player_height - 10
    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    
    # Blocks list
    blocks = []
    
    # Game state variables
    score = 0
    block_spawn_timer = 0
    block_spawn_interval = 60  # Spawn a block every 60 frames (1 second at 60 FPS)
    game_over = False
    
    return player_rect, blocks, score, block_spawn_timer, block_spawn_interval, game_over

def main():
    # Initial game state
    player_rect, blocks, score, block_spawn_timer, block_spawn_interval, game_over = reset_game()
    
    # Initialize game variables
    running = True
    game_active = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over:
                    # Restart game
                    player_rect, blocks, score, block_spawn_timer, block_spawn_interval, game_over = reset_game()
                    game_active = True
        
        if game_active:
            # Handle player movement
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_rect.x > 0:
                player_rect.x -= player_speed
            if keys[pygame.K_RIGHT] and player_rect.x < SCREEN_WIDTH - player_width:
                player_rect.x += player_speed
            
            # Update block spawn timer and spawn new blocks
            block_spawn_timer += 1
            if block_spawn_timer >= block_spawn_interval:
                block_x = random.randint(0, SCREEN_WIDTH - block_width)
                block_y = -block_height
                block_rect = pygame.Rect(block_x, block_y, block_width, block_height)
                blocks.append(block_rect)
                block_spawn_timer = 0
                
                # Slightly increase difficulty every 5 spawns
                if len(blocks) % 5 == 0 and block_spawn_interval > 20:
                    block_spawn_interval -= 3
            
            # Update blocks positions
            for block in blocks[:]:
                block.y += block_speed + (score // 500)  # Slight speed increase as score goes up
                if block.y > SCREEN_HEIGHT:
                    blocks.remove(block)
                    score += 10
            
            # Collision detection
            for block in blocks:
                if player_rect.colliderect(block):
                    game_over = True
                    game_active = False
            
            # Clear screen
            screen.fill(WHITE)
            
            # Draw player
            pygame.draw.rect(screen, BLUE, player_rect)
            
            # Draw blocks
            for block in blocks:
                random_block_color = (random.randint(150, 255), random.randint(50, 150), random.randint(50, 150))
                pygame.draw.rect(screen, random_block_color, block)
            
            # Draw score
            score_text = font_small.render(f"Score: {score}", True, BLACK)
            screen.blit(score_text, (10, 10))
            
            # Difficulty indicator
            level_text = font_small.render(f"Level: {2 + score // 500}", True, BLACK)
            screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 10, 10))
        
        if game_over:
            # Game Over overlay
            game_over_text = font_large.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            final_score_text = font_small.render(f"Final Score: {score}", True, BLACK)
            screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
            restart_text = font_small.render("Press any key to restart", True, GREEN)
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
        
        # Update display
        pygame.display.flip()
        
        # Cap frame rate
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()