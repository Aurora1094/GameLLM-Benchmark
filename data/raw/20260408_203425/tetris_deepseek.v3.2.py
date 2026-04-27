import pygame
import random
import sys

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
GRID_SIZE = 20  # 网格单元格大小
GRID_WIDTH = 10  # 游戏区的列数
GRID_HEIGHT = 20  # 游戏区的行数
PANEL_X = 300  # 右侧信息面板的起始X坐标
NEXT_PANEL_X = PANEL_X + 320  # 下一个方块区域
PANEL_Y = 50  # 面板Y坐标

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 128, 0)
BLUE = (0, 120, 255)
CYAN = (0, 220, 255)
YELLOW = (255, 255, 0)
PURPLE = (200, 0, 255)
ORANGE = (255, 140, 0)
LIME = (0, 220, 0)

# 游戏块设计，7种不同形状
TETROMINOS = [
    {'shape': [(0, -1), (0, 0), (0, 1), (0, 2)],                 # I
     'color': (0, 220, 255, 255), 'id': 0},
    {'shape': [(0, 0), (1, 0), (0, 1), (1, 1)],                 # O (Square)
     'color': (255, 255, 0, 255), 'id': 1},
    {'shape': [(-1, 1), (0, 1), (0, 0), (0, -1)],                # J
     'color': (0, 0, 255, 255), 'id': 2},
    {'shape': [(1, 1), (1, 0), (0, 0), (-1, 0)],                 # T
     'color': (180, 0, 200, 255), 'id': 3},
    {'shape': [(-1, 1), (0, 1), (0, 0), (1, 0)],                # S
     'color': (0, 255, 0, 255), 'id': 4},
    {'shape': [(1, 1), (0, 1), (0, 0), (-1, 0)],                 # Z
     'color': (255, 50, 0, 255), 'id': 5},
    {'shape': [(-1, 0), (0, -1), (-1, -1), (1, 0)],              # L
     'color': (255, 140, 0, 255), 'id': 5}
]

class BlockType:
    I,O,J,L,T,S,Z = 0,1,2,3,4,5,6

#block type sets
TYPE = {
    'I': 0,
    'O': 1,
    'T': 2,
    'S': 3,
    'Z': 4,
    'J': 5,
    'L': 6,
}
class Tetromino:
    def __init__(self, x: int,y: int):
        self.blocks=[]

