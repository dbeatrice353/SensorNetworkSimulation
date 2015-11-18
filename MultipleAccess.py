'''

MultipleAccess Class
----------------------

David Beatrice
11/8/2015


An implementation of p-Persistant CSMA. Each node in
the network has a MultipleAccess object which provides
a simple send_message() and receive_message() interface
to that node. The MultipleAccess object manages problems
like listening to the medium, running a backoff counter,
transmitting messages, transmitting ACKs, retransmission, etc.


'''
import random
import copy
from Medium2 import Medium

class MultipleAccess:
    def __init__(self,node_id):
        self._node_id = node_id             # the id of the node that owns this object/instance
        self._state = 'QUEUE_IS_EMPTY'      # the state of the FSM
        self._incoming_queue = []           # a queue of incoming packets
        self._outgoing_queue = []           # a queue of outgoing packets
        self._incoming_ack = None           # the holder for an incoming ACK
        self._contention_window = 3         # the contention window for CSMA
        self._ack_wait = 200                # the amount of time the system should wait for expected ACKs before assuming failure.
        self._backoff_counter = 0           # the backoff counter for CSMA
        self._ack_wait_counter = 0          # a counter for when the system is waiting for an ACK(s)
        self.p = 0.05                       # the "p" in p-persistant CSMA: transmit with a probability of p.
        self._expected_acks = []            # a list of the ids of nodes from which we're expecting ACKs
        self.save = []
        self.medium = None                  # a pointer to the medium

    def connect_to_the_medium(self,medium):
        # point to the medium
        self.medium = medium

    #NOTE send_message is 1 of the 2 important interface methods
    #------------------------------------------------------------
    def send_message(self,message):
        # work around a design flaw in the packet
        if type(message['receiver_id']) == int:
            message['receiver_id'] = [message['receiver_id']]
        # check for errors
        self._validate_packet(message)
        # enqueue
        self._outgoing_queue.insert(0,message)

    #NOTE receive_message is 1 of the 2 important interface methods
    #--------------------------------------------------------------
    def receive_message(self):
        if self._incoming_queue:
            # dequeue
            return self._incoming_queue.pop()
        else:
            return None

    def _send_high_priority_message(self,message):
        # place a packet at the front of the queue.
        # (namely for sending ACKS)
        self._outgoing_queue.append(message)

    def _validate_packet(self,packet):
        # This is not completely air-tight.
        if 'mode' not in packet.keys():
            raise Exception("packet missing field: mode")
        if 'sender_id' not in packet.keys():
            raise Exception("packet missing field: sender_id")
        if 'receiver_id' not in packet.keys():
            raise Exception("packet missing field: receiver_id")
        if packet['mode'] not in ['broadcast','multicast','unicast']:
            raise Exception("invalid mode")
        if not type(packet['sender_id']) == str:
            raise Exception("invalid datatype for sender_id ")
        if packet['mode'] != 'broadcast' and packet['receiver_id'] == None:
            raise Exception("receiver_id(s) required")
        if type(packet['receiver_id']) != list:
            raise Exception('receiver_id must be a list of ints')

    def _bernoulli_trial(self):
        # p-persistant sends when the channel is clear with a probability p, using this as a trial.
        return random.random() < self.p

    def _set_backoff_counter(self):
        # if the medium is busy, set the back off counter and wait for it to run out.
        self._backoff_counter = random.randint(0,self._contention_window)

    def _set_ack_wait_counter(self):
        # This timer places a limit on how long we should wait for an ACK before retransmitting. 
        self._ack_wait_counter = self._ack_wait

    def _is_a_packet(self,sample):
        # determine if what we've received over the network is a packet.
        # (Packets are dictionaries. Busy and clear signals are strings)
        return type(sample) == dict

    def _listen(self):
        # The medium's listen method will return either 'BUSY', 'CLEAR', or an actual packet.
        return self.medium.listen(self._node_id)

    def _transmit(self,packet):
        # ..the packet becomes a signal...
        signal = packet
        self.medium.propagate(signal)

    def _save_receiver_ids(self, packet):
        # In the case of a multicast or unicast, save the receiver
        # id(s) from a sent packet so that we know who should be sending ACKs.
        self._expected_acks = packet['receiver_id']


    def _is_for_me(self,packet):
        # determine if a packet is intended for me
        if packet['mode'] == 'broadcast' and packet['sender_id'] != self._node_id:
            return True
        elif self._node_id in packet['receiver_id']:
            return True
        else:
            return False

    def _requires_ack(self,packet):
        # Determine if the sender of a packet we've received requires an ACK
        return not packet['mode'] == 'broadcast' and not packet['payload'] == 'ACK'

    def _make_ack(self,receiver_id):
        # Create an ACK packet for a given receiver.
        return {'sender_id':self._node_id,                  # sender id (the node that owns this multiple access instance)
                'receiver_id':[receiver_id],                # the id(s) of the receiver(s)
                'payload':'ACK',                            # the message/payload
                'mode':'unicast'}                           # the mode (broadcast, multicast, unicast)

    def _outgoing_message_pending(self):
        # STATE: outgoing message pending
        if self._backoff_counter == 0:                              # if the backoff counter has run out...
            medium_sample = self._listen()                          # ... then listen to the medium.
            if medium_sample == 'CLEAR':                            # if the medium is clear...
                if self._bernoulli_trial():                         # ... then perform a random trial
                    packet = self._outgoing_queue[-1]               # take the next message from the queue. But dont dequeue, incase we need to re-transmit later.
                    self._transmit(packet)                          # if the random trial is successful, then send!
                    if self._requires_ack(packet):                  # if the transmission was a multicast or unicast and not an ack...
                        self._save_receiver_ids(packet)             # ... make note of who should be sending ACKs.
                        self._set_ack_wait_counter()
                        self._state = 'WAITING_FOR_ACK'             # ... then wait for the ACK
                    else:
                        self._outgoing_queue.pop()
                        if not self._outgoing_queue:                # Otherwise, if the queue is empty... 
                            self._state = 'QUEUE_IS_EMPTY'          # ... then just wait.
            else:
                self._set_backoff_counter()                         # ... otherwise, set the backoff counter and keep waiting.
        else:
            self._backoff_counter -= 1                              # ... keep counting down the backoff counter.
    '''
    def _waiting_for_ack(self):
        if self._ack_wait_counter != 0:
            if self._expected_acks:                                 # if we're expecting ACKs... 
                if self._incoming_ack:                              # if there's an incoming ACK...
                    sender_id = self._incoming_ack['sender_id']         
                    if sender_id in self._expected_acks:            # if the incoming ack is one of the ones we've been expecting...
                        self._expected_acks.remove(sender_id)       # ... we needn't wait for that ACK anymore.
                        self._incoming_ack = None                   # ... clear the ACK holder.
                self._ack_wait_counter -= 1                         # keep counting down.
            else:
                self._outgoing_queue.pop()                          # dequeue that message because it was received.
                self._ack_wait_counter = 0                          # reset the ACk wait counter.
                if self._outgoing_queue:                            # exit this state.
                    self._state = 'OUTGOING_MESSAGE_PENDING'
                else:
                    self._state = 'QUEUE_IS_EMPTY'
        else:
            if self._expected_acks:                                 # if time ran out, and we're still expecting ACKs...
                self._state = 'OUTGOING_MESSAGE_PENDING'            # assume failure, and retransmit.
            else:                                                   # otherwise, success.
                self._outgoing_queue.pop()                          # dequeue that message because it was received.
    '''
    
    def _waiting_for_ack(self):
        # STATE: waiting for ACK
        if self._expected_acks and self._ack_wait_counter != 0:     # we're expecting ACKs and time hasn't run out.
            if self._incoming_ack:
                sender_id = self._incoming_ack['sender_id']
                if sender_id in self._expected_acks:
                    self._expected_acks.remove(sender_id)
                    self._incoming_ack = None
            self._ack_wait_counter -= 1
        elif self._expected_acks and self._ack_wait_counter == 0:   # we're expecting ACKs but time has run out.
            self._expected_acks = []
            self._state = 'OUTGOING_MESSAGE_PENDING'
        elif not self._expected_acks:                               # we're expecting no more ACKS and time doesn't matter.
            self._ack_wait_counter = 0
            self._outgoing_queue.pop()
            if self._outgoing_queue:
                self._state = 'OUTGOING_MESSAGE_PENDING'
            else:
                self._state = 'QUEUE_IS_EMPTY'

    def _undefined_state(self):
        raise Exception('undefined state!')

    def _handle_incoming_packets(self):
        medium_sample = self._listen()
        if self._is_a_packet(medium_sample):
            if self._is_for_me(medium_sample):
                packet = copy.deepcopy(medium_sample)
                if packet['payload'] == 'ACK':
                    self._incoming_ack = packet
                else:
                    if self._requires_ack(packet):
                        ack_packet = self._make_ack(packet['sender_id'])
                        self._send_high_priority_message(ack_packet)
                    self._incoming_queue.insert(0,packet) 

    def _handle_outgoing_packets(self):
        if self._state == 'QUEUE_IS_EMPTY':
            # check if there's a packet in the outgoing queue.
            if self._outgoing_queue:
                self._state = 'OUTGOING_MESSAGE_PENDING'
                
        elif self._state == 'OUTGOING_MESSAGE_PENDING':
            self._outgoing_message_pending()
            
        elif self._state == 'WAITING_FOR_ACK':
            self._waiting_for_ack()
            
        else:
            self._undefined_state()
        
    def update(self):
        # Receive any incoming messages
        self._handle_incoming_packets()
        # Send any outgoing messages (this is the state machine).
        self._handle_outgoing_packets()

    def print_info(self):
        print "node_id: ", self._node_id
        print "state: ", self._state
        print "incoming_ack: ", self._incoming_ack
        print "contention_window: ", self._contention_window
        print "ack_wait: ", self._ack_wait
        print "backoff_counter: ", self._backoff_counter
        print "ack_wait_counter: ", self._ack_wait_counter
        print "p: ", self.p
        print "expected_acks: ", self._expected_acks
        for each in self._incoming_queue:
            print "incoming_queue: ", each
        for each in self._outgoing_queue:
            print "outgoing_queue: ", each

        
