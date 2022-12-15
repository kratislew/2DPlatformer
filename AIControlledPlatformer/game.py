import pygame, sys
from settings import *
from overworld import Overworld
from level import Level
#Game Setup
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()

class GameAI:
    def __init__(self):
        screen.fill('grey')
        self.max_level = 2
        self.current_level = 0
        self.reward = 0
        #AI considerations
        #AI score
        self.score = 0
        self.previous_score = 0
        #AI movements
        self.frame_iteration = 0
        self.isDead = False
        self.status = 'level'
        #setup overworld
        self.level = Level(0, screen, self.create_level, self.update_score, self.set_game_over, self.update_frames)
        #For initial AI, max level will only be zero and AI will only be able to play level 0
        #reset functionality
        #self.reset()
        
    def create_level(self, current_level):
        self.level = Level(current_level, screen, self.create_level, self.update_score, self.set_game_over, self.update_frames)
        self.status = 'level'

    #Unused for AI, not necessary visual.
    def create_overworld(self, current_level, new_max_level):
        if new_max_level > self.max_level:
            self.max_level = new_max_level
        self.overworld = Overworld(current_level,self.max_level,self.screen,self.create_level)
        self.status = 'overworld'

    #allows AI to control actions when in level
    #returns score associated with action
    def perform_action(self, action):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        self.previous_score = self.score
        screen.fill('grey')
        self.run(action)
        pygame.display.update()
        clock.tick(60)
        return (self.score - self.previous_score), self.isDead, self.score

    #not used for AI, will select next level when user confirms next level.
    def perform_overworld_selection(self, action):
        self.overworld.input(action)

    #check game_over
    def set_game_over(self):
        self.isDead = True

    def check_game_over(self):
        if self.isDead or self.frame_iteration > 500:
            self.reset()

    #update AI score
    def update_score(self, amount):
        self.previous_score = self.score
        self.score += amount

    #update AI frame iteration
    def update_frames(self):
        self.frame_iteration += 1
    
    #AI reset functionality
    def reset(self):
        self.score = 0
        self.reward = 0
        self.previous_score = 0
        self.frame_iteration = 0
        self.max_level = 2
        self.status = 'level'
        self.isDead = False
        self.level = Level(self.current_level, screen, self.create_level, self.update_score, self.set_game_over, self.update_frames)

    #AI collision / movement determination functionality
        
    def run(self, action):
        self.level.run(action)

# while True:
#     #Close listener
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             sys.exit()
    
#     screen.fill('grey')
    
#     pygame.display.update()
#     clock.tick(60)