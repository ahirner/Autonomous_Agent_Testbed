


import pygame
from pygame.locals import *
def to_pygame_color(color_in): 
    return pygame.Color(int(color_in[0]*255), int(color_in[1]*255), int(color_in[2]*255))

import pymunk
collision_shape_counter = 0
def get_new_collision_group_counter():
    global collision_shape_counter 
    collision_shape_counter += 1
    if collision_shape_counter == 0: collision_shape_counter += 1
    return collision_shape_counter

import numpy

__author__ = 'AH'

from pybrain.utilities import abstractMethod
from pybrain.rl.environments.twoplayergames.twoplayergame import CompetitiveEnvironment


class Thing(object):                                      #TODO: make derive from ParameterContainer?
    def __init__(self, env):
        env.embedThing(self)

    @property
    def color(self):                                #Tuple of r, g, b
        abstractMethod()
    @property
    def position(self):
        abstractMethod()
    def updateState(self, env, dt):                 #dt in seconds
        abstractMethod()        
    def draw(self, env):
        abstractMethod()
    def removeFromEnv(self, env):                   #Called upon removing
        abstractMethod()    
    def embedInEnv(self, env):                      #Called upon adding to Env
        pass
            
class StaticLines(Thing):
    def __init__(self, env, line_points, radius, color = (1.,1.,1.), friction = 0.1, elasticity = 0.25):
        #Line_points is a list of 2d points (tuples) 
        self.color_in = color
        self.body = pymunk.Body(pymunk.inf, pymunk.inf)         #Make indefinite heavy body
        
        lp_old = None
        self.lines = []
        index = 0
        for lp in line_points:                                  #Expand to individual lines 
            if index > 0:
                self.lines.append(pymunk.Segment(self.body, lp_old, lp, radius))
                self.lines[-1].owner = self
                self.lines[-1].friction = friction
                self.lines[-1].elasticity = elasticity
            lp_old = lp
            index += 1
        Thing.__init__(self, env)
    def removeFromEnv(self, env):
        env.space.remove_static(self.lines)
    def embedInEnv(self, env):
        env.space.add_static(self.lines)
    def updateState(self, env, dt):
        return None                                             #Do nothing
    def draw(self, env):
        for line in self.lines:
                body = line.body
                p1 = env.transformPoint2Screen(body.position + line.a.rotated(body.angle))
                p2 = env.transformPoint2Screen(body.position + line.b.rotated(body.angle))
                thick = int(max(env.transformDimension2Screen(line.radius) * 2, 1.0))
                c = to_pygame_color(self.color)
                p1 = (int(p1[0]), int(p1[1]))
                p2 = (int(p2[0]), int(p2[1]))
                
                pygame.draw.line(env.surface, c, p1, p2, thick)
                pygame.draw.circle(env.surface, c, p1, thick/2)
                pygame.draw.circle(env.surface, c, p2, thick/2)
    @property               
    def color(self): return self.color_in
    @property
    def position(self):             #return start of the first line
        return self.lines[0].body.position
################################################

class DynamicThing(Thing):
    body = None
    shape = None
    def __init__(self, env, position=(0., 0.), *args):
        #Be sure to be ready before registering back to the env
        self._initPhysics(*args)
        self.body.position = position
        self.shape.friction = 0.1                            #Defaults
        self.shape.elasticity = 0.5
        Thing.__init__(self, env)        
    def _initPhysics(self, *args):                           #Responsibility is on the superclasses to create a shape and body
        abstractMethod()        
    def embedInEnv(self, env):
        env.space.add(self.body, self.shape)
        # Mark the owner
        self.shape.owner = self
    def removeFromEnv(self, env):
        #del self.shape.owner
        env.space.remove(self.body, self.shape)
    @property
    def position(self):             #return start of the first line
        return self.body.position
    
