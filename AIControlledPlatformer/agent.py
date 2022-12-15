import torch
import random
import pygame
import numpy as np
from collections import deque
from game import GameAI
from model import Linear_QNet, QTrainer
from helper import plot
import time

#Allocated Resources
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
#Learning Rate
LR = 0.001

class Agent:
    def __init__(self):
        #Track num games played
        self.n_games = 0
        #control randomness of AI movement
        self.ran_movement = 0
        #control randomness when same score achieved
        self.same_score_count = 0
        #discount rate
        self.gamma = 0.9
        #AI Memory - use deque to allow popleft to be called and prevent extreme memory useage
        self.memory = deque(maxlen=MAX_MEMORY) 
        #model, trainer
        self.model = Linear_QNet(10, 256, 4)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    #get player state
    def get_state(self, game):
        player = game.level.player.sprite
        isDownRight = False
        isDownLeft = False
        isUpRight = False
        isUpLeft = False
        noRight = False
        noLeft = False

        solid_sprites = game.level.terrain_sprites.sprites() + game.level.pig_sprites.sprites()
        for sprite in solid_sprites:
            if(sprite.rect.colliderect(player.rect.centerx + 10, player.rect.centery + 32, 32,32)):
                isDownRight = True
            if(sprite.rect.colliderect(player.rect.centerx - 10, player.rect.centery + 32, 32,32)):
                isDownLeft = True
            if(sprite.rect.colliderect(player.rect.centerx + 64, player.rect.centery - 40, 16,16)):
                isUpRight = True
            if(sprite.rect.colliderect(player.rect.centerx + 64, player.rect.centery - 104, 16,16)):
                isUpRight = True
            if(sprite.rect.colliderect(player.rect.centerx - 48, player.rect.centery - 40, 16,16)):
                isUpLeft = True
            if(sprite.rect.colliderect(player.rect.centerx - 48, player.rect.centery - 104, 16,16)):
                isUpLeft = True
            

        if(not isDownRight and not isUpRight): noRight = True
        if(not isDownLeft and not isUpLeft): noLeft = True

        end_l = game.level.goal.sprite.rect.centerx < player.rect.centerx, # end left
        end_r = game.level.goal.sprite.rect.centerx > player.rect.centerx # end right

        m_r = (((player.on_left and not player.on_right) or (not player.on_left and not player.on_right)) and isDownRight and (not isUpRight) and end_r) 
        m_l = (((player.on_right and not player.on_left) or (not player.on_left and not player.on_right)) and isDownLeft and (not isUpLeft) and end_l)
        m_ur =((isUpRight or noRight) and end_r)
        m_ul =((isUpLeft or noLeft) and end_l)

        move_r = 0
        move_l = 0
        move_ur = 0 
        move_ul = 0

        if m_r == True: move_r = 1
        if m_l == True: move_l = 1
        if m_ur == True: move_ur = 1
        if m_ul == True: move_ul = 1

        state = [
            #player location
            player.on_left, 
            player.on_right, 
            player.on_ground, 
            player.on_ceiling,            
            
            #player next move
            move_r,
            move_l,
            move_ur,
            move_ul,

            #location of end
            game.level.goal.sprite.rect.centerx < player.rect.centerx, # end left
            game.level.goal.sprite.rect.centerx > player.rect.centerx # end right
            ]

        return np.array(state, dtype=int)

    #save information function
    def remember(self, state, action, reward, next_state, done):
        #popleft if max memory reached
        self.memory.append((state, action, reward, next_state, done))

    #method for long-term memory (movements past next)
    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            sample = random.sample(self.memory, BATCH_SIZE) #List of memory tuples
        else:
            sample = self.memory
        
        states, actions, rewards, next_states, dones = zip(*sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    #method for training next movement
    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    #get next movement
    def get_action(self, state):
        #random moves - initially random then as model gets better move less random, will get more random when same score occurs 
        #for multiple games
        self.ran_movement = (40 * self.same_score_count) - self.n_games
        final_move = [0,0,0,0]
        #control randomness
        ranNum = random.randint(0,200)
        if ranNum < self.ran_movement:
            move = random.randint(0,3)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move

def train():
    #initialize training variables
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = GameAI()
    prev_score = 0

    #begin training
    while True:
        #get current state
        state_old = agent.get_state(game)

        #get move based on state
        movement = agent.get_action(state_old)

        #perform action and get next state
        #checks if in overworld - for now no logic implemented for overworld only
        #selection of level 1
        # if game.status == 'overworld':
        #     game.perform_overworld_selection([1,1,1,1])
        # else:
        
        reward, done, score = game.perform_action(movement)
        state_new = agent.get_state(game)

        #train short-term memory
        agent.train_short_memory(state_old, movement, reward, state_new, done)

        #store movements 
        agent.remember(state_old, movement, reward, state_new, done)
        
        keys = pygame.key.get_pressed()
        #allow for user to move through levels
        if keys[pygame.K_d]:
            if game.current_level < game.max_level:
                pygame.time.wait(50)
                plot_scores = []
                plot_mean_scores = []
                total_score = 0
                record = 0
                agent = Agent()
                game.current_level = game.current_level + 1
                game.reset()
                
        elif keys[pygame.K_a]:
            if game.current_level > 0:
                pygame.time.wait(50)
                game.current_level -= 1
                plot_scores = []
                plot_mean_scores = []
                total_score = 0
                record = 0
                agent = Agent()
                game.reset()

        if done:
            #train long-term memory, plot results
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score == prev_score:
                agent.same_score_count += 1

            prev_score = score

            if score > record:
                record = score
                agent.same_score_count = 0
                agent.model.save()
                

            print('Game #', agent.n_games, ' Score: ', score, ' Record: ', record)

            #plotting
            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)
            


if __name__ == '__main__':
    train()

