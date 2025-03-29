# app.py
from flask import Flask, render_template, jsonify
from threading import Thread, Lock, Event
import time
import random
import logging
from queue import Queue
import math

app = Flask(__name__)
simulation = None

class Passenger:
    def __init__(self, pid, start_floor, dest_floor):
        self.id = pid
        self.start_floor = start_floor
        self.dest_floor = dest_floor
        self.status = "waiting"
        self.wait_start = time.time()
        self.ride_start = None

class Elevator:
    def __init__(self, eid, capacity, speed):
        self.id = eid
        self.capacity = capacity
        self.speed = speed
        self.current_floor = 1
        self.direction = 0  # -1: down, 0: stopped, 1: up
        self.passengers = []
        self.target_floors = set()
        self.lock = Lock()
        self.queue = Queue()
        self.running = True

    def move(self):
        while self.running:
            if self.target_floors:
                next_floors = [f for f in self.target_floors if (f > self.current_floor and self.direction == 1) or 
                              (f < self.current_floor and self.direction == -1)]
                if not next_floors:
                    self.direction *= -1
                    continue
                
                next_floor = min(next_floors) if self.direction == 1 else max(next_floors)
                time.sleep(self.speed)
                self.current_floor = next_floor
                self._handle_floor_stop()
            else:
                time.sleep(0.1)

    def _handle_floor_stop(self):
        # Disembark passengers
        remaining = [p for p in self.passengers if p.dest_floor != self.current_floor]
        disembarked = [p for p in self.passengers if p.dest_floor == self.current_floor]
        
        # Embark new passengers (implementation needed)
        
        with self.lock:
            self.passengers = remaining
            self.target_floors.discard(self.current_floor)

class Building:
    def __init__(self, floors, elevators, elevator_capacity):
        self.floors = floors
        self.elevators = [Elevator(i, elevator_capacity, 1) for i in range(elevators)]
        self.floor_queues = {f: [] for f in range(1, floors+1)}
        self.lock = Lock()
        self.passenger_id = 1

    def add_passenger(self, passenger):
        with self.lock:
            self.floor_queues[passenger.start_floor].append(passenger)

class Simulation(Thread):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.building = None
        self.running = Event()
        self.passenger_generator = None

    def run(self):
        self.building = Building(
            self.config['floors'],
            self.config['elevators'],
            self.config['elevator_capacity']
        )
        
        # Start elevator threads
        for elevator in self.building.elevators:
            Thread(target=elevator.move, daemon=True).start()
        
        # Start passenger generator
        self.passenger_generator = Thread(target=self.generate_passengers, daemon=True)
        self.passenger_generator.start()
        
        self.running.set()
        while self.running.is_set():
            time.sleep(0.1)

    def generate_passengers(self):
        while self.running.is_set():
            mean_arrival = self.config['mean_arrival']
            delay = random.expovariate(1.0/mean_arrival)
            time.sleep(delay)
            
            start_floor = random.randint(1, self.config['floors'])
            # Generate destination with normal distribution
            dest_floor = min(max(int(random.normalvariate(
                self.config['floors']/2, 
                self.config['floors']/6
            )), 1), self.config['floors'])
            
            passenger = Passenger(
                self.building.passenger_id,
                start_floor,
                dest_floor
            )
            self.building.add_passenger(passenger)
            self.building.passenger_id += 1

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/status')
def status():
    if not simulation or not simulation.building:
        return jsonify({})
    
    status = {
        'elevators': [],
        'floor_queues': {},
        'metrics': {}
    }
    
    for elevator in simulation.building.elevators:
        with elevator.lock:
            status['elevators'].append({
                'id': elevator.id,
                'current_floor': elevator.current_floor,
                'direction': elevator.direction,
                'passengers': [p.id for p in elevator.passengers],
                'target_floors': list(elevator.target_floors)
            })
    
    with simulation.building.lock:
        for floor, queue in simulation.building.floor_queues.items():
            status['floor_queues'][floor] = len(queue)
    
    return jsonify(status)

@app.route('/configure', methods=['POST'])
def configure():
    # Implementation needed for parameter handling
    pass

@app.route('/start', methods=['POST'])
def start_simulation():
    global simulation
    if not simulation or not simulation.is_alive():
        config = {
            'floors': 20,
            'elevators': 10,
            'elevator_capacity': 8,
            'mean_arrival': 5
        }
        simulation = Simulation(config)
        simulation.start()
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop_simulation():
    if simulation and simulation.is_alive():
        simulation.running.clear()
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    app.run(debug=True)