class Tetris:
    def __init__(self):
        pygame.init()
        # 主屏幕设置
        self.screen = pygame.display.set_mode((850, 650))
        pygame.display.set_caption("Tetris Medium")
        self.clock = pygame.time.Clock()
        
        # 游戏状态
        self.speed = 1
        self.pause = False
        self.isPauseScreen=False
        self.pause_text = "PAUSED"
        # 左边的block grid (包括下个形状矩阵)
        # GRID把它分成 24(20可见+4隐藏)+6的隐藏行(19-23)
        # 每个方块位置  行 0-23,  0-9, (0,0)左上角 (row:0 col:0)
        self.grid = [[-1] * GRID_WIDTH for _ in range(TRUNCATE_ROW + 4+VISIBLE_ROW)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        
        #player piece
        self.ID_TO = ["I","O","T","S","Z","J","L"]
        self.SIDEAREA_WIDTH = 200
        self.grid_width =20
        self.grid_height=20
        #next piece attributes
        self.blockshape_idx = random.randint(0,6)  # index of piece shape in SHAPES
        self.blockshape_rot = 0   # 0,1,2,3
        # re-draw area maybe we can draw on surface etc.
        #  next block indicator
        self.next_blockshape_idx = random.randint(0,len(SHAPES)-1)

        #current moving piece, initially none, wait for
        self.cur_x = GRID_WIDTH  // 2
        self.cur_y = 0 if self.blockshape_idx!=0 else -1  #I piece starts 2
        cur_shape=SHAPES[self.blockshape_idx]
        # we maintain the pieces position using rows cols relative to the grid.
        self.current_piece = self.create_new_piece()



        # frames per sec = 30
        self.fps = 60

    def initialize(self):
        #reset
        self.grid = [[-1] * GRID_WIDTH for _ in range(24)]  #0-23
        self.score = 0
        self.lines_cleared=0
        self.level= 1
        self.lock_delay_frames=0
        self.framecount=0

        # start a game
        self. is_game_over=False
        self.init_piece()

    def rotate_blocks(positions, grid):
        """rotate a piece's block cluster 90° clockwise
        about its center of rotation.
        Arguments: positions of blocks, local coordinates """
        rotated = []
        for (x,y) in positions:
            #90° => (x,y) -> (y,-x)
            #x, y of shape coordinates here
            y_n = -0
            x1,y1= y, -1
            #x=1,y=0
            x_r = -y1
            y_r = x1
            #sc
            return

    def init_piece(self):
        self.cur_piece_idx =self.blockshape_idx
        self.next_piece =self.next_blockshape_idx
        self.cur_rotation=0
        if self.cur_piece_idx in [0,2,4,5,6]: # T, Z, S, J, L
            self.cur_piece_x, self.cur_piece_y = GRID_WIDTH//2,19
        else:
            self.cur_piece_x = GRID_WIDTH//2
    
    def new_piece(self):
        # 添加尝试生成4x4的错误情况

        self.cur_piece_idx = self.next_piece_idx
        self.next_piece_idx = (self.next_piece_idx+random.randint(0,len(SHAPES)-))%7
        # reset cur_piece rotation position
        # 根据类型决定 
        if curpiece in [0,1,2] :  #I,O,T 
            # 
            pass

        

    def run(self):
        running=True
        while running
if __name__=="__main__":
    screen=width,height = 740,880
    game=Tetris(screen)
    game.init_grid()
    clock=pygame.time.Clock()
    running=True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        dt = clock.tick(15)
        
        game.update(dt/max(dt,0.001))  #modify update as needed

    
    pygame.quit() 

import pygame
import random
import sys

# 30 ticks/sec, that's 33ms per frame
TICKS_PER_SECOND = 60
LOCK_DELAY_FRAMES = 15
GRAVITY_TICK_START_LEVEL = 48
FALL_SPEED_LEVELS = [48,43,38,33,28,23,18,13,8,6,5,5,
                    5,5,4,4, 4,3,3,3,             
                    2,  2,2,2,2,2,2,2,2,2,1]
LEVEL_UP_LINES = 10

# board parameters
GAME_WIDTH = 10
GAME_HEIGHT = 21 # including 3 rows of hidden

VISIBLE_FROM_ROW_INDEX =0

LASER_SPEED = 3

LOCK_DELAY_START = 1000

PIECES = [
    'L', 'J', 'I', 'O', 'Z', 'S', 'T'
]

ALL_PIECES= [
        [0,1,2,3,4,5,6]
]

SHAPES = {
    'I': [(-2, 0), (-1, 0), (0,0), (1,0)],    # I at zero rotation

}

TILESIZE = 30

# lock down through placement, lockDownBuffer, downButton speed

AREA_SHOW = (20, 3) # col, row (0-39, 0-59)
AREA_NEXT = (4, 4)

BLACK     = pygame.Color('black')
BGCOLOR = (40,40,40)
GRID_COLOR = (60,60,60)
COLORS = {
    'I': (0,255,255),
    'Z': (255, 87, 34),
    'S': (124, 252, 0),
    'Z':(0,255,255),
    'O': (255,255,0),
    'T':((255,255,0)),# colour?
    'J':(0,0,255),
    'L':(255, 140, 26)
    }

COLOUR_NAMES = [(200,20,20), 
                 (40, 200, 40),  # green
                 (90, 90, 240),   # blue
                 (240,240,0),      # yellow
                 (160,0,200),
                 (255,128,0),
                 (255,255,255)]    # 

def create_empty_grid(width,height,initialval=0):
    return [[initialval for _ in range(width)] for __ in