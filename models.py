# models.py
import time

class Elevator:
    def __init__(self, id, current_floor=0, capacity=3):
        self.id = id
        self.current_floor = current_floor
        self.capacity = capacity
        self.passengers = []  # List of Passenger objects onboard.
        self.direction = 1    # 1 means up, -1 means down.
        self.stops = set()    # Floors this elevator must stop at.
        self.stop_timer = 0   # Number of simulation ticks to remain stopped.

    def board(self, passenger):
        if len(self.passengers) < self.capacity:
            self.passengers.append(passenger)
            # Also add the passenger's destination to the stops.
            self.stops.add(passenger.destination)

    def disembark(self):
        # Remove passengers whose destination is the current floor.
        disembarked = [p for p in self.passengers if p.destination == self.current_floor]
        self.passengers = [p for p in self.passengers if p.destination != self.current_floor]
        self.stops.discard(self.current_floor)
        return disembarked

class Passenger:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.request_time = time.time()
        self.board_time = None
        self.drop_time = None

    def __repr__(self):
        return f"P({self.source}->{self.destination})"
