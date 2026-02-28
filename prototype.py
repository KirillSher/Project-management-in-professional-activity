import pygame
import numpy as np
import random

# -------------------
# НАСТРОЙКИ ПОЛЯ
# -------------------
GRID_SIZE = 20
CELL_SIZE = 25
SIDE_PANEL = 360
BOTTOM_PANEL = 120

WIDTH = GRID_SIZE * CELL_SIZE + SIDE_PANEL
HEIGHT = GRID_SIZE * CELL_SIZE + BOTTOM_PANEL

RABBIT = 1
WOLF_F = 2
WOLF_M = 3

# Дефолтные параметры
RABBIT_REPRO = 0.1
ENERGY_LOSS = 0.25
ENERGY_GAIN = 1.0
SIM_SPEED = 6
START_RABBITS = 30
START_WOLVES = 12

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Модель «Хищник–Жертва»")
font = pygame.font.SysFont("Arial", 16)
title_font = pygame.font.SysFont("Arial", 18, bold=True)
menu_font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()

grid = np.zeros((GRID_SIZE, GRID_SIZE))
energy = np.zeros((GRID_SIZE, GRID_SIZE))

rabbits_history = []
wolves_history = []
MAX_HISTORY = 200

# -------------------
# КЛАСС СЛАЙДЕРА
# -------------------
class Slider:
    def __init__(self, x, y, width, min_val, max_val, start_val, label, integer=False):
        self.rect = pygame.Rect(x, y, width, 6)
        self.min = min_val
        self.max = max_val
        self.value = start_val
        self.label = label
        self.knob_radius = 8
        self.dragging = False
        self.integer = integer

    def draw(self):
        pygame.draw.rect(screen, (180, 180, 180), self.rect)
        ratio = (self.value - self.min) / (self.max - self.min)
        knob_x = self.rect.x + ratio * self.rect.width
        knob_y = self.rect.y + 3
        pygame.draw.circle(screen, (50, 50, 50), (int(knob_x), knob_y), self.knob_radius)

        val = int(self.value) if self.integer else round(self.value, 2)
        text = font.render(f"{self.label}: {val}", True, (0, 0, 0))
        screen.blit(text, (self.rect.x, self.rect.y - 22))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            ratio = (mouse_x - self.rect.x) / self.rect.width
            ratio = max(0, min(1, ratio))
            self.value = self.min + ratio * (self.max - self.min)
            if self.integer:
                self.value = int(round(self.value))

