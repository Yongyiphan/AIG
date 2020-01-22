import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *
from HelperFunctions import *

class Archer_PIRANHAGUN(Character):

    def __init__(self, world, image, projectile_image, base, position):

        Character.__init__(self, world, "archer", image)

        self.projectile_image = projectile_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "archer_move_target", None)
        self.target = None

        self.maxSpeed = 50
        self.min_target_distance = 100
        self.projectile_range = 100
        self.projectile_speed = 100

        self.is_on_wall = False
        self.is_stuck = False
        self.away_from_wall_start = pygame.time.get_ticks()
        
        self.knight_has_died = False

        self.range_damage_count = 0
        self.range_boost = 18

        seeking_state = ArcherStateSeeking_PIRANHAGUN(self)
       
        ko_state = ArcherStateKO_PIRANHAGUN(self)
       # stuck_state = ArcherStateStuck_PIRANHAGUN(self)
        attack_state = ArcherStateAttack_PIRANHAGUN(self)
        

        self.brain.add_state(seeking_state)
       
        self.brain.add_state(ko_state)
        #self.brain.add_state(stuck_state)
        self.brain.add_state(attack_state)
        

        self.brain.set_state("seeking")
        # print(self.current_hp)

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)
        self.is_on_wall = onwallcollide(self, time_passed)
        
        level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range"]
      
        if self.can_level_up():           
            if self.range_damage_count > 2:
                choice = 3
            else:
                choice = 2
                self.range_damage_count = self.range_damage_count + 1
            self.level_up(level_up_stats[choice])   


class ArcherStateSeeking_PIRANHAGUN(State):

    def __init__(self, archer):

        State.__init__(self, "seeking")
        self.archer = archer
        self.archer.is_stuck = False
        self.archer.path_graph = self.archer.world.paths[0]
        
        


    def do_actions(self):
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        opponent_distance = (self.archer.position - nearest_opponent.position).length()
        self.archer.velocity = self.archer.move_target.position - self.archer.position
        if self.archer.velocity.length() > 0:
            self.archer.velocity.normalize_ip()
            self.archer.velocity *= self.archer.maxSpeed
        
        if opponent_distance >= 75 and self.archer.current_hp/self.archer.max_hp * 100 < 80:
            self.archer.heal()
       

    def check_conditions(self):
       
        # check if opponent is in range
        
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        #print(self.archer.position)
        
        if nearest_opponent is not None:
            opponent_distance = (self.archer.position - nearest_opponent.position).length()
            # if (self.archer.is_on_wall == True and opponent_distance <= self.archer.min_target_distance + self.archer.range_boost):
            #     self.archer.target = nearest_opponent
            #     self.archer.is_stuck = True
            #     return "attacking"   
           
            if opponent_distance <= self.archer.min_target_distance + self.archer.range_boost:                
                self.archer.target = nearest_opponent
                if ((get_entity_on_enemyteam(self.archer.world, "base", self.archer).position - self.archer.position).length() <= self.archer.min_target_distance + self.archer.range_boost):
                    self.archer.target = get_entity_on_enemyteam(self.archer.world, "base", self.archer)
                    self.base_targeted = True
                self.archer.is_stuck = False
                return "attack"
        
        if (self.archer.position - self.archer.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.archer.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            
        return None

    def entry_actions(self):
        
        nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)
        
        # move to next node if from - to is near zero
        self.path = pathFindAStar(self.archer.path_graph, \
                                  nearest_node, \
                                  self.archer.path_graph.nodes[self.archer.base.target_node_index])
        self.path_length = len(self.path)
        if(len(self.path) > 0):
            archer_to_from = Vector2(self.archer.position - self.path[0].fromNode.position).length()
            archer_to_to = Vector2(self.archer.position - self.path[0].toNode.position).length()

            if (archer_to_from - archer_to_to < 20):
                if (self.path_length > 0):
                    self.current_connection = 0
                    self.archer.move_target.position = self.path[0].toNode.position
                    self.prev_path = self.path
                else:
                    self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.target_node_index].position
                    self.prev_path = self.path
            else:
                if (self.path_length > 0):
                    self.current_connection = 0
                    self.archer.move_target.position = self.path[0].fromNode.position
                    self.prev_path = self.path
                else:
                    self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.target_node_index].position
                    self.prev_path = self.path
        else:
            nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)
        
            self.path = pathFindAStar(self.archer.path_graph, \
                                  nearest_node, \
                                  self.archer.path_graph.nodes[self.archer.base.target_node_index])



