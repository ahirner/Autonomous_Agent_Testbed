#!/usr/bin/env python

import pygame
from pygame.locals import *

import pyconsole

import pylab as pl


class World:
    def __init__(self, resolution=(640,480), background=((255,255,255)), font=("Courier",16,True,False)):
        self.screen = pygame.display.set_mode(resolution)
        self.screen.fill(background)
        self.font = pygame.font.SysFont(font[0],font[1],font[2],font[3])
        self.resolution = resolution
        self.background = background
        
        self.drawing = True             # Only then all the continous drawing and flipping is performed
        self.draw_frame_time = True     # Draw Timesteps into window?
        self.last_delta_time = 0        # Last time step between calling 
    
        #Setup console
        self.console = pyconsole.Console(self.screen,pygame.Rect(0,0,self.resolution[0],self.resolution[1]/2))
        self.activate_console(False)
    
    def tick (self, timestep):
        self.last_delta_time = timestep
               
        if self.drawing:
            if self.console.active:
                self.console.process_input()
                self.console.draw()
            if self.draw_frame_time:
                srf = self.font.render("dt: " + str(round(dt*1000.)) + "ms", True, (255-self.background[0],255-self.background[1],255-self.background[2]))
                self.screen.blit(srf,(0,0))
            pygame.display.flip()
            self.screen.fill(self.background)
    
    def activate_console(self, activate):
        self.console.active = activate
        
#Helper functions
def text_blit_scale(surface, font, text, color, tx, ty, scale = 1.0, centerx = True, centery = True, background = None):
    if background == None: srf = font.render(text, True, color)
    else: srf = font.render(text, True, color, background)
    #if scale <> 1.0:
#        if background == None: srf = pygame.transform.smoothscale(srf,(srf.get_width()*scale,srf.get_height()*scale))
#        else: srf = pygame.transform.scale(srf,int((srf.get_width()*scale),int(srf.get_height()*scale)))
    if centerx: tx -= srf.get_width() / 2
    if centery: ty -= srf.get_height() / 2
    surface.blit(srf, (tx,ty))

def draw_network(network, surface, font, text_scale = 1.0):
    
    #extract layer-data
    layer_list = [[]]
    names = []
    i = 0
    max_units = 0
    for l in network.modulesSorted:
        unit_descr = {}
        unit = 0
        while unit < l.dim:
            if l.inputbuffer.size > unit:
                unit_descr['inputb'] = l.inputbuffer[0][unit]
            else: unit_descr['inputb'] = 0.0
            
            if l.outputbuffer.size > unit:
                unit_descr['outputb'] = l.outputbuffer[0][unit]
            else: unit_descr['outputb'] = 0.0
            
            layer_list[i].append(unit_descr.copy())
            unit += 1
        
        max_units = max(max_units, l.dim)
        i += 1
        names.append(l.name)
        layer_list.append([])
        
    layer_list.pop()
    
    #Partition the space for drawing
    width = surface.get_width()
    height = surface.get_height()
    
    slice_w = width / (max_units+1)
    slice_h = height / len(layer_list)
    radius = min(slice_w, slice_h)/4
    
    color = pygame.Color(255,255,255)
    back_color = pygame.Color(0,0,0)
    number_scale = radius/2 / (font.get_height()*text_scale)
    
    #Calculate centers
    i = 0
    for l in layer_list:
        cy = height - (slice_h / 2) - slice_h*i
        text_blit_scale(surface, font, names[i], color, 0, cy, text_scale, False, True)
        for x in range(len(l)):
            cx = slice_w + (width-slice_w)/len(l)*x + (width-slice_w)/len(l)/2
            #Save center of circles
            l[x]['cx'] = cx
            l[x]['cy'] = cy          
        i += 1

    #Draw everything
    i = 0
    for l in layer_list:
        for connection in network.connections.get(network.modulesSorted[i]):
            if connection.__class__.__name__ == "FullConnection":
                in_index  = network.modulesSorted.index(connection.inmod)
                out_index = network.modulesSorted.index(connection.outmod)
                for weight in range(len(connection.params)):
                    #print i, in_index, out_index, weight, connection.whichBuffers(weight)
                    unit_in, unit_out = connection.whichBuffers(weight)
                    lx1, ly1 = layer_list[in_index][unit_in]['cx'],layer_list[in_index][unit_in]['cy']
                    lx2, ly2 = layer_list[out_index][unit_out]['cx'],layer_list[out_index][unit_out]['cy']

                    pygame.draw.line(surface, color, (lx1,ly1), (lx2,ly2), 3)
                    text_blit_scale(surface, font, str(round(connection.params[weight],2)), color, (lx1+lx2)/2, (ly1+ly2)/2, text_scale*number_scale, True, True, back_color)
         
        for x in range(len(l)):
            cx = l[x]['cx']
            cy = l[x]['cy']
            pygame.draw.circle(surface, color, (cx, cy), radius, 3)
            text_blit_scale(surface, font, str(round(l[x]['outputb'],2)), color, cx, cy-radius*0.5, text_scale*number_scale, True, True, back_color)
            text_blit_scale(surface, font, str(round(l[x]['inputb'],2)) , color, cx, cy+radius*0.5, text_scale*number_scale, True, True, back_color)
        
        i += 1
    return layer_list

