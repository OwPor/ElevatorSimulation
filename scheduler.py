# scheduler.py
from models import Elevator, Passenger
import random, time
import math

class Scheduler:
    def __init__(self, num_elevators, num_floors, speed=1.0):
        """
        speed: multiplier for simulation speed. 
               speed=1.0 => base speed,
               speed>1.0 => simulation runs faster,
               speed<1.0 => simulation runs slower.
        """
        self.num_floors = num_floors
        self.elevators = [Elevator(i, capacity=3) for i in range(num_elevators)]
        self.floors = {floor: [] for floor in range(num_floors)}
        self.active_calls = set()
        self.step_count = 0

        # Statistics attributes.
        self.total_passengers_served = 0
        self.total_wait_time = 0.0
        self.total_journey_time = 0.0

        # Simulation speed factor.
        self.speed = speed
        self.base_tick = 0.5  # seconds per tick at base speed.
        self.effective_tick = self.base_tick / self.speed

        # Derived parameters (in ticks).
        self.stop_delay_ticks = max(1, math.ceil(0.5 / self.effective_tick))
        # Spawn passengers every 2 seconds (base) => in ticks:
        self.spawn_interval_ticks = max(1, math.ceil(3.0 / self.effective_tick))

    def spawn_passengers(self):
        """Spawn a random number (0 to 5) of passengers."""
        num_new = random.randint(0, 3)
        for _ in range(num_new):
            source = random.randint(0, self.num_floors - 1)
            destination = random.randint(0, self.num_floors - 1)
            while destination == source:
                destination = random.randint(0, self.num_floors - 1)
            self.add_passenger(source, destination)

    def add_passenger(self, source, destination):
        passenger = Passenger(source, destination)
        self.floors[source].append(passenger)
        if source not in self.active_calls:
            self.dispatch_elevator(source, passenger)
            self.active_calls.add(source)

    def dispatch_elevator(self, floor, passenger):
        """
        Destination dispatch–inspired algorithm:
        - If an idle elevator exists (no stops and no passengers), assign the call immediately.
        - Otherwise, choose the elevator with available capacity that minimizes the combination of:
            (a) the distance to the call floor, and
            (b) the current number of scheduled stops.
        """
        # Look for idle elevators (no stops and empty)
        idle_elevators = [e for e in self.elevators if not e.stops and len(e.passengers) == 0]
        if idle_elevators:
            best_elevator = min(idle_elevators, key=lambda e: abs(e.current_floor - floor))
            best_elevator.stops.add(floor)
            return

        # Otherwise, consider elevators with available capacity.
        candidate_elevators = [e for e in self.elevators if len(e.passengers) < e.capacity]
        if candidate_elevators:
            # Choose the elevator that minimizes a combination of distance and current stop count.
            best_elevator = min(candidate_elevators, key=lambda e: (abs(e.current_floor - floor), len(e.stops)))
            best_elevator.stops.add(floor)


    def step(self):
        self.step_count += 1

        # Spawn new passengers every spawn_interval_ticks.
        if self.step_count % self.spawn_interval_ticks == 0:
            self.spawn_passengers()

        for elevator in self.elevators:
            # If the elevator is in a stop delay, decrement its stop timer and skip movement.
            if elevator.stop_timer > 0:
                elevator.stop_timer -= 1
                continue

            # Process disembarking.
            disembarked = elevator.disembark()
            disembark_count = 0
            if disembarked:
                disembark_count = len(disembarked)
                for passenger in disembarked:
                    passenger.drop_time = time.time()
                    self.total_passengers_served += 1
                    self.total_journey_time += (passenger.drop_time - passenger.board_time)
                if elevator.current_floor in self.active_calls and not self.floors[elevator.current_floor]:
                    self.active_calls.discard(elevator.current_floor)

            # Process boarding.
            waiting_queue = self.floors[elevator.current_floor]
            board_count = 0
            for passenger in waiting_queue[:]:
                if len(elevator.passengers) < elevator.capacity:
                    passenger.board_time = time.time()
                    elevator.board(passenger)
                    waiting_queue.remove(passenger)
                    self.total_wait_time += (passenger.board_time - passenger.request_time)
                    board_count += 1
                else:
                    break

            # If either boarding or disembarking occurred, compute the stop delay.
            total_stop_passengers = board_count + disembark_count
            if total_stop_passengers > 0:
                # Calculate the delay in seconds (0.2 sec per passenger).
                delay_seconds = 0.1 * total_stop_passengers
                # Convert delay_seconds into ticks (rounding up).
                elevator.stop_timer = max(1, math.ceil(delay_seconds / self.effective_tick))
                continue  # Skip movement this tick.

            # Determine the next target floor.
            target = None
            stops_in_direction = [
                stop for stop in elevator.stops
                if (stop - elevator.current_floor) * elevator.direction > 0
            ]
            if stops_in_direction:
                target = min(stops_in_direction, key=lambda x: abs(x - elevator.current_floor))
            else:
                if elevator.stops:
                    elevator.direction *= -1
                    target = min(elevator.stops, key=lambda x: abs(x - elevator.current_floor))
                else:
                    waiting_floors = [floor for floor, queue in self.floors.items() if queue]
                    if waiting_floors:
                        target = min(waiting_floors, key=lambda x: abs(x - elevator.current_floor))
                        elevator.stops.add(target)
            # Move one floor toward the target if one exists.
            if target is not None:
                if elevator.current_floor < target:
                    elevator.current_floor += 1
                elif elevator.current_floor > target:
                    elevator.current_floor -= 1


    def get_state(self):
        avg_wait = (self.total_wait_time / self.total_passengers_served) if self.total_passengers_served > 0 else 0
        avg_journey = (self.total_journey_time / self.total_passengers_served) if self.total_passengers_served > 0 else 0

        state = {
            'elevators': [
                {
                    'id': e.id,
                    'current_floor': e.current_floor,
                    'direction': e.direction,
                    'occupancy': len(e.passengers),
                    'capacity': e.capacity,
                    'passengers': [p.destination for p in e.passengers],
                    'stops': sorted(list(e.stops))
                } for e in self.elevators
            ],
            'queues': {
                floor: [f"{p.source}->{p.destination}" for p in queue]
                for floor, queue in self.floors.items()
            },
            'stats': {
                'total_passengers_served': self.total_passengers_served,
                'average_wait_time': round(avg_wait, 2),
                'average_journey_time': round(avg_journey, 2)
            }
        }
        return state