#### Ball with reasonable defaults
class Ball(DynamicThing):
    def __init__(self, env, position=(0., 0.), radius = 0.25, density = 30, color = (1.,1.,1.), outline=(0.5,0.5,0.5)):
        self.color_in = color
        self.outline = outline
        self.radius = radius
        self.look_at = pymunk.Vec2d(1,0)
        DynamicThing.__init__(self, env, position, density)
 
    def _initPhysics(self, *args):
        mass = self.radius**2*3.1416 * args[0]
        inertia = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, inertia)
        self.shape = pymunk.Circle(self.body, self.radius)
    
    def updateState(self, env, dt):
        return None                                             #Do nothing
    def setLookAt(self, vec):                                   #Determines the orientation line in world space
        self.look_at = vec
    def draw(self, env):
        radius = int(env.transformDimension2Screen(self.radius))
        pos = env.transformPoint2Screen(self.body.position)
        c = to_pygame_color(self.color)
        pos = (int(pos[0]), int(pos[1]))
        pygame.draw.circle(env.surface, c, pos, int(radius))
        if self.outline != None:
            if radius >= 4:
                thick = int(max(min(radius / 12,3),1))
                if radius > 10: radius +=1
                pygame.draw.circle(env.surface, to_pygame_color(self.outline), pos, radius, thick)
                pos2 = env.transformPoint2Screen((self.look_at*self.radius).rotated(self.body.angle)+self.body.position)
                pos2 = (int(pos2[0]), int(pos2[1]))
                pygame.draw.line(env.surface, to_pygame_color(self.outline), pos, pos2, thick)
    @property             
    def color(self): return self.color_in
        

class Creature(Thing):   
    def __init__(self, env, position=(0., 0.), energy = 1.0):
        Thing.__init__(self, env)
        self.energy = energy

class Food(Ball):
    def __init__(self, env, position=(0., 0.)):
        Ball.__init__(self, env, position, 0.2, 20, (1.0,1.0,0))
        

#SensorRay querying information on a contained linespace about the environment
class SensorRay(object):
    def __init__(self, inner_radius, radius, angle):
        self.setInitParams(inner_radius, radius, angle)
    def setInitParams(self, inner_radius, radius, angle, fadeout = 0.60):
        self.inner_radius = inner_radius                                  #This space will be ignored, ray starting outside inner_radius
        self.radius = radius
        self.angle = angle
        self.fadeout = fadeout
        
        #The buffered results
        self._zero()
    def _zero(self):
        self.owner_hit = None
        self.normal_hit = None
        self.results = numpy.array([0.]*4)
        self.results[3] = 1.         
    def updateSegment(self, pos, orientation, flipy):
        direction = orientation.rotated(self.angle)                       #0 Degrees means pointing to the right
        if flipy: direction.y *= -1.
        self.start = direction * self.inner_radius + pos
        self.end = direction * self.radius + pos
    def processSegment(self, env, ignore_group):
        sq = env.space.segment_query_first(self.start, self.end, group = ignore_group)
        if sq == None: 
            self.owner_hit = None
            self.normal_hit = None
            self.results[3] = 1.
            self.results[0:3] *= self.fadeout                            #But fade out the color to give it some kind of memory
            return
        if sq.shape.owner == None: return                                #We don't know that thing...
        
        self.normal_hit = sq.n
        self.owner_hit = sq.shape.owner
        self.results[:-1] += (self.owner_hit.color-self.results[:-1])*self.fadeout
        self.results[3] = sq.t
        
    def draw(self, env):
        p1 = env.transformPoint2Screen(self.start)
        p2 = env.transformPoint2Screen(self.end)
        c = to_pygame_color(self.color_hit)
        pygame.draw.circle(env.surface, c, (int(p2[0]), int(p2[1])), 1)      #Draw dot at outermost sensorpoint
        if self.owner_hit != None:
            p3 = self.start.interpolate_to(self.end, self.distance)
            p3 = env.transformPoint2Screen(p3)
            pygame.draw.aaline(env.surface, c, p1, p3)
    @property
    def color_hit(self):
        return tuple(self.results[0:3])
    @property
    def distance(self):
        return self.results[3]

from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import * #RecurrentNetwork, LinearLayer, SigmoidLayer, FullConnection
from pybrain.rl.environments import Task, EpisodicTask

class Living(Creature):                             #Gets a brain and processing interfaces
    def __init__(self, indim, outdim, env, position=(0., 0.), energy = 1.0):
        Creature.__init__(self, env, position, energy)
        self.indim = indim
        self.outdim = outdim
        self.inbuf = numpy.array([0.]*self.indim)                   #All the sensory and of course mostly dynamic inputs to the brain
        self.outbuf = numpy.empty(self.outdim)                      #The processed and to be used output 
        
        self._createBrain()
        
    def _createBrain(self):                                         #Standard neural net, overwrite as you like for individual brains
        self.brain = buildNetwork(self.indim, int(self.indim*0.3), self.outdim, bias=True, outputbias=False, recurrent=False) #30% of indim is hiddenlayer neurons

