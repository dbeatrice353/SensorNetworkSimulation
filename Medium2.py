
'''
The Medium Class
----------------

David Beatrice
11/7/2015

This class simulates the physical medium employed in wireless information transmission.
- In essense, it allows a group of nodes to propagate signals, listen and receive signals.
- It manages collisions and propagation delays.
- It works by maintaining three tables: signals, nodes, and signal_node_pairs.
  With each time step, a medium object makes multiple passes over these tables to
  determine
      - Which signals are currently propagating
      - Which signals are in range of which nodes
      - Which signals are colliding where


The "tables" are (basically) of the following form:

signals
    signal_id
    source_x
    source_y
    radius
    time
    packet
    
nodes
    node_id
    x
    y
    radius

signals_to_nodes
    node_id
    signal_id
    collision
    
'''


class Medium:
    def __init__(self):
        self.signals = []               # current signals in the medium
        self.nodes = []                 # current nodes in the meduim
        self.signal_node_pairs = []     # signal/node pairs: a signal and a node that both exists at the same physical point.
        self.signal_id_counter = 0
        self.signal_node_pair_id_counter = 0

    def connect_to_the_nodes(self,nodes):
        self.register_nodes(nodes)      # create node records

    def get_node_by_id(self,node_id):
        nodes = [node for node in self.nodes if node['id'] == node_id]
        if len(nodes) == 1:
            return nodes[0]
        else:
            raise Exception("Zero or multiple nodes have that ID")

    def get_signal_by_id(self,signal_id):
        signals = [signal for signal in self.signals if signal['id'] == signal_id]
        if len(signals) == 1:
            return signals[0]
        else:
            raise Exception("Zero or multiple signals have that ID")

    def get_signal_node_pair_by_both_ids(self,signal_id,node_id):
        pairs = [pair for pair in self.signal_node_pairs if pair['signal_id'] == signal_id and pair['node_id'] == node_id]
        if len(pairs) > 1:
            raise Exception("Zero or multiple signal/node pairs have those IDs")
        elif len(pairs) == 1:
            return pairs[0]
        else:
            return None

    def get_signal_node_pairs_by_node_id(self,node_id):
        return [pair for pair in self.signal_node_pairs if pair['node_id'] == node_id]
        
    def delete_signal_node_pairs_by_signal_id(self,signal_id):
        self.signal_node_pairs = [pair for pair in self.signal_node_pairs if pair['signal_id'] != signal_id]
        
    def register_nodes(self,nodes):
        # initially register all nodes.
        for node in nodes:
            self.nodes.append({'id':node.id,'x':node.x,'y':node.y,'radius':node.radius})
        
    def propagate(self,packet):
        # propagate a signal accross the medium 
        sender_node = self.get_node_by_id(packet['sender_id'])
        self.signals.append({'packet':packet,
                             'node_id':sender_node['id'],
                             'source_x':sender_node['x'],
                             'source_y':sender_node['y'],
                             'radius':sender_node['radius'],
                             'id': self.signal_id_counter,
                             'time':4}) # propegation/receive delay. Add 1 because its decremented in the initial update.
        self.signal_id_counter += 1

    def create_signal_node_pairs(self):
        # loop over all signals and nodes.
        for signal in self.signals:
            signal_id = signal['id']
            for node in self.nodes:
                node_id = node['id']
                # if a signal and node are in range of eachother...
                if self.in_range(signal,node):
                    # check if we have recorded the fact.
                    signal_node_pair = self.get_signal_node_pair_by_both_ids(signal_id,node_id)
                    if not signal_node_pair:
                        self.signal_node_pairs.append({'signal_id':signal_id,'node_id':node_id,'collision':False,'id':self.signal_node_pair_id_counter})
                        self.signal_node_pair_id_counter += 1

    def update_propagation_counters(self):
        # Propagation takes 3 time steps.
        # Each signal has a counter to track it's propagation progress.
        # Signals dissapear after propagating (timers reach 0).
        updated_signals = []
        for signal in self.signals:
            signal['time'] -= 1
            if signal['time'] > 0:
                updated_signals.append(signal)
            else:
                self.delete_signal_node_pairs_by_signal_id(signal['id'])
        self.signals = updated_signals

    def record_collisions(self):
        # Mark each signal/node pair according to whether the node can successfully receive the full signal.
        # If a signal collides with another signal at the location of the node, at any given time,
        # then the signal can't be received successfully.
        for node in self.nodes:
            pairs_in_range = self.get_signal_node_pairs_by_node_id(node['id'])
            # if there are multiple signals at this location during this timestep: collision!
            if pairs_in_range and len(pairs_in_range) > 1:
                for pair in pairs_in_range:
                    self.signal_node_pairs.remove(pair) # remove the old record.
                    pair['collision'] = True            
                    self.signal_node_pairs.append(pair) # add the new record.
                                                         
    def in_range(self,signal,node):
        # determine if a signal is in range of a node
        return (signal['source_x'] - node['x'])**2 + (signal['source_y'] - node['y'])**2 <= signal['radius']**2

    def update(self):
        self.create_signal_node_pairs()
        self.record_collisions()
        self.update_propagation_counters()
        #print "----------------------------------------------------------------------"
        #for each in self.signals:
            #print each['packet']

    def listen(self,node_id):
        pairs_in_range = self.get_signal_node_pairs_by_node_id(node_id)
        if pairs_in_range:
            # If more than one signal is in range, or only one signal is in range
            # but a collision previously occured obscuring part of that packet...
            if len(pairs_in_range) > 1 or pairs_in_range[0]['collision'] == True:
                return 'BUSY'
            else:
            # Otherwise, there's only one signal in range and its clean and clear.
            # if the signal is finished transmitting, then return it.
            # NOTE: to simplify the model, a receiver doesnt know it's receiving a message until that message is fully transmitted.
            # So, The medium returns 'BUSY' until the message is fully transmitted.
                signal = self.get_signal_by_id(pairs_in_range[0]['signal_id'])
                if signal['time'] == 1:
                    return signal['packet']
                else:
                    return 'BUSY'
        else:
            return 'CLEAR'
                
    def print_signal_node_pairs(self):
        # for debugging
        for pair in self.signal_node_pairs:
            print pair

    def print_nodes(self):
        # for debugging
        for node in self.nodes:
            print node

    def print_signals(self):
        # for debugging
        for signal in self.signals:
            print signal




    


        
        


        
    
        

        
    
        
        
