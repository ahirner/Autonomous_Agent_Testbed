Dependencies
============
* pybrain
* pygame
* pymunk
* scipy (minor)
* pylab (minor)

Running
=======
To run the baseline scenario, refer to test.py. This is where an environment like in this recording is generated: https://www.youtube.com/watch?v=XvPdLdCOVGk

Functional Description
======================
This is from a simple AI project using the excellent pybrain (http://pybrain.org) library and pymunk 2D physics (http://www.pymunk.org). The reason why pybrain is excellent for this task is because it allows to configure and layer numerous ANN building blocks into a more or less functioning whole. With these possibilities it's quite straigthforward to test different topologies on performance and characteristics. This particular agent e.g., consists of linear input layers, a bias unit, two feed forward layers, an LSTM layer for 'memory', output layer and several connections between them. One of them being recurrent, that is looking back one tick in time to facilitate behavioral patterns over time. Also, feedback connections have been tried to further enhance this aspect.
As it turns out, after some amount of explorative reinforcement learning (til 1:00), the eater recognizes certain advantageous patterns. E.g. if it senses the yellow food in front, it accelerates towards it, if it sees a red wall it reverses the direction (after some hesitation) and if it sees the blue ball it jumps (for a non obvious reason, maybe just to avoid getting stuck). 
In general all the behavior is quite trivial, or in a sense stubborn. Repeating actions without much contingency of prior input. I.e., 'consciousness' is maybe less than a second.

The inputs are as follows: rays around the agent reporting back the distance and color they sense (also visualised in the video). In this world, yellow signifies the bits of food which act as a reward as soon as they get in contact with the agent.
The scalar outputs are acceleration to the left/right and scalar with a 0.5 threshold for jumping (if it is near ground).
