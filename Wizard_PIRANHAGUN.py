import pygame
import math

from random import randint, random
from Graph import *

from Character import *
from State import *
from HelperFunctions import *

class Wizard_PIRANHAGUN(Character):

    def __init__(self, world, image, projectile_image, base, position, explosion_image = None):

        Character.__init__(self, world, "wizard", image)

        self.projectile_image = projectile_image
        self.explosion_image = explosion_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "wizard_move_target", None)
        self.target = None

        self.maxSpeed = 50
        self.min_target_distance = 100
        self.projectile_range = 100
        self.projectile_speed = 100
        self.buffer = 20
        
        self.currentLevel = 0
        self.route = randint(2, 3)
        self.comfortZone = self.min_target_distance * 10/12
        self.kiting = False
        self.dying = False
        self.damaged = False
        self.hitWall = False
        self.targetted = False

        seeking_state = WizardStateSeeking_PIRANHAGUN(self)
        attacking_state = WizardStateAttacking_PIRANHAGUN(self)
        ko_state = WizardStateKO_PIRANHAGUN(self)
        retreating_state = WizardStateRetreating_PIRANHAGUN(self)
        

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(retreating_state)
        
        self.brain.set_state("seeking")
        
        self.getDistance = lambda object1, object2: (Vector2(object1.position) - Vector2(object2.position)).length() 

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        

        Character.process(self, time_passed)
        self.hitWall = onwallcollide(self, time_passed)
        self.targetted =  targetted(self)
        level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range", "healing_cooldown"]
        
        lookOut = [0,1,5,8]
        detectEnemies(self, lookOut)
        
        if time_passed % 3 == 0:
            # print(detectEnemies(self, lookOut))
            print("Test")
            
        
        if self.current_hp < 0.3 * self.max_hp:
            self.dying = True
        if self.current_hp > 0.7 * self.max_hp:
            self.dying = False
        
        if self.current_hp < self.max_hp:
            self.damaged = True
        else:
            self.damaged = False

        # print(str(self.dying))
        print(self.move_target.position)
        if self.can_level_up():
            
            choice = 2
            
            self.currentLevel  += 1
            self.level_up(level_up_stats[choice])      
            


class WizardStateSeeking_PIRANHAGUN(State):
    #move towards enemy base
    def __init__(self, wizard):

        State.__init__(self, "seeking")
        self.wizard = wizard

        self.wizard.path_graph = self.wizard.world.paths[self.wizard.route]
        

    def do_actions(self):
        # print("Seeking")
        self.wizard.velocity = self.wizard.move_target.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip();
            self.wizard.velocity *= self.wizard.maxSpeed

    def check_conditions(self):
        #check for opponent --> within range? --> attack
        ## if no target find one, if can attack --> attack else, run
        #move along path

        
         #move along path
        if (self.wizard.position - self.wizard.move_target.position).length() < 8:
            if self.current_connection < self.path_length:
                self.wizard.lastNode = self.path[self.current_connection].fromNode
                #move to next node in path
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
                # print(self.current_connection)
        
        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        
        if self.wizard.target is None:
            if nearest_opponent is not None:
                opponent_distance = (self.wizard.position - nearest_opponent.position).length()
                if opponent_distance <= self.wizard.min_target_distance:
                    self.wizard.target = nearest_opponent
                    if self.wizard.current_ranged_cooldown <= 0:
                        return "attacking"
                    else:
                        return "retreating"
        else:
            if self.wizard.current_ranged_cooldown <=0:
                return "attacking"

            
        if (Vector2(nearest_opponent.position) - self.wizard.position).length() > 1.2 * self.wizard.min_target_distance and \
            self.wizard.current_hp < self.wizard.max_hp:
                self.wizard.heal()
                self.wizard.kiting = False
                return "seeking"

            
        ## if wizard is moving towards base but too far away
        if self.wizard.move_target.position == self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position and \
             self.wizard.getDistance(self.wizard.move_target, self.wizard) > self.wizard.min_target_distance * 2:
                nearestNode = get_Nearest_Node_In_Path(self.wizard.position, self.wizard.path_graph)
                self.wizard.move_target.position = nearestNode.position
                self.wizard.kiting = False
                return "seeking"
        
        if self.wizard.hitWall == True:
            self.wizard.kiting = False
            return "seeking"
        
        return None
    
    def entry_actions(self):
        # print("seeking")

        #Default initialised path to enemy base. 
        if self.wizard.kiting == False:
            print(str(self.wizard.kiting))
            # print(list(self.wizard.path_graph.nodes.keys()))
            nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)
            # nearest_node = get_Nearest_Node_In_Path(self.wizard.position, self.wizard.path_graph)
            # path along designated route

            
            self.path = pathFindAStar(self.wizard.path_graph, \
                nearest_node, \
                self.wizard.path_graph.nodes[self.wizard.base.target_node_index])
            
            # if list(self.wizard.path_graph.nodes.keys()).index(nearest_node.id) == False:
            #     path = pathFindAStar(self.wizard.world.graph, nearest_node, \
            #         self.wizard.world.graph.nodes[self.wizard.base.spawn_node_index])
            #     self.path.extend(path)
                
            self.path_length = len(self.path)

            if (self.path_length > 0):
                self.current_connection = 0
                self.wizard.move_target.position = self.path[0].toNode.position
            else:
                self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position
        
        if self.wizard.kiting == True:
            print(str(self.wizard.kiting))
            nearestNode = get_Nearest_Node_In_Path(self.wizard.position, self.wizard.path_graph)
            # Best Case -- nearestNode is closest to/ towards enemy base
            nextNode = nearestNode
            
            # print(nearestNode.id)
            
            # By right, when kiting is triggered, self.wizard.lastNode exists
            # Alternate Case -- nearestNode is away from enemy base
            ## lastNode --> closer to ally base
            if self.wizard.lastNode is not None:
                if nearestNode is self.wizard.lastNode:
                    lastNodeIndex = list(self.wizard.path_graph.nodes.keys()).index(nearestNode.id)
                    if lastNodeIndex + 1 == self.wizard.base.target_node_index:
                        nextNode = self.wizard.path_graph.nodes[self.wizard.base.target_node_index]
                        return nextNode
                    else:
                        nextNode = list(self.wizard.path_graph.nodes.values())[lastNodeIndex + 1]
                        return nextNode

            
            end = self.wizard.path_graph.nodes[self.wizard.base.target_node_index]
            # ///  following designated route. ///
            self.path = pathFindAStar(self.wizard.path_graph, nextNode, end)

            
            self.path_length = len(self.path)
            
            if (self.path_length > 0):
                self.current_connection = 0
                self.wizard.move_target.position = self.path[0].fromNode.position
                
            else:
                self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position
       
        return  
                
        
