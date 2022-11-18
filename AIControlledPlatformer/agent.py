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
        #discount rate
        self.gamma = 0.9
        #AI Memory - use deque to allow popleft to be called and prevent extreme memory useage
        self.memory = deque(maxlen=MAX_MEMORY) 
        #model, trainer
        self.model = Linear_QNet(4, 256, 4)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    #get player state - to be updated with more information
    def get_state(self, game):
        player = game.level.player.sprite
        state = [
            player.on_left, 
            player.on_right, 
            player.on_ground, 
            player.on_ceiling,
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
        #random moves - initially random then as model gets better move less random
        self.ran_movement = 80 - self.n_games
        final_move = [0,0,0,0]
        
        #control randomness
        if random.randint(0, 200) < self.ran_movement:
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

        if done:
            #train long-term memory, plot results
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
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

