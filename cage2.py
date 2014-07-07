

import pymunk


class CollisionReceiver(object):
    def __init__(self, shape):
        #shape.group = get_new_collision_group_counter()
        shape.collision_receiver = self
        pass
    def receiveOnBegin(self, thing, contacts):
        return True                     #Return True if you want to get the collision to be processed
    def receiveOnPreSolve(self, thing, contacts):
        return True
    def receiveOnPostSolve(self, thing, contacts):
        return True
    def receiveOnSeparate(self, thing, contacts):
        return True
    
from cage import Thing, to_pygame_color
    
class CollisionVisualizer(Thing, CollisionReceiver):
    draw_dict = {}
    scale = 1.0
    updated = False
    def __init__(self, shape, env, begin, pre_solve, post_solve, separate):
        self.setVisualize(begin, pre_solve, post_solve, separate)
        self._clearDict()
        CollisionReceiver.__init__(self, shape)
        Thing.__init__(self, env)
    def setVisualize(self,begin, pre_solve, post_solve, separate):
        self.begin = begin
        self.pre_solve = pre_solve
        self.post_solve = post_solve
        self.separate = separate
    def _clearDict(self):
        self.draw_dict = dict(begin=[], pre_solve=[], post_solve=[], separate=[])
        
    def receiveOnBegin(self, thing, contacts):
        if self.begin: self.draw_dict['begin'].append((thing, contacts))
        return True
    def receiveOnPreSolve(self, thing, contacts):
        if self.pre_solve: self.draw_dict['pre_solve'].append((thing, contacts))
        return True
    def receiveOnPostSolve(self, thing, contacts):
        if self.post_solve: self.draw_dict['post_solve'].append((thing, contacts))
        return True
    def receiveOnSeparate(self, thing, contacts):
        if self.begin: self.draw_dict['separate'].append((thing, contacts))
        return True
    
    def updateState(self, env, dt):                
        self.updated = True
    def draw(self, env):
        import pygame
        for _, collisions in self.draw_dict.iteritems():
            for collision in collisions:
                c = to_pygame_color(collision[0].color)
                for contacts in collision[1]:
                    p1, p2 = env.transformPoint2Screen(contacts.position), env.transformPoint2Screen(contacts.position+contacts.normal*self.scale)
                    p1 = (int(p1[0]), int(p1[1]))
                    p2 = (int(p2[0]), int(p2[1]))
                    pygame.draw.circle(env.surface, (255,255,255), p1, 1)
                    pygame.draw.aaline(env.surface, c, p1, p2)
                    
        if self.updated: 
            self._clearDict()
            self.updated = False    
