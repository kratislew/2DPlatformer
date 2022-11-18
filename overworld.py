import pygame
from game_data import levels
from settings import screen_height, screen_width

class Node(pygame.sprite.Sprite):
    def __init__(self,pos,status,icon_speed):
        super().__init__()
        self.image = pygame.Surface((100,80))
        if status == 'unlocked':
            self.image.fill('green')
        else:
            self.image.fill('grey')
        self.rect = self.image.get_rect(center = pos)

        self.detection_zone = pygame.Rect(self.rect.centerx - (icon_speed/2), self.rect.centery - (icon_speed/2), icon_speed, icon_speed)

class PlayerIcon(pygame.sprite.Sprite):
    def __init__(self,pos):
        super().__init__()
        self.pos = pos
        self.image = pygame.image.load('assets/overworld/head.png').convert_alpha()
        self.rect = self.image.get_rect(center = pos)
    
    def update(self):
        self.rect.center = self.pos

class Overworld:
    def __init__(self, start_level, max_level, surface, create_level):
        
        #setup
        self.display_surface = surface
        self.max_level = max_level
        self.current_level = start_level
        self.create_level = create_level
        #level display
        self.font = pygame.font.Font(None,40)
        self.text_surf = self.font.render('Game Map',True,'Black')
        self.text_rect = self.text_surf.get_rect(center = (screen_width / 2, screen_height * (1/8)))

        #movement logic
        self.moving = False
        self.move_direction = pygame.math.Vector2(0,0)
        self.speed = 5

        #sprites
        self.setup_nodes()
        self.setup_player_icon()

    def setup_nodes(self):
        self.nodes = pygame.sprite.Group()

        for index, node_data in enumerate(levels.values()):
            if index <= self.max_level:
                node_sprite = Node(node_data['node_pos'],'unlocked', self.speed)
            else:
                node_sprite = Node(node_data['node_pos'],'locked', self.speed)

            self.nodes.add(node_sprite)     

    def setup_player_icon(self):
        self.player_icon = pygame.sprite.GroupSingle()
        icon_sprite = PlayerIcon(self.nodes.sprites()[self.current_level].rect.center)
        self.player_icon.add(icon_sprite)
    
    def input(self):
        keyp = pygame.key.get_pressed()

        if not self.moving:
            if keyp[pygame.K_d] and self.current_level < self.max_level:
                self.move_direction = self.get_movement_data('next')
                self.current_level += 1
                self.moving = True
            elif keyp[pygame.K_a] and self.current_level > 0:
                self.move_direction = self.get_movement_data('prev')
                self.current_level -= 1
                self.moving = True
            elif keyp[pygame.K_SPACE]:
                self.create_level(self.current_level)

    def get_movement_data(self, target):
        start = pygame.math.Vector2(self.nodes.sprites()[self.current_level].rect.center)
        
        if target == 'next':
            end = pygame.math.Vector2(self.nodes.sprites()[self.current_level + 1].rect.center)
        else:
            end = pygame.math.Vector2(self.nodes.sprites()[self.current_level - 1].rect.center)
        
        return(end-start).normalize()

    def update_icon_pos(self):
        if self.moving and self.move_direction:
            self.player_icon.sprite.pos += self.move_direction * self.speed
            target_node = self.nodes.sprites()[self.current_level]
            if target_node.detection_zone.collidepoint(self.icon.sprite.pos):
                self.moving = False
                self.move_direction = pygame.math.Vector2(0,0)

    def run(self):
        self.input()
        self.update_icon_pos()
        self.player_icon.update()
        self.nodes.draw(self.display_surface)
        self.player_icon.draw(self.display_surface)
        self.display_surface.blit(self.text_surf,self.text_rect)
        