class TaskLiving(EpisodicTask):
    def __init__(self, env, living, start_point = (0,0), max_samples = 5000):
        self.start_point = start_point
        self.living = living
        Task.__init__(self, env)
        self.max_samples = max_samples
        
    @property
    def indim(self):
        return self.living.outdim
    @property
    def outdim(self):
        return self.living.indim
    
    def reset(self):
        #self.living.body.position = self.start_point
        self.cumreward = 0
        self.samples = 0   
            
    def performAction(self, action):
        """ Execute one action. """
        #Task.performAction(self, action) #Must be done asynchronous!
        self.living.outbuf = action
        self.addReward()
        self.samples += 1
        
    def getReward(self):
        """ Compute and return the current reward (i.e. corresponding to the last action performed) """
        return abstractMethod()
    
    def getObservation(self):
        """ A filtered mapping to getSample of the underlying environment. """
        return self.living.inbuf           

    def isFinished(self):
        if self.samples >= self.max_samples: return True
        return False

class Eater(Ball, Living):
    
    ### outbuf ###
    #0: accel left, right (-1. to 1.)
    #1: jump (if >= 0.5) creature tries a jump (must be on solid ground)
    #2: reserved (speech?!)
    #3: red color
    #4: green color
    #5: blue color, each from 0. to 1.
    
    ### inbuf ###
    #0: energy
    #1: accel
    #... sensors
    decay = 0.00    
    
    max_force = 200.
    jump_impulse = 140.
    sensors_front = 3
    sensor_radius = 10.
    did_jump = False
    def __init__(self, env, position=(0., 0.), energy = 1.0, fixed_color = None):
        Ball.__init__(self, env, position, 0.25, 50, (1.,1.,1.), (0.5,0.5,0.5))
        self.fixed_color = fixed_color                          #You could fix the color manually (reducing agents' variety)
        #self.body.damping = self.drag
        #self.shape.group = get_new_collision_group_counter()      #Every collision-aware individual should get it's own id                                                   #
        
        self._setSensorRays(0, 3.1416/3, self.sensors_front)
        self.jump_time = 0.
        Living.__init__(self, 2+(2+self.sensors_front)*4, 6, env, position, energy)

    def _setSensorRays(self,start_angle, end_angle, nr):
        self.sensors = []
        self.sensors.append(SensorRay(self.radius*0.5, self.sensor_radius, -3.1416/2))   #first is always down, second is always up
        self.sensors.append(SensorRay(self.radius*0.5, self.sensor_radius,  3.1416/2))
        for i in range(nr):
            self.sensors.append(SensorRay(self.radius*0.5, self.sensor_radius,  start_angle + (end_angle-start_angle)/nr*i))
        
    def _createBrain(self):                                         #Standard neural net, overwrite as you like for individual brains
        n = RecurrentNetwork()#buildNetwork(self.indim, 18, self.outdim, bias=False, outputbias=False, recurrent=True, hiddenclass=TanhLayer)
        
        n.addInputModule(LinearLayer(self.indim, name='in'))
        n.addModule(TanhLayer(8*4, name='hidden0'))
        n.addModule(TanhLayer(12,"hidden1"))
        n.addModule(BiasUnit(name="bias"))
        n.addOutputModule(LinearLayer(self.outdim, name='out'))
        
        n.addModule(LSTMLayer(8, False, "Memory"))
        
        n.addConnection(FullConnection(n['in'], n['hidden1'])) #1
        n.addConnection(FullConnection(n['bias'], n['Memory']))
        n.addConnection(FullConnection(n['hidden1'], n['Memory']))
        n.addConnection(FullConnection(n['Memory'], n['hidden0']))
        n.addConnection(FullConnection(n['hidden0'],n['out']))
        #n.addRecurrentConnection(FullConnection(n['hidden0'], n['hidden0']))
        n.addRecurrentConnection(FullConnection(n['hidden0'], n['Memory']))
        #n.addRecurrentConnection(FullConnection(n['hidden0'], n['Memory']))
        #n.addRecurrentConnection(FullConnection(n['hidden1'],n['hidden0']))
        #n.addRecurrentConnection(FullConnection(n['hidden0'],n['hidden0']))
        
        
        n.sortModules()
        
        self.brain = n

    def updateState(self, env, dt):
        self.did_jump = False
        self.energy -= dt*self.decay
        #Keep it straight
        self.body.angular_velocity = 0.
        #Orientation
        acc = self.acceleration
        #if acc < -0.01 and self.look_at.x > 0.:   #face left, only change when relevant margin of > 0.1 is reached
        if self.body.velocity.x < -0.01:
            if self.look_at.x > 0: 
                self.setLookAt(pymunk.Vec2d(-1,0))
                for s in self.sensors[2:]: s.results[0:3] = 0               #clear color sensors
        #elif acc > 0.01 and self.look_at.x < 0: 
        elif  self.body.velocity.x > 0.01 :
            if self.look_at.x < 0:   
                self.setLookAt(pymunk.Vec2d(1,0))
                for s in self.sensors[2:]: s.results[0:3] = 0               #clear color sensors
        elif acc < 0: 
            if self.look_at.x > 0: 
                self.setLookAt(pymunk.Vec2d(-1,0))
                for s in self.sensors[2:]: s.results[0:3] = 0   
        else:
            if self.look_at.x < 0:   
                self.setLookAt(pymunk.Vec2d(1,0))
                for s in self.sensors[2:]: s.results[0:3] = 0            
        #    else: self.setLookAt(pymunk.Vec2d(1,0))
        #Acceleration
        self.body.reset_forces()
        force = self.max_force * self.acceleration
        force = pymunk.Vec2d(self.body.rotation_vector) * force
        self.body.apply_force(force)
        #Update sensors
        for s in self.sensors:
            flipy = False
            if self.look_at.x < 0: flipy = True
            s.updateSegment(self.body.position, self.look_at, flipy)
            s.processSegment(env, self.shape.group)
            s.draw(env)
        #Jump      
        if self.jump and self.jump_time > 0.3:
            if self.sensors[0].distance < 0.005*self.sensors[0].radius: 
                self.body.apply_impulse(pymunk.Vec2d(0,self.jump_impulse))
                self.did_jump = True
                self.jump_time = 0
        self.jump_time += dt
        
        self._fillInBuf()
        
    def _fillInBuf(self):
        self.inbuf[0] = self.energy
        self.inbuf[1] = self.body.velocity.x                                #Reserved
        i = 0
        for s in self.sensors:
            self.inbuf[2+i*4+0] = s.results[0]#-numpy.log(1.-s.results[0]+0.1)
            self.inbuf[2+i*4+1] = s.results[1]#-numpy.log(1.-s.results[1]+0.1)
            self.inbuf[2+i*4+2] = s.results[2]#-numpy.log(1.-s.results[2]+0.1)
            self.inbuf[2+i*4+3] = -numpy.log(s.results[3])
            i +=1
        #self.outbuf = self.brain.activate(self.inbuf)
            
    @property
    def color(self):
        if self.fixed_color == None:
            return tuple(numpy.clip((self.outbuf[3:6]+1.0)/2., 0., 1.))
        return self.fixed_color       
    @property
    def acceleration(self):
        ac = numpy.clip(self.outbuf[0], -1., 1.)
        return float(ac)  #!
    @acceleration.setter
    def acceleration(self, lr): self.outbuf[0] = lr
    
    @property
    def jump(self):
        if self.outbuf[1] < 0.5: return False
        return True
    @jump.setter
    def jump(self, j):
        if j: self.outbuf[1] = 1.0
        else: self.outbuf[1] = -1.0

