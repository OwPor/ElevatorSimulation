# app.py
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from scheduler import Scheduler
import threading, time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

NUM_ELEVATORS = 3
NUM_FLOORS = 10
# Set a desired speed factor; for example, 2.0 makes the simulation run twice as fast.
speed_factor = 0.5
scheduler = Scheduler(num_elevators=NUM_ELEVATORS, num_floors=NUM_FLOORS, speed=speed_factor)

def simulation_thread():
    while True:
        scheduler.step()
        state = scheduler.get_state()
        socketio.emit('update', state)
        time.sleep(scheduler.effective_tick)  # Sleep for effective tick duration.

@app.route('/')
def index():
    return render_template('index.html', num_floors=NUM_FLOORS, num_elevators=NUM_ELEVATORS)

@app.route('/add_passenger', methods=['POST'])
def add_passenger():
    data = request.json
    source = int(data.get('source'))
    destination = int(data.get('destination'))
    scheduler.add_passenger(source, destination)
    return jsonify({'status': 'passenger added'}), 200

if __name__ == '__main__':
    thread = threading.Thread(target=simulation_thread)
    thread.daemon = True
    thread.start()
    socketio.run(app, debug=True)
