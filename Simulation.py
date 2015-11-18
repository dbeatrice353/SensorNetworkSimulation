"""

Simulation Script (top level file)
-----------------

David Beatrice
11/14/2015


This script drives the simulation of the in-network data aggregation.


"""


from MultipleAccess import MultipleAccess
from Medium2 import Medium
from Node import Node, Edges
import sys, pygame
import random
import time


# colors for pygame
BLACK =  (  0,   0,   0)
WHITE =  (255, 255, 255)
BLUE =   (  0,   0, 255)
GREEN =  (  0, 255,   0)
RED =    (255,   0,   0)
YELLOW = (255, 255,   0)

def render_building():
    pygame.draw.rect(screen,BLUE,(850,250,100,200),0)

# Initialize the game engine
pygame.init()
size = [1000,600]
screen = pygame.display.set_mode(size)

# designate an output file
output_file = 'output.txt'
# clear the file
open(output_file,'w').close()

for each in range(30):
    print each
    
    # create nodes
    nodes = []
    for i in range(0,10):
        for j in range(0,10):
            if random.random() <= .62:
                node_id = str(i) + '_' + str(j)
                node = Node(i,j,node_id)
                node.set_output_file(output_file) # give it the output file 
                nodes.append(node)

    # mark the start of one simulation
    with open(output_file,'a') as f:
        f.write('#'+str(len(nodes))+'\n')
    
    # create a data sink
    sink = Node(10,5,'10_5')
    
    # create the medium
    medium = Medium()

    # point the medium to the nodes
    medium.connect_to_the_nodes(nodes + [sink])
    
    # point the nodes to the medium
    for node in nodes:
        node.connect_to_the_medium(medium)

    # point the sink to the medium
    sink.connect_to_the_medium(medium)
    # set as sink node (it initiates the process)
    sink.set_as_sink()

    # record and render edges
    edges = Edges(screen)

    # simulation loop
    while True:
        
        edges.reset()
        # pygame inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
                
        # parking lot node updates
        output = sink.update()
        for node in nodes:
            node.update()
            edges.record_edge(node)
        medium.update()
        
        # visual updates 
        screen.fill(BLACK)
        render_building()
        sink.render(screen)
        for node in nodes:
            node.render(screen)
        edges.render(screen)
            
        pygame.display.update()

        if output:
            break
    
pygame.quit()

