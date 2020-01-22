import pygame
from pygame.locals import *

from math import *
from pygame.math import *
from Globals import *
from StateMachine import *
from Graph import *
from Character import *


def onwallcollide(self, time_passed):
   
    collision_list = pygame.sprite.spritecollide(self, self.world.obstacles, False, pygame.sprite.collide_mask)
    for entity in collision_list:
        if entity.team_id == self.team_id:
            continue
        elif entity.name is "obstacle":
            return True
            #nearest_node = self.path_graph.get_nearest_node(self.position)
           #self.move_target.position = nearest_node.position  
    return False
def get_entity_on_team(self, name, self_entity):

        for entity in self.entities.values():
            if entity.name == name and entity.team_id == self_entity.team_id:
                return entity
        
        return None
def get_entity_on_enemyteam(self, name, self_entity):

        for entity in self.entities.values():
            if entity.name == name and entity.team_id != self_entity.team_id and entity.team_id != 3:
                return entity
        
        return None
    
