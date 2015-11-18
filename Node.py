"""

Node Class
----------

David Beatrice
11/12/2015

The class represents the network node, as the highest level entity.
It handles the recursive construction of the tree topology and the
data aggregation.

"""

from MultipleAccess import MultipleAccess
from Medium2 import Medium
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


class Node:
    
    # protocol messages:
    ANNEX_FREE_NODES = "If you have no parent node yet, then I am your parent node." # broadcast
    ACK_OF_PARENT = "I am your child node."                                          # unicast
    GROW_COMMAND = "Annex any free nodes."                                           # unicast
    DATA_TO_PARENT = "DATA"                                                          # unicast: "DATA,233,44,234,12,456"  

    # states
    WAIT_TO_BE_ANNEXED = 1
    WAIT_FOR_GROW_COMMAND = 2
    GROW = 3
    SEND_GROW_COMMANDS = 4
    DO_NOTHING = 5
    
    def __init__(self,x,y,node_id):
        # unique identifier
        self.id = node_id
        # physical position
        self.x = x
        self.y = y
        # transmission radius
        self.radius = 2
        # access to the network
        self.network_interface = MultipleAccess(node_id)
        # pointers
        self.parent_id = None
        self.child_ids = []
        # state element
        self.state = Node.WAIT_TO_BE_ANNEXED
        # a timer
        self.timer = 0
        # a timeout value for listening for responses to the grow broadcast.
        self.grow_timeout = 750 # timesteps
        # a timeout value for listening for a data response from a child. 
        self.child_response_timeout = 99999999999 #timesteps
        # save the id of thie child node from whom we're currently expecting a data response
        self.selected_child = None
        # data received from child nodes
        self.received_data = ''
        # sample id
        self.sample_id = None
        # is this the data sink node?
        self.i_am_the_data_sink = False
        # screen positions
        self.screen_position = ((self.x + 1)*80,(self.y + 2)*50)
        self.parent_screen_position = None
        # a file pointer to log data
        self.output_file = None

    def set_as_sink(self):
        # set this node to be the data sink node.
        self.i_am_the_data_sink = True
        self.sample_id = 1
        self.grow_enter()

    def set_output_file(self,output_file):
        # set the file pointer
        self.output_file = output_file

    def ids_sent(self):
        # there's an extra comma in the ids string.
        return 'ids_sent_' + str(self.received_data.count(',') + 1)

    def log_event(self,event):
        if self.output_file:
            with open(self.output_file,'a') as fp:
                fp.write(self.id + '\t' + event + '\n')
    
    def set_parent_id(self,parent_id):
        self.parent_id = parent_id
        [x,y] = map(int, parent_id.split('_'))
        self.parent_screen_position = ((x + 1)*80,(y + 2)*50)

    def connect_to_the_medium(self,medium):
        # this is one part of the bidirectional pointer between the node and the medium.
        self.network_interface.connect_to_the_medium(medium)

    def save_data(self,payload):
        # save the node ids recieved from a child node.
        data = payload.replace('DATA','')
        self.received_data += data

    def send_data_to_parent(self):
        data = 'DATA' + self.received_data + ',' + str(self.id)
        message = {'sender_id':self.id,'receiver_id':[self.parent_id],'payload':data,'mode':'unicast'}
        self.network_interface.send_message(message)
        self.log_event(self.ids_sent())
        
    def wait_to_be_annexed_do(self,message):
        # listen for the broadcast from a leaf node. 
        if message and message['payload'] == Node.ANNEX_FREE_NODES and message['sample_id'] != self.sample_id:
            self.wait_to_be_annexed_exit(message['sender_id'],message['sample_id'])

    def wait_to_be_annexed_exit(self,parent_id,sample_id):
        # remeber what sampling this is to prevent double sampling
        self.sample_id = sample_id
        # become the broadcasting node's child.
        self.set_parent_id(parent_id)
        # send an acknowledgement to the broadcasting node.
        message = {'sender_id':self.id,'receiver_id':[self.parent_id],'payload':Node.ACK_OF_PARENT,'mode':'unicast'}
        self.network_interface.send_message(message)
        self.log_event('ack_of_parent')
        # state transition
        self.state = Node.WAIT_FOR_GROW_COMMAND

    def wait_for_grow_command_do(self,message):
        if message and message['sender_id'] == self.parent_id and message['payload'] == Node.GROW_COMMAND:
            self.grow_enter()
            
    def grow_enter(self):
        self.state = Node.GROW
        # broadcast to free nodes
        message = {'sender_id':self.id,'receiver_id':[],'payload':Node.ANNEX_FREE_NODES,'mode':'broadcast','sample_id':self.sample_id}
        self.network_interface.send_message(message)
        self.log_event('broadcast')
        # limit the window of time to listen for responses.
        self.timer = self.grow_timeout
        
    def grow_do(self,message):
        # listen for responses to the broadcast, establishing that the senders are this node's children.
        if message and message['payload'] == Node.ACK_OF_PARENT and message['mode'] == 'unicast':
            if message['sender_id'] not in self.child_ids:
                self.child_ids.append(message['sender_id'])
        # keep counting down
        self.timer -= 1
        if self.timer == 0:
            # exit state
            self.grow_exit()

    def grow_exit(self):
        if self.child_ids:
            self.send_grow_commands_enter()
        else:
            self.send_data_to_parent()
            self.state = Node.WAIT_TO_BE_ANNEXED
            self.parent_id = None

    def send_grow_commands_enter(self):
        # send a command to each of the child nodes instructing them to annex free nodes.
        self.state = Node.SEND_GROW_COMMANDS
        # the ids should be in random order already.
        if self.child_ids:
            self.selected_child = self.child_ids[-1]
            message = {'sender_id':self.id,'receiver_id':[self.selected_child],'payload':Node.GROW_COMMAND,'mode':'unicast'}
            self.network_interface.send_message(message)
            self.log_event('grow_command')
            self.timer = self.child_response_timeout
        else:
            self.send_grow_commands_exit()

    def send_grow_commands_do(self,message=None):
        # listen for the data response from each child node
        if message and message['payload'].startswith(Node.DATA_TO_PARENT) and message['sender_id'] == self.selected_child:
            self.save_data(message['payload'])
            self.child_ids.remove(self.selected_child)
            self.send_grow_commands_exit()
        self.timer -= 1
        if self.timer == 0:
            # exit state
            self.send_grow_commands_exit()

    def send_grow_commands_exit(self):
        # are there more child nodes from whom we need data?
        if self.child_ids:
            # if so, contact them
            self.send_grow_commands_enter()
        else:
            if self.i_am_the_data_sink:
                self.state = Node.DO_NOTHING
            else:
                # otherwise, send the accumulated data to the parent node.
                self.send_data_to_parent()
                # reset
                self.timer = 0
                self.selected_child = None
                self.parent_id = None
                self.received_data = ''
                self.state = Node.WAIT_TO_BE_ANNEXED
            
    def handle_stray_ack_of_parenthood(self,message):
        #
        #
        if message and message['payload'] == Node.ACK_OF_PARENT and message['mode'] == 'unicast':
            if self.child_id: 
                self.child_ids.insert(0,message['sender_id'])
                
    def update(self):
        # listen to the network
        message = self.network_interface.receive_message()
        # an ad-hoc fix to a systemic issue.
        #self.handle_stray_ack_of_parenthood(message)
        # state machine
        if self.state == Node.WAIT_TO_BE_ANNEXED:
            self.wait_to_be_annexed_do(message)
        elif self.state == Node.WAIT_FOR_GROW_COMMAND:
            self.wait_for_grow_command_do(message)
        elif self.state == Node.GROW:
            self.grow_do(message)
        elif self.state == Node.SEND_GROW_COMMANDS:
            self.send_grow_commands_do(message)
        else: # do nothing because the sink has the data.
            return True
        # update the multiple access machine
        self.network_interface.update()


    def render(self,screen):
        # Draw the node. The color depends on the state.
        if self.state == Node.WAIT_TO_BE_ANNEXED:
            color = BLUE
        elif self.state == Node.WAIT_FOR_GROW_COMMAND:
            color = YELLOW
        elif self.state == Node.GROW:
            color = GREEN
        elif self.state == Node.SEND_GROW_COMMANDS:
            color = RED
        else:
            color = WHITE
        pygame.draw.circle(screen, color, self.screen_position, 10, 0)


class Edges:
    #
    # This class was a last minute fix to the problem
    # of drawing edges between nodes. For each time step, you
    # have to loop over all the nodes, calling record_edge(node)
    # on each node. Then, to render the edges on the screen,
    # just call render().
    # 
    def __init__(self,screen):
        self.edges = []
        self.screen = screen

    def record_edge(self,node):
        if node.parent_id:
            self.edges.append([node.screen_position,node.parent_screen_position])

    def reset(self):
        self.edges = []

    def _render_edge(self,edge):
        pygame.draw.line(self.screen, WHITE, edge[0], edge[1], 1)

    def render(self,screen):
        map(self._render_edge,self.edges)


