In-Network Data Aggregation: A Parking Lot Application
------------------------------------------------------
Date: 11/18/2015
Programmer: David Beatrice 
Algorithm Design Collaborators: David Beatrice, Aakash Mohapatra, Robin Wu

Dependencies: Python 2.7, PyGame
To run: python Simulation.py

This program simulates the aggregation of vehicle position data for the cars in a parking lot. The simulation consists of 3 main classes:

a) Medium: A discrete event simulator for single-channel wireless transmission. This singleton class maintains tables of nodes, signals, and node-signal pairs in order to determine which signals reach which nodes, simulate propagation delays, and identify when a collision has occurred.
b) MultipleAccess: An implementation of p-Persistent CSMA. Each node in the network has a MultipleAccess object which provides a simple send_message() and receive_message() interface to that node. The MultipleAccess object manages problems like listening to the medium, running a backoff counter, transmitting messages, transmitting ACKs, retransmission, etc. The design file for this class’s functional behavior is attached.
c) Node: The node is the highest level entity that handles the recursive construction of the tree topology and the data aggregation. 

