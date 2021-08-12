====================
Donkey Car Evaluator 
====================

:Package: dcevaluator

Automatic evaluation of the model that drives the car


Description
===========

This program will evaluate the performance of a model by running it a number of times in a simulator 
and displaying the results obtained (number of laps, time taken, off road, timout, ...)

Prerequisite
============
This program has been developed for **Python 3.9**.
The installation uses **PyPi**.

Installation
============
0. Git clone the project

**In the repository :**

1. `make install`
2. `source ./venv/bin/activate`
3. `python src/dcevaluator/launch.py MODEL_PATH` by replacing MODEL_PATH with the path of the model to be tested.

NOTE
----
The program reads the recorded models in a very particular way (records the source code of the wrapper and the weights of the neural network).

It may be necessary to adapt the Brain class to communicate with the Evaluator.

This will be the subject of the next improvement.

Parameters
==========

    :--evaluation_name: Name of the evaluation
    :--host: host to connect to a server like ip address with string
    :--port: port to connect to a server with int
    :--evaluation_scene: scene to load before the evaluation


EVALUATOR
---------
    :--nbr_turns_limit: limit number of turns from which the evaluation is stopped (to avoid that the car drives to infinity).
    :--nbr_epochs: number of epochs, i.e. the number of times the experiment is reproduced. This prevents us from evaluating once and having surprising results on a stroke of luck.
    :--max_time_to_wait: waiting time for a controller ready to drive the car.
    :--delay_between_check_interval: delay between each verification interval when waiting for a controller to be ready.
    :--delay_before_launch_car: delay time after a scene reset before launching the car. This allows us to be sure that all components are loaded before starting the evaluation.
    

CLIENT
------
    :--poll_socket_sleep_sec: time to sleep before polling socket
    :--buffer_message_size_read: number of bits to read into the socket
    :--delatime_to_compute_fps: deltatime between computation of the FPS
    :--margin_before_car_leaving_road: distance from the center of the road at the active node to the car. Maximum value from which it can be considered that the car has left the road
    :--deltatime_min_between_turns: minimum time interval between two turns from which we can count a turn (incrementation)
    :--node_after_start_detection_turn: node from which we can possibly count a turn. (To avoid false positives on the rest of the road)
    :--deltatime_max_between_nodes: Maximum time interval to travel the distance between two nodes. If the vehicle takes too long, it is probably stuck somewhere but not far enough off the road to be considered 'off road'.
    :--deltatime_max_after_driving_to_reach_first_node: Maximum time interval for the car to reach a node if its default settings have not been changed when the car is launched. This is the case when the car moves before the real start and the evaluator has not captured this departure because the simulator does not respond.

CONTROLLER
----------
    :--buffer_requests_size: Size of buffer of requests