class WizardStateRetreating_PIRANHAGUN(State):
    # move back to base
    def __init__(self, wizard):
        
        State.__init__(self, "retreating")
        self.wizard = wizard   
        
    def do_actions(self):

        self.wizard.velocity = self.wizard.move_target.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip();
            self.wizard.velocity *= self.wizard.maxSpeed

    
    def check_conditions(self):

        #move along path
        if (self.wizard.position - self.wizard.move_target.position).length() < 8:
            if self.current_connection < self.path_length:
                self.wizard.lastNode = self.path[self.current_connection].fromNode
                #move to next node in path
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            else:
                self.wizard.kiting = False
                return "seeking"
        
        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        if self.wizard.getDistance(nearest_opponent, self.wizard) >= self.wizard.min_target_distance:
            self.wizard.kiting = True
            return "seeking"
        
        if self.wizard.target is not None:
            if  self.wizard.getDistance(self.wizard.target, self.wizard) > self.wizard.min_target_distance:
                self.wizard.kiting = True
                return "seeking"
        
        else: 
            self.wizard.kiting = False
            return "seeking"
            
        ## if hp below threshold --> heal
        ## if target still exist --> (kiting = True) --> seeking --> attack
        ## if ranged cooldown done --> (kiting = True) --> seeking
        ## if target dead --> (kiting = True) --> seek
        
        if self.wizard.current_healing_cooldown <= 0:
            if self.wizard.current_ranged_cooldown <=0:
                self.wizard.kiting = True
                return "seeking"
                
        else:
            if self.wizard.damaged == True:
                self.wizard.heal()
                return "retreating"
        
        if self.wizard.dying == True:
            if self.wizard.targetted == True:
                return "attacking"
            else:
                self.wizard.heal()
                self.wizard.targt = None
                self.wizard.kiting = False
                return "retreating"
        
        if self.wizard.world.get(self.wizard.target.id) is None or self.wizard.target.ko:
            self.wizard.target = None
            if self.wizard.dying == True:
                self.wizard.heal()
                return "retreating"
            else:
                self.wizard.kiting = True
                return "seeking"
        
        return 
    
    def entry_actions(self):

        #assign a path back to base
        
        nearestNode = get_Nearest_Node_In_Path(self.wizard.position, self.wizard.path_graph)
        nearestNodeIndex = list(self.wizard.path_graph.nodes.keys()).index(nearestNode.id)
        currenttoEnemyBase =  (self.wizard.position - self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position).length()
        currenttoAllyBase = (self.wizard.position - self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index].position).length()
        nearesttoEnemyBase = (Vector2(nearestNode.position) - self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position).length()
        nearesttoAllyBase = (Vector2(nearestNode.position) - self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index].position).length()
        
        # Best Best Case
        previousNode = self.wizard.lastNode
        if previousNode is None:
            #Alternate Best Case
            previousNode = nearestNode
            ##in case of nearestNode being closer to target than base 
            if nearestNodeIndex == self.wizard.base.target_node_index:
                ## If nearestNode is base.target_node_index --> go previous node in path_graph
                previousNode = list(self.wizard.path_graph.nodes.values())[nearestNodeIndex - 1] #
                return previousNode
            elif nearestNodeIndex == self.wizard.base.spawn_node_index:
                ## If nearestNode is the base, move towards base.
                ## Will cause self.path_length later on to be 0
                previousNode = selif.wizard.path_graph.nodes[self.wizard.base.spawn_node_index] #
                return previousNode
            elif nearestNodeIndex - 1 == self.wizard.base.spawn_node_index:
                ## Occur at either node 1 or node 5 or node 8
                previousNode = self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index]
                return previousNode
            elif nearestNodeIndex + 1 == self.wizard.base_target_node_index:
                ## Occurs at either node 3 or node 7 or node 11
                if currenttoEnemyBase < nearesttoEnenmyBase:
                    previousNode = nearestNode
                    return previousNode
                else:
                    previousNode = list(self.wizard.path_graph.nodes.values())[nearestNodeIndex - 1]
                    return previousNode
            else:
                if nearesttoAllyBase < currenttoAllyBase:
                    previousNode = nearestNode
                    return previousNode
                else:
                    previousNode = list(self.wizard.path_graph.nodes.values())[nearestNodeIndex - 1]
                    return previousNode

        end = self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index]
    
        print(previousNode.id)
        self.path = pathFindAStar(self.wizard.world.graph, previousNode, end)
        
        self.path_length = len(self.path)   
        
        
        if self.path_length > 0:
            self.current_connection = 0
            self.wizard.move_target.position = self.path[self.current_connection].fromNode.position
        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index].position
        
        return 