def get_all_weights(network):

    layer_list = [[]]
    names = []
    i = 0
    max_units = 0
    for l in network.modulesSorted:
        unit_descr = {}
        unit = 0
        while unit < l.dim:
            if l.inputbuffer.size > unit:
                unit_descr['inputb'] = l.inputbuffer[0][unit]
            else: unit_descr['inputb'] = 0.0
            
            if l.outputbuffer.size > unit:
                unit_descr['outputb'] = l.outputbuffer[0][unit]
            else: unit_descr['outputb'] = 0.0
            
            layer_list[i].append(unit_descr.copy())
            unit += 1
        
        max_units = max(max_units, l.dim)
        i += 1
        names.append(l.name)
        layer_list.append([])
        
    layer_list.pop()
    i = 0
    weights = []
    for l in layer_list:
        for connection in network.connections.get(network.modulesSorted[i]):
            if connection.__class__.__name__ == "FullConnection":
                in_index  = network.modulesSorted.index(connection.inmod)
                out_index = network.modulesSorted.index(connection.outmod)
                for weight in range(len(connection.params)):
                    #print i, in_index, out_index, weight, connection.whichBuffers(weight)
                    unit_in, unit_out = connection.whichBuffers(weight)
                    weights.append(connection.params[weight])
    return weights

#Main
import code
import inspect

import math

from pybrain.tools.shortcuts import buildNetwork

from pybrain.rl.learners import *
from pybrain.rl.agents import LearningAgent

from random import *
from scipy import *


import pickle
def save_net(brain, filename):
    pickle.dump(brain, open(filename, "wb"))
def load_net(filename):
    n = pickle.load(open(filename))
    n.offset = 0                                  #seems the offsets get corrupted --> repair, bug?
    for m in n.modulesSorted: m.offset = 0
    return n

from cage import *
from cage2 import *

class Team(object):
    def __init__(self, living, task, learner = ENAC()):
        self.living = living
        self.task = task
        self.last_reward = 0
        self.agent = LearningAgent(self.living.brain, learner)
        self.oldparams = self.living.brain.params
    def Interaction(self):
        self.agent.integrateObservation(self.task.getObservation())
        self.task.performAction(self.agent.getAction())
        self.last_reward = self.task.getReward()
        self.agent.giveReward(self.last_reward)
        
        finished = self.task.isFinished()
        if finished:
            #print task.cumreward
            self.agent.newEpisode()
            self.task.reset()
        return self.last_reward, finished
    
    def Learn(self, episodes = 1):    
        self.agent.learn(episodes)
        self.agent.reset()
                        
        newparams = self.living.brain.params.copy() #get_all_weights(eater.brain)[:]
        dif = 0
        j = 0
        for i in newparams:
            dif += (self.oldparams[j] - newparams[j])**2
            j += 1
        self.oldparams = newparams
        return dif
        