# -------------------
# МЕНЮ
# -------------------
class Menu:
    def __init__(self):
        self.visible = False
        self.active_tab = "help"

        # Слайдеры
        self.repro_slider = Slider(250, 170, 360, 0.01, 0.5, RABBIT_REPRO, "Размножение кроликов")
        self.loss_slider = Slider(250, 210, 360, 0.05, 1.0, ENERGY_LOSS, "Потеря энергии")
        self.gain_slider = Slider(250, 250, 360, 0.5, 2.0, ENERGY_GAIN, "Получение энергии")
        self.speed_slider = Slider(250, 290, 360, 1, 20, SIM_SPEED, "Скорость", True)
        self.rabbit_slider = Slider(250, 330, 360, 5, 100, START_RABBITS, "Начальные кролики", True)
        self.wolf_slider = Slider(250, 370, 360, 2, 50, START_WOLVES, "Начальные хищники", True)
        self.sliders = [self.repro_slider, self.loss_slider, self.gain_slider,
                        self.speed_slider, self.rabbit_slider, self.wolf_slider]

        # Окна
        self.settings_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 250, 400, 550)
        self.help_rect = pygame.Rect(WIDTH//2 - 250, HEIGHT//2 - 250, 500, 550)

    def draw(self):
        if not self.visible:
            return

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((50,50,50))
        screen.blit(overlay, (0,0))

        if self.active_tab=="settings":
            self.draw_settings()
        else:
            self.draw_help()

        # обновляем глобальные параметры
        global RABBIT_REPRO, ENERGY_LOSS, ENERGY_GAIN, SIM_SPEED, START_RABBITS, START_WOLVES
        RABBIT_REPRO = self.repro_slider.value
        ENERGY_LOSS = self.loss_slider.value
        ENERGY_GAIN = self.gain_slider.value
        SIM_SPEED = self.speed_slider.value
        START_RABBITS = self.rabbit_slider.value
        START_WOLVES = self.wolf_slider.value

    def draw_settings(self):
        pygame.draw.rect(screen,(240,240,240),self.settings_rect)
        pygame.draw.rect(screen,(0,0,0),self.settings_rect,3)
        screen.blit(menu_font.render("НАСТРОЙКИ", True,(0,0,150)),
                    (self.settings_rect.x+150, self.settings_rect.y+15))

        # вкладки
        settings_tab = pygame.Rect(self.settings_rect.x + 80, self.settings_rect.y + 50, 100,30)
        help_tab = pygame.Rect(self.settings_rect.x + 220, self.settings_rect.y + 50, 100,30)
        pygame.draw.rect(screen,(180,180,255) if self.active_tab=="settings" else (200,200,200), settings_tab)
        pygame.draw.rect(screen,(180,180,255) if self.active_tab=="help" else (200,200,200), help_tab)
        pygame.draw.rect(screen,(0,0,0),settings_tab,2)
        pygame.draw.rect(screen,(0,0,0),help_tab,2)
        screen.blit(font.render("Настройки", True,(0,0,0)), (settings_tab.x+18, settings_tab.y+5))
        screen.blit(font.render("Справка", True,(0,0,0)), (help_tab.x+25, help_tab.y+5))

        for slider in self.sliders:
            slider.draw()

        close_btn = pygame.Rect(self.settings_rect.x+150, self.settings_rect.y+500,100,30)
        pygame.draw.rect(screen,(200,100,100),close_btn)
        pygame.draw.rect(screen,(0,0,0),close_btn,2)
        screen.blit(font.render("Закрыть",True,(0,0,0)),(close_btn.x+25, close_btn.y+5))

    def draw_help(self):
        pygame.draw.rect(screen,(240,240,240),self.help_rect)
        pygame.draw.rect(screen,(0,0,0),self.help_rect,3)
        screen.blit(menu_font.render("СПРАВКА", True,(0,0,150)),
                    (self.help_rect.x+200,self.help_rect.y+15))

        settings_tab = pygame.Rect(self.help_rect.x+130, self.help_rect.y+50,100,30)
        help_tab = pygame.Rect(self.help_rect.x+270, self.help_rect.y+50,100,30)
        pygame.draw.rect(screen,(180,180,255) if self.active_tab=="settings" else (200,200,200), settings_tab)
        pygame.draw.rect(screen,(180,180,255) if self.active_tab=="help" else (200,200,200), help_tab)
        pygame.draw.rect(screen,(0,0,0),settings_tab,2)
        pygame.draw.rect(screen,(0,0,0),help_tab,2)
        screen.blit(font.render("Настройки", True,(0,0,0)), (settings_tab.x+18, settings_tab.y+5))
        screen.blit(font.render("Справка", True,(0,0,0)), (help_tab.x+25, help_tab.y+5))

        help_text = [
            "МОДЕЛЬ «ХИЩНИК–ЖЕРТВА»",
            "=================================",
            "",
            "ОБОЗНАЧЕНИЯ НА ПОЛЕ:",
            "• Зеленые клетки - кролики",
            "• Красные клетки - самки волков",
            "• Синие клетки - самцы волков",
            "",
            "ПРАВИЛА МОДЕЛИ:",
            "1. Кролики размножаются на свободные клетки",
            "2. Волки теряют энергию каждый ход",
            "3. Волки восстанавливают энергию съедая кроликов",
            "4. Волки размножаются при встрече самца и самки",
            "",
            "УПРАВЛЕНИЕ:",
            "• Старт/Пауза/Перезапуск/Шаг",
            "• Меню - настройки и справка",
            "• Пробел - пауза, R - перезапуск, S - шаг",
            "",
            "ГРАФИК: зеленая линия - кролики, красная - волки"
        ]
        y_offset=90
        for line in help_text:
            color=(0,0,150) if line.startswith(("МОДЕЛЬ","ПРАВИЛА","УПРАВЛЕНИЕ","ГРАФИК")) else (100,100,100) if line.startswith("•") else (0,0,0)
            text=font.render(line,True,color)
            screen.blit(text,(self.help_rect.x+30,self.help_rect.y+y_offset))
            y_offset+=20

        close_btn = pygame.Rect(self.help_rect.x+200, self.help_rect.y+500,100,30)
        pygame.draw.rect(screen,(200,100,100),close_btn)
        pygame.draw.rect(screen,(0,0,0),close_btn,2)
        screen.blit(font.render("Закрыть",True,(0,0,0)),(close_btn.x+25, close_btn.y+5))

    def handle_event(self,event):
        if not self.visible:
            return False
        if event.type==pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.active_tab=="settings":
                settings_tab = pygame.Rect(self.settings_rect.x+80,self.settings_rect.y+50,100,30)
                help_tab = pygame.Rect(self.settings_rect.x+220,self.settings_rect.y+50,100,30)
                close_btn = pygame.Rect(self.settings_rect.x+150,self.settings_rect.y+500,100,30)
                if help_tab.collidepoint(mouse_pos): self.active_tab="help"; return True
                elif close_btn.collidepoint(mouse_pos): self.visible=False; return True
            else:
                settings_tab = pygame.Rect(self.help_rect.x+130,self.help_rect.y+50,100,30)
                help_tab = pygame.Rect(self.help_rect.x+270,self.help_rect.y+50,100,30)
                close_btn = pygame.Rect(self.help_rect.x+200,self.help_rect.y+500,100,30)
                if settings_tab.collidepoint(mouse_pos): self.active_tab="settings"; return True
                elif close_btn.collidepoint(mouse_pos): self.visible=False; return True
        for slider in self.sliders:
            slider.handle_event(event)
        return False

# -------------------
# ФУНКЦИИ МОДЕЛИ
# -------------------
def reset_model(rabbits, wolves):
    global grid, energy, rabbits_history, wolves_history
    grid=np.zeros((GRID_SIZE,GRID_SIZE))
    energy=np.zeros((GRID_SIZE,GRID_SIZE))
    rabbits_history=[]
    wolves_history=[]
    for _ in range(int(rabbits)):
        x,y=random.randint(0,GRID_SIZE-1),random.randint(0,GRID_SIZE-1)
        grid[x][y]=RABBIT
    for _ in range(int(wolves)):
        x,y=random.randint(0,GRID_SIZE-1),random.randint(0,GRID_SIZE-1)
        grid[x][y]=random.choice([WOLF_F,WOLF_M])
        energy[x][y]=1

def get_neighbors(x,y):
    neighbors=[]
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if dx==0 and dy==0: continue
            nx,ny=x+dx,y+dy
            if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE: neighbors.append((nx,ny))
    return neighbors

def step():
    global grid,energy
    new_grid=grid.copy()
    new_energy=energy.copy()
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            if grid[x][y]==RABBIT:
                if random.random()<RABBIT_REPRO:
                    empty=[(nx,ny) for nx,ny in get_neighbors(x,y) if grid[nx][ny]==0]
                    if empty: nx,ny=random.choice(empty); new_grid[nx][ny]=RABBIT
            elif grid[x][y] in [WOLF_F,WOLF_M]:
                neighbors=get_neighbors(x,y)
                rabbits=[(nx,ny) for nx,ny in neighbors if grid[nx][ny]==RABBIT]
                if rabbits:
                    nx,ny=random.choice(rabbits)
                    new_grid[nx][ny]=grid[x][y]
                    new_energy[nx][ny]=energy[x][y]+ENERGY_GAIN
                    new_grid[x][y]=0
                else:
                    new_energy[x][y]-=ENERGY_LOSS
                    if new_energy[x][y]<=0: new_grid[x][y]=0; new_energy[x][y]=0
                if grid[x][y]==WOLF_M and energy[x][y]>1:
                    females=[(nx,ny) for nx,ny in neighbors if grid[nx][ny]==WOLF_F]
                    empty=[(nx,ny) for nx,ny in neighbors if grid[nx][ny]==0]
                    if females and empty:
                        nx,ny=random.choice(empty)
                        new_grid[nx][ny]=random.choice([WOLF_F,WOLF_M])
                        new_energy[nx][ny]=1
    grid[:]=new_grid
    energy[:]=new_energy
    rabbits_history.append(np.sum(grid==RABBIT))
    wolves_history.append(np.sum((grid==WOLF_F)|(grid==WOLF_M)))
    if len(rabbits_history)>MAX_HISTORY:
        rabbits_history.pop(0)
        wolves_history.pop(0)

# -------------------
# ГРАФИК
# -------------------
def draw_graph():
    graph_x = GRID_SIZE*CELL_SIZE+50
    graph_y = 120
    graph_width = 260
    graph_height = 130
    pygame.draw.rect(screen,(240,240,240),(graph_x,graph_y,graph_width,graph_height))
    pygame.draw.rect(screen,(0,0,0),(graph_x,graph_y,graph_width,graph_height),2)
    # screen.blit(title_font.render("График популяции",True,(0,0,0)),(graph_x+50,graph_y-25))
    pygame.draw.rect(screen,(0,200,0),(graph_x+10,graph_y-20,12,12))
    screen.blit(font.render("Кролики",True,(0,0,0)),(graph_x+25,graph_y-22))
    pygame.draw.rect(screen,(200,0,0),(graph_x+100,graph_y-20,12,12))
    screen.blit(font.render("Волки",True,(0,0,0)),(graph_x+115,graph_y-22))
    if len(rabbits_history)>1:
        max_pop=max(max(rabbits_history+wolves_history+[1]),1)
        for i in range(len(rabbits_history)-1):
            x1=graph_x+i*graph_width/MAX_HISTORY
            x2=graph_x+(i+1)*graph_width/MAX_HISTORY
            y1=graph_y+graph_height-(rabbits_history[i]/max_pop)*graph_height
            y2=graph_y+graph_height-(rabbits_history[i+1]/max_pop)*graph_height
            pygame.draw.line(screen,(0,200,0),(x1,y1),(x2,y2),2)
            y1=graph_y+graph_height-(wolves_history[i]/max_pop)*graph_height
            y2=graph_y+graph_height-(wolves_history[i+1]/max_pop)*graph_height
            pygame.draw.line(screen,(200,0,0),(x1,y1),(x2,y2),2)
    if rabbits_history:
        screen.blit(font.render(f"Кролики: {rabbits_history[-1]} Волки: {wolves_history[-1]}",True,(0,0,0)),
                    (graph_x+10,graph_y+graph_height+5))
    else:
        screen.blit(font.render(f"Кролики: {START_RABBITS} Волки: {START_WOLVES}", True, (0, 0, 0)),
                    (graph_x + 10, graph_y + graph_height + 5))

    screen.blit(title_font.render("ПАРАМЕТРЫ ЗАПУСКА", True, (0,0,150)), (graph_x + 50, graph_y + 170))
    screen.blit(font.render(f"Размножение кроликов: {RABBIT_REPRO}", True, (0,0,0)), (graph_x + 10, graph_y + 200))
    screen.blit(font.render(f"Потеря энергии: {ENERGY_LOSS}", True, (0,0,0)), (graph_x + 10, graph_y + 230))
    screen.blit(font.render(f"Получение энергии: {ENERGY_GAIN}", True, (0,0,0)), (graph_x + 10, graph_y + 260))
    screen.blit(font.render(f"Скорость: {SIM_SPEED}", True, (0,0,0)), (graph_x + 10, graph_y + 290))


# -------------------
# КНОПКИ
# -------------------
start_button = pygame.Rect(20,HEIGHT-80,100,30)
pause_button = pygame.Rect(130,HEIGHT-80,100,30)
reset_button = pygame.Rect(240,HEIGHT-80,120,30)
step_button = pygame.Rect(370,HEIGHT-80,120,30)
menu_button = pygame.Rect(WIDTH-140,20,120,30)  # верхний правый угол

reset_model(START_RABBITS,START_WOLVES)
paused=True
menu=Menu()
running=True

# -------------------
# ГЛАВНЫЙ ЦИКЛ
# -------------------
while running:
    clock.tick(int(SIM_SPEED))
    screen.fill((255,255,255))
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if menu.visible:
            menu.handle_event(event)
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                menu.visible=False
            continue
        if event.type==pygame.MOUSEBUTTONDOWN:
            if start_button.collidepoint(event.pos): paused=False
            if pause_button.collidepoint(event.pos): paused=True
            if reset_button.collidepoint(event.pos): reset_model(START_RABBITS,START_WOLVES)
            if step_button.collidepoint(event.pos) and paused: step()
            if menu_button.collidepoint(event.pos): menu.visible=True
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE: paused=not paused
            elif event.key==pygame.K_r: reset_model(START_RABBITS,START_WOLVES)
            elif event.key==pygame.K_s and paused: step()
    if not paused: step()
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect=pygame.Rect(y*CELL_SIZE,x*CELL_SIZE,CELL_SIZE,CELL_SIZE)
            if grid[x][y]==RABBIT: pygame.draw.rect(screen,(0,200,0),rect)
            elif grid[x][y]==WOLF_F: pygame.draw.rect(screen,(200,0,0),rect)
            elif grid[x][y]==WOLF_M: pygame.draw.rect(screen,(0,0,200),rect)
            pygame.draw.rect(screen,(200,200,200),rect,1)
    screen.blit(title_font.render("ГРАФИК ПОПУЛЯЦИИ",True,(0,0,150)),(GRID_SIZE*CELL_SIZE+105,70))
    pygame.draw.rect(screen,(0,200,0),start_button)
    pygame.draw.rect(screen,(200,200,0),pause_button)
    pygame.draw.rect(screen,(200,0,0),reset_button)
    pygame.draw.rect(screen,(0,150,200),step_button)
    pygame.draw.rect(screen,(200,150,150),menu_button)
    screen.blit(font.render("СТАРТ",True,(0,0,0)),(start_button.x+29,start_button.y+5))
    screen.blit(font.render("ПАУЗА",True,(0,0,0)),(pause_button.x+29,pause_button.y+5))
    screen.blit(font.render("ПЕРЕЗАПУСК",True,(0,0,0)),(reset_button.x+17,reset_button.y+5))
    screen.blit(font.render("ОДИН ШАГ",True,(0,0,0)),(step_button.x+25,step_button.y+5))
    screen.blit(font.render("МЕНЮ",True,(0,0,0)),(menu_button.x+40,menu_button.y+5))
    draw_graph()
    menu.draw()
    pygame.display.flip()
pygame.quit()
