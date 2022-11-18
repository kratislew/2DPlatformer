import pygame
from tiles import AnimatedTile

class Pig(AnimatedTile):
    def __init__(self, size, x, y):
        super().__init__(size, x, y,'assets/terrain/pig')
        self.speed = 1

    def move(self):
        self.rect.y += self.speed

    def reverse(self):
        self.speed *= -1

    def update(self, shift):
        self.rect.x += shift
        self.animate()
        self.move()
    