def collision_func(space, arbiter, env, methodname):
    handle = True
    if hasattr(arbiter.shapes[0], "collision_receiver"):
        if hasattr(arbiter.shapes[1], "owner"):
            collidee = arbiter.shapes[1].owner
            handle = handle and arbiter.shapes[0].collision_receiver.__getattribute__(methodname)(collidee, arbiter.contacts[:])    
    if hasattr(arbiter.shapes[1], "collision_receiver"):
        if hasattr(arbiter.shapes[0], "owner"):
            collidee = arbiter.shapes[0].owner
            handle = handle and arbiter.shapes[1].collision_receiver.__getattribute__(methodname)(collidee, arbiter.contacts[:])    
    return handle
    return True

class CageEnvironment():
    
    things = []
    steps = 0
    
    def __init__(self, surface, gravity = 9.81, xdim = 200., focus = (0.,0.)):
        self.space = pymunk.Space()
        self.space.gravity = (0., -gravity)
        
        self.space.add_collision_handler(0, 0, lambda space, arbiter, env: collision_func(space, arbiter, env, "receiveOnBegin"), None, None, lambda space, arbiter, env: collision_func(space, arbiter, env, "receiveOnSeparate"), self)
        #Limit the callbacks a little bit
        self.surface = surface
        self.setViewPort(xdim, focus)
 
    def setViewPort(self, xdim, focus):
        if xdim != None: self.scale = self.surface.get_width() / xdim
        self.offset_x = self.surface.get_width() / 2. - focus[0]*self.scale
        self.offset_y = self.surface.get_height() / 2. + focus[1]*self.scale     
    def transformPoint2Screen(self, point):
        return point[0]*self.scale + self.offset_x, -point[1]*self.scale + self.offset_y
    def transformScreen2Point(self, screenpoint):
        return (screenpoint[0]-self.offset_x) / self.scale, (screenpoint[1]-self.offset_y) / self.scale
    def transformDimension2Screen(self, dim):
        return dim * self.scale

    def embedThing (self, th):              #Creatures and other things usually embed themselves upon construction
        if self.things.count(th) > 0: return self.things.index(th)
        self.things.append(th)
        th.embedInEnv(self)
        return len(self.things)-1
    def removeThing(self, th):
        self.things.remove(th)             #... and remove themselves (from the darwin pool :) if necessary
        th.removeFromEnv(self)
        
    def processTimeStep(self, timestep):
        #Update all Things' states
        for thing in self.things:
            thing.updateState(self, timestep)
        #Bring physics forward
        self.space.step(timestep)
        
    def drawThings(self):
        for thing in self.things: thing.draw(self)
                    

