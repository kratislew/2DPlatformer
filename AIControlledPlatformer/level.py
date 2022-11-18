import pygame
from tiles import Tile, StaticTile, House, AnimatedTile, Egg, Coin
from settings import tile_size, screen_width, screen_height
from player import Player
from support import import_csv_layout, import_cut_graphics
from pig import Pig
from game_data import levels


class Level:
    def __init__(self, current_level, screen, create_level, update_score, set_game_over, update_frames):
        #AI Considerations
        self.update_score = update_score
        self.set_game_over = set_game_over
        self.update_frames = update_frames

        #level setup and overworld transition
        self.display_surface = screen
        self.current_level = current_level
        level_data = levels[current_level]
        #self.create_overworld = create_overworld
        self.create_level = create_level
        level_message = level_data['indicator']
        self.new_max_level = level_data['unlock']
        
        #level display
        self.font = pygame.font.Font(None,20)
        self.text_surf = self.font.render(level_message,True,'White')
        self.text_rect = self.text_surf.get_rect(center = (50, 20))

        #screen shift
        self.world_shift = 0
        self.current_x = None
        
        #player setup
        player_layout = import_csv_layout(level_data['player'])
        self.player = pygame.sprite.GroupSingle()
        self.goal = pygame.sprite.GroupSingle()
        self.player_setup(player_layout)

        #terrain setup
        terrain_layout = import_csv_layout(level_data['terrain'])
        self.terrain_sprites = self.create_tile_group(terrain_layout,'terrain')
        
        #house setup
        house_layout = import_csv_layout(level_data['house'])
        self.house_sprites = self.create_tile_group(house_layout, 'house')

        #pig setup 
        pig_layout = import_csv_layout(level_data['pig'])
        self.pig_sprites = self.create_tile_group(pig_layout, 'pig')

        #constraint setup
        constraint_layout = import_csv_layout(level_data['constraints'])
        self.constraint_sprites = self.create_tile_group(constraint_layout, 'constraints')

        #coin (will be used for AI functionality) setup
        coin_layout = import_csv_layout(level_data['coin'])
        self.coin_sprites = self.create_tile_group(coin_layout, 'coin')

    #method to create tiles for game
    def create_tile_group(self, layout, type):
        sprite_group = pygame.sprite.Group()

        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                if val != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size

                    #terrain
                    if type == 'terrain':
                        terrain_tile_list = import_cut_graphics('AIControlledPlatformer/assets/terrain/terrain_tiles.png')
                        tile_surface = terrain_tile_list[int(val)]
                        sprite = StaticTile(tile_size,x,y, tile_surface)

                    #house
                    if type == 'house':
                        sprite = House(tile_size,x,y)
                    
                    #pig
                    if type == 'pig':
                        sprite = Pig(tile_size,x,y)
                    
                    #constraint tiles for flying pigs
                    if type == 'constraints':
                        sprite = Tile(tile_size,x,y)
                    
                    #coin tiles for AI to collect
                    if type == 'coin':
                        sprite = Coin(tile_size,x,y)

                    sprite_group.add(sprite)
        return sprite_group

    #player creation
    def player_setup(self, layout):
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if val == '0':
                   sprite = Player((x,y), self.update_score, self.update_frames)
                   self.player.add(sprite)
                if val == '1':
                    sprite = Egg(tile_size,x,y)
                    self.goal.add(sprite)

    #world scroll to follow AI player
    def scroll_x(self):
        player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        if player_x < screen_width / 4 and direction_x < 0:
            self.world_shift = 5
            player.speed = 0
        elif player_x > screen_width - (screen_width / 4) and direction_x > 0:
            self.world_shift = -5
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = 5

    def horizontal_movement_collision(self):
        player = self.player.sprite
        player.rect.x += player.direction.x * player.speed
        solid_sprites = self.terrain_sprites.sprites()

        for sprite in solid_sprites:
            if sprite.rect.colliderect(player.rect):
                if player.direction.x < 0:
                    player.rect.left = sprite.rect.right
                    player.on_left = True
                    self.current_x = player.rect.left
                elif player.direction.x > 0:
                    player.rect.right = sprite.rect.left
                    player.on_right = True
                    self.current_x = player.rect.right
            
        if player.on_left and (player.rect.left < self.current_x or player.direction.x >= 0):
            player.on_left = False
        if player.on_right and (player.rect.right > self.current_x or player.direction.x <= 0):
            player.on_right = False
    
    def vertical_movement_collision(self):
        player = self.player.sprite
        player.apply_gravity()
        solid_sprites = self.terrain_sprites.sprites() + self.pig_sprites.sprites()
        
        for sprite in solid_sprites:
            if sprite.rect.colliderect(player.rect):
                if player.direction.y > 0:
                    player.rect.bottom = sprite.rect.top
                    player.direction.y = 0
                    player.on_ground = True
                elif player.direction.y < 0:
                    player.rect.top = sprite.rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True
        
        #check if player is falling or jumping
        if player.on_ground and player.direction.y < 0 or player.direction.y > 1:
            player.on_ground = False
        #check if player is falling
        if player.on_ceiling and player.direction.y > 0:
            player.on_ceiling = False

    def pig_collision_reverse(self):
        for pig in self.pig_sprites.sprites():
            if pygame.sprite.spritecollide(pig,self.constraint_sprites,False):
                pig.reverse()

    #Reset input functionality removed for AI
    # def input(self):
    #     keyp = pygame.key.get_pressed()

    #     if keyp[pygame.K_r]:
    #         self.new_max_level = self.current_level
    #         self.create_level(self.current_level)
    #     elif keyp[pygame.K_ESCAPE]:
    #         self.create_overworld(self.current_level,0) 

    #check for player fall death
    def check_death(self):
        if self.player.sprite.rect.top > screen_height:
            self.new_max_level = self.current_level
            self.update_score(-10)
            self.set_game_over()
    
    #check win con
    def check_win(self):
        if pygame.sprite.spritecollide(self.player.sprite,self.goal,False):
            self.update_score(50)
            self.set_game_over()

    #AI Considerations for collecting coins (used to score for each platform to encourage generational growth)
    def check_coin_collection(self):
        collided_coins = pygame.sprite.spritecollide(self.player.sprite,self.coin_sprites,True)
        if collided_coins:
            for coin in collided_coins:
                self.update_score(10)

    def run(self, action):
        #run level / draw level terrain
        #self.input()
        self.terrain_sprites.update(self.world_shift)
        
        self.terrain_sprites.draw(self.display_surface)
        
        self.display_surface.blit(self.text_surf,self.text_rect)
        
        #draw Coins for AI pickup
        self.coin_sprites.update(self.world_shift)
        
        self.coin_sprites.draw(self.display_surface)
        
        self.check_coin_collection()

        #draw house
        self.house_sprites.update(self.world_shift)
        
        self.house_sprites.draw(self.display_surface)
        

        #draw pigs
        self.pig_sprites.update(self.world_shift)
        
        self.constraint_sprites.update(self.world_shift)
        
        self.pig_collision_reverse()
        self.pig_sprites.draw(self.display_surface)
        
        
        #player
        self.goal.update(self.world_shift)
        
        self.goal.draw(self.display_surface)
        
        self.player.update(action)
        
        self.scroll_x()
        
        self.horizontal_movement_collision()
        self.vertical_movement_collision()
        
        #display player
        self.player.draw(self.display_surface)
        
        #check win/death conditions
        self.check_death()
        self.check_win()