class WizardStateAttacking_PIRANHAGUN(State):

    def __init__(self, wizard):

        State.__init__(self, "attacking")
        self.wizard = wizard

    def do_actions(self):
        
        # stop and attack enemies

        opponent_distance = (self.wizard.target.position - self.wizard.position).length()
        if opponent_distance <= self.wizard.min_target_distance:
            self.wizard.velocity = Vector2(0,0)
            if self.wizard.current_ranged_cooldown <= 0:
                self.wizard.ranged_attack(self.wizard.target.position, self.wizard.explosion_image)
                self.target_hp = self.wizard.target.current_hp
                    

        #move into range to attack enemies
        else:
            self.wizard.velocity = self.wizard.target.position - self.wizard.position
            if self.wizard.velocity.length() > 0:
                self.wizard.velocity.normalize_ip();
                self.wizard.velocity *= self.wizard.maxSpeed
        
        
        return

    def check_conditions(self):

        #check if there is a nearer enemy --> change target
        #check if the current target is dead --> find new target
        #check if hp less than threshold --> retreat and heal
        #check if enemies too close --> retreat
        
        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        if self.wizard.target is not None:
            if nearest_opponent is not None:
                if nearest_opponent is not self.wizard.target:
                    self.wizard.target = nearest_opponent
                    if self.wizard.current_ranged_cooldown <= 0:
                        return "attacking"
                    else:
                        return "retreating"
        

        if self.wizard.world.get(self.wizard.target) is None or self.wizard.target.ko:
            self.wizard.target = None
            self.wizard.kiting = True
            return "seeking"
        
        return None

    def entry_actions(self):

        return None


class WizardStateKO_PIRANHAGUN(State):

    def __init__(self, wizard):

        State.__init__(self, "ko")
        self.wizard = wizard

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.wizard.current_respawn_time <= 0:
            self.wizard.current_respawn_time = self.wizard.respawn_time
            self.wizard.ko = False
            self.wizard.path_graph = self.wizard.world.paths[self.wizard.route]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.wizard.current_hp = self.wizard.max_hp
        self.wizard.position = Vector2(self.wizard.base.spawn_position)
        self.wizard.velocity = Vector2(0, 0)
        self.wizard.target = None
        self.wizard.kiting = False
        self.wizard.dying = False
        self.wizard.lastNode = self.wizard.world.graph.nodes[self.wizard.base.spawn_node_index]

        return None



def get_Nearest_Node_In_Path(position,graph):
    
    currentIndex = 0
    nearest = None
    # self.nodes is a dictionary. 
    for node in graph.nodes.values():
        if nearest is None:
            nearest = node
            nearest_distance = (position - Vector2(nearest.position)).length()
        else:
            distance = (position - Vector2(node.position)).length()
            if distance < nearest_distance:
                nearest = node
                nearest_distance = distance

    return nearest


def detectEnemies(char, node):
    
    # search through all the entities, update/ get closest enemies. 
    record = {}
    
    for location in node:
        count = 0
        for entity in char.world.entities.values():
            # neutral entity
            if entity.team_id == 2:
                continue
            # same team
            if entity.team_id == char.team_id:
                continue

            if entity.name == "projectile" or entity.name == "explosion":
                continue

            if entity.ko:
                continue
            
            if (entity.position - char.world.graph.nodes[list(char.world.graph.nodes.keys()).index(location)].position).length() < 100:
                count+= 1
            
            return count
        record[node[location]] = count
        
    return record                
                

# char = self
def targetted(char):
    
    for entities in char.world.entities.values():
        if entities.team_id == 2:
            continue
        if entities.team_id == char.team_id:
            continue
        if entities.name == "projectile" or entities.name == "explosion":
            continue
        if entities.ko:
            continue
        
        if entities.target == char:
            return True
        
    return False