if __name__ == '__main__':

    pl.ion()
    pygame.init()

    world = World((800,600), (0,0,0))
    world.console.submit_input("import __main__ as main\n")
    
    looping = True
    rendering = True
    steps = 0
    clk = pygame.time.Clock()
    fps = 30
    dt = 1./fps
    time = 0
    
    cage_env = CageEnvironment(world.screen, 9.81, 45, (0,2))
    cage_env.space.damping = 0.15
    
    #construct borders and platforms
    borders = StaticLines(cage_env, [(-20,10),(-20,-6),(0,-5),(20,-6),(20,10)] , 0.25, (0.7,0.0,0.))
    platform = StaticLines(cage_env, [(-5,0),(-1,0),(-0.5,0.5)],0.1,(0,1.0,1.0))
    platforml = StaticLines(cage_env, [(-18,-4),(-9,-4.5)],0.1,(0,1.0,0.0))
    platformr = StaticLines(cage_env, [(+18,-4),(+9,-4.5)],0.1,(0,1.0,0.0))    
    eater = Eater(cage_env)
    
    eater.brain = load_net("Eat_first_attempt.p")
    eater.brain.randomize()
    eater.brain.forget = False
    #eater.brain._setParameters([random.random()*1.-0.5 for x in range(eater.brain.paramdim)])

    task = TaskEat(cage_env, eater)    
    learner = ENAC()
    team = Team(eater, task, learner)
    
    ball = None
    ball_c = Ball(cage_env, color = (0.0,0.1,0.9), radius = 0.6)
    CollisionVisualizer(ball_c.shape, cage_env, True, False, False, False)  
    count_food = 0
    
    while looping:
        
        m_steps = 20
        reward, finished = team.Interaction()
        #team.agent.learner.explorer.mutate()

        if finished or (steps%100 >= 100-1):
        #if (steps%m_steps >= m_steps-1) or agent.history.getNumSequences() >= 2:
        #if task.isFinished() or time > 30. or eater.energy <= 0:
            dif = team.Learn()     
            print steps+1, " -     " + "brain dif: %3.8f" %dif + "  - energy: %3.3f" %eater.energy
            print "Food: ", count_food
        
        if (eater.energy <= 0.) or time > 30.: 
            eater.energy = 1.0
            print "---------------------------------------------------------------------- : tal: ", time
            eater.body.position = random.random()*40-20,2
            for s in eater.sensors: s._zero()          
            #agent.newEpisode()
            task.reset()
            time = 0

        if (steps%m_steps >= m_steps-1) and random.random() > 0.6 or time > 30:
            #team.agent.learner.explorer.sigma = [100000000000]*len(team.agent.learner.explorer.sigma)
            team.agent.learner.network.reset()
            team.agent.reset()
            #team.agent.newEpisode()               

        if (steps%40 >= 40-1):
            count = 0
            for thing in cage_env.things:
                if isinstance(thing, Food): count += 1 
            if count <= 80: Food(cage_env, (random.random()*40-20, 0))
            count_food = count
            
        text_blit_scale(world.screen, world.font, "%.1f" % reward, (255,255,255), 400,20, 1.5, False, True, (0,0,0))
        text_blit_scale(world.screen, world.font, "%.2f: energy" % eater.inbuf[0], (127,255,127), 400,40, 1, False, True, (0,0,0))
        text_blit_scale(world.screen, world.font, "%.2f: velo.x" % eater.inbuf[1], (127,255,127), 400,60, 1, False, True, (0,0,0))
        text_blit_scale(world.screen, world.font, "%.2f: accel" % eater.outbuf[0], (127,255,127), 400,80, 1, False, True, (0,0,0))
        text_blit_scale(world.screen, world.font, "%.2f: jump" % eater.outbuf[1], (127,255,127), 400,100, 1, False, True, (0,0,0))
        
        events = pygame.event.get()
        for e in events:
            if e.type==QUIT: looping = False
            if e.type==KEYDOWN:
                if e.key == K_ESCAPE: looping = False
                if e.key == K_F1: world.activate_console(not world.console.active)
                if e.key == K_F2: code.interact(local=locals())
                #if e.key == K_F3:
                if e.key == K_F4:
                    pl.clf()
                if e.key == K_LEFT: eater.acceleration = -1.
                if e.key == K_RIGHT: eater.acceleration = 1.
                if e.key == K_UP: eater.jump = True
                if e.key == K_F5: 
                    evo_n = MaskedModule(eater.brain)
                    evo_n.mutate()
                if e.key == K_F6:
                    team.agent.learning = not team.agent.learning
                    if team.agent.learning: pygame.draw.circle(world.screen, (255,255,0), (40, 40), 5)            
                if e.key == K_F7: 
                    eater.body.position = 2,3   
                if e.key == K_F10: rendering = not rendering
                pygame.draw.circle(world.screen, (255,0,0), (20, 40), 5)
            if e.type==KEYUP:
                if e.key == K_LEFT: eater.acceleration = 0.
                if e.key == K_RIGHT: eater.acceleration = 0.
                if e.key == K_UP: eater.jump = False               
                pygame.draw.circle(world.screen, (0,255,0), (20, 20), 5)
            if e.type==MOUSEBUTTONDOWN:
                if e.button == 4: 
                    cage_env.scale *= 1.05
                if e.button == 5:
                    cage_env.scale *= 1./1.05
                x, y = (pygame.mouse.get_pos())
                cage_env.offset_x -= (x-world.screen.get_width()/2)*0.25
                cage_env.offset_y -= (y-world.screen.get_height()/2)*0.25                               
            pygame.event.post(e)              
            
        cage_env.processTimeStep(1./fps)            
        if rendering: cage_env.drawThings()  
        if rendering: world.tick(dt)
        pygame.event.clear()
        if rendering: dt = clk.tick(fps)/1000.
        else: dt = 1./fps
        time += dt
        steps += 1