class ArcherStateAttack_PIRANHAGUN(State):
    def __init__(self,archer):
        State.__init__(self, "attack")
        self.archer = archer
        

    def do_actions(self):
    
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        if nearest_opponent is not None:
            opponent_distance = (self.archer.position - nearest_opponent.position).length()
        if (opponent_distance <= self.archer.min_target_distance + self.archer.range_boost):             
            if nearest_opponent is not None:
                if ((get_entity_on_enemyteam(self.archer.world, "base", self.archer).position - self.archer.position).length() <= self.archer.min_target_distance + self.archer.range_boost + 80):
                    self.archer.target = get_entity_on_enemyteam(self.archer.world, "base", self.archer)
                    self.base_targeted = True
                else:
                    self.archer.target = nearest_opponent
                    self.base_targeted = False
                opponent_distance = (self.archer.position - nearest_opponent.position).length()
                if opponent_distance <= (self.archer.min_target_distance + self.archer.range_boost):                   
                    if self.archer.current_ranged_cooldown <= 0:
                        # print("Blue archer did " + str(self.archer.ranged_damage) + "to" + str(self.archer.target))
                        self.archer.ranged_attack(self.archer.target.position)                   
                    if opponent_distance >= 75 and self.archer.current_hp/self.archer.max_hp * 100 < 70 and self.base_targeted == False and self.archer.is_stuck == False:
                        self.archer.heal()
        if self.base_targeted == True:
            self.archer.velocity = Vector2(0,0)
        else:
            self.archer.velocity = self.archer.move_target.position - self.archer.position
        if self.archer.velocity.length() > 0:
            self.archer.velocity.normalize_ip();
            self.archer.velocity *= self.archer.maxSpeed
        return None


    def check_conditions(self):

        # respawned
        if (self.archer.position - self.archer.move_target.position).length() < 8:
            # continue on path
            if self.current_connection < self.path_length:
                self.archer.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
        if(self.archer.position - self.archer.target.position).length() >= self.archer.min_target_distance + self.archer.range_boost:
            return "seeking"  
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        opponent_distance = (self.archer.position - nearest_opponent.position).length()

        if opponent_distance >= self.archer.min_target_distance + self.archer.range_boost:
            return "seeking"
        return None

    def entry_actions(self):
        nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)
        
        # move to next node if from - to is near zero
        self.path = pathFindAStar(self.archer.path_graph, \
                                  nearest_node, \
                                  self.archer.path_graph.nodes[self.archer.base.spawn_node_index])
        self.path_length = len(self.path)
        if(len(self.path) > 0):
            archer_to_from = Vector2(self.archer.position - self.path[0].fromNode.position).length()
            archer_to_to = Vector2(self.archer.position - self.path[0].toNode.position).length()

            if (archer_to_from - archer_to_to < 20):
                if (self.path_length > 0):
                    self.current_connection = 0
                    self.archer.move_target.position = self.path[0].toNode.position
                    self.prev_path = self.path
                else:
                    self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.spawn_node_index].position
                    self.prev_path = self.path
            else:
                if (self.path_length > 0):
                    self.current_connection = 0
                    self.archer.move_target.position = self.path[0].fromNode.position
                    self.prev_path = self.path
                else:
                    self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.spawn_node_index].position
                    self.prev_path = self.path
        else:
            nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)
        
            self.path = pathFindAStar(self.archer.path_graph, \
                                  nearest_node, \
                                  self.archer.path_graph.nodes[self.archer.base.spawn_node_index])
        

        return None

class ArcherStateKO_PIRANHAGUN(State):

    def __init__(self, archer):

        State.__init__(self, "ko")
        self.archer = archer

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.archer.current_respawn_time <= 0:
            self.archer.current_respawn_time = self.archer.respawn_time
            self.archer.ko = False
            self.archer.path_graph = self.archer.world.paths[0]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.archer.current_hp = self.archer.max_hp
        self.archer.position = Vector2(self.archer.base.spawn_position)
        self.archer.velocity = Vector2(0, 0)
        self.archer.target = None

        return None
