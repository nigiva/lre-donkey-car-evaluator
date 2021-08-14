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
The installation uses **PyPi** and **virtual Env (venv)**.

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

    :--evaluation-name: Name of the evaluation
    :--host: host to connect to a server like ip address with string
    :--port: port to connect to a server with int
    :--evaluation-scene: scene to load before the evaluation
    :--log-path: the path of the generated log file


EVALUATOR
---------
    :--nbr-turns-limit: limit number of turns from which the evaluation is stopped (to avoid that the car drives to infinity).
    :--nbr-epochs: number of epochs, i.e. the number of times the experiment is reproduced. This prevents us from evaluating once and having surprising results on a stroke of luck.
    :--max-time-to-wait: waiting time for a controller ready to drive the car.
    :--delay-between-check-interval: delay between each verification interval when waiting for a controller to be ready.
    :--delay-before-launch-car: delay time after a scene reset before launching the car. This allows us to be sure that all components are loaded before starting the evaluation.
    

CLIENT
------
    :--poll-socket-sleep-sec: time to sleep before polling socket
    :--buffer-message-size-read: number of bits to read into the socket
    :--delatime-to-compute-fps: deltatime between computation of the FPS
    :--margin-before-car-leaving-road: distance from the center of the road at the active node to the car. Maximum value from which it can be considered that the car has left the road
    :--deltatime-min-between-turns: minimum time interval between two turns from which we can count a turn (incrementation)
    :--node-after-start-detection-turn: node from which we can possibly count a turn. (To avoid false positives on the rest of the road)
    :--deltatime-max-between-nodes: Maximum time interval to travel the distance between two nodes. If the vehicle takes too long, it is probably stuck somewhere but not far enough off the road to be considered 'off road'.
    :--deltatime-max-after-driving-to-reach-first-node: Maximum time interval for the car to reach a node if its default settings have not been changed when the car is launched. This is the case when the car moves before the real start and the evaluator has not captured this departure because the simulator does not respond.

CONTROLLER
----------
    :--buffer-requests-size: Size of buffer of requests