class TaskAvoidRed(TaskLiving):
    min_reward = 0.
    success = False
    failure = False
    
    samples_success_hysteresis = 15
    def getReward(self):
        #Error calculation
        ib = self.living.inbuf
        e = 0
        reds = ib[2] * (2-ib[5])  + (ib[6] + ib[10] + ib[14] + ib[18]) / 2
        reds = ib[2] * (ib[5]) + (ib[6]*(ib[9]) + ib[10]*(ib[13]) + ib[14]*(ib[17]) + ib[18]*(ib[21])) / 2
        e = -reds*2
        #Energy decrease and reward calculation
        self.living.energy += (min(e/5000,0.02))/2#+0.0001
        reward = e*30 + 25
        self.min_reward = min(reward,self.min_reward)
        
        if reward > 20 and self.success == False:
            self.countdown()  #We have met a successful condition, start counting
            self.failure = False
            self.success = True
        #if reward < -250. and self.failure == False: 
            #self.countdown()
            #self.living.energy -= 0.5
            #self.success = False
            #self.failure = True
        return reward                         #+ a fixed value to retain or give it  some "braveness" !
    
    def countdown(self):
        self.max_samples = self.samples_success_hysteresis
        self.samples = 0
    def reset(self):
        TaskLiving.reset(self)
        self.success = False
        self.failure = False
        self.min_reward = 0.
        self.max_samples = 10000

from cage2 import CollisionReceiver
class TaskEat(TaskLiving, CollisionReceiver):
    success = False
    failure = False    
    def __init__(self, env, living):
        TaskLiving.__init__(self, env, living)
        CollisionReceiver.__init__(self, living.shape)
        
        self.living.decay = 0.01
        self.collected = 0.
        
    def receiveOnBegin(self, thing, contacts):
        if isinstance(thing, Food):
 #           self.env.removeThing(thing)
            self.living.energy += 0.1
            self.collected += 1.
            self.countdown()
            return False 
        return True
    
    def countdown(self):
        self.max_samples = 10
        self.samples = 0
            
    def getReward(self):
        reward = 0.0
        for s in self.living.sensors:
            if isinstance(s.owner_hit, Food):
                reward += 0.0# * (1. - s.results[3])
        if isinstance(self.living.sensors[0].owner_hit, Food) and self.living.did_jump:
            reward -= 1
        
        #reward -= 0.1
        reward += 100 * self.collected 
        self.collected *= 0.8
        return reward*100.
    
    def reset(self):
        TaskLiving.reset(self)
        self.success = False
        self.failure = False
        self.max_samples = 100000

class TaskAdoptColorDown(TaskLiving):
    max_samples = 100
    def getReward(self):
        reward = 0
        err = 0
        ib = self.living.inbuf     
        
        v2 = (ib[1]**2)
        if v2 <  0.5**2:
            err += (0.5*2-ib[1])**2 - 0.5**2
        else: reward += ib[1]**2 - 0.5**2
        
        r, g, b = ib[2], ib[3], ib[4]        # color down
        c = self.living.color
        dc = (r-c[0])**2 + (g-c[1])**2 + (b-c[2])**2
        if dc > 0.5**2:
            err += dc 
        else: reward += dc                  
        return (reward-err)*50.
        
    
