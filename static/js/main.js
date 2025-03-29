// static/js/main.js
const socket = io();

const canvas = document.getElementById("simulationCanvas");
const ctx = canvas.getContext("2d");
const NUM_FLOORS = 10;
const NUM_ELEVATORS = 3;
const canvasWidth = canvas.width;
const canvasHeight = canvas.height;
const floorHeight = canvasHeight / NUM_FLOORS;
const shaftSpacing = canvasWidth / (NUM_ELEVATORS + 1);

// Modern color palette
const colors = {
  background: "#f8fafc",
  floorLine: "#e2e8f0",
  floorText: "#64748b",
  shaft: "#cbd5e1",
  elevator: {
    body: "#6366f1",  // indigo-500
    border: "#4f46e5", // indigo-600
    text: "#ffffff"
  },
  passenger: {
    waiting: "#ef4444", // red-500
    onboard: "#10b981", // emerald-500
    text: "#1e293b"
  },
  indicator: {
    up: "#10b981",    // emerald-500
    down: "#ef4444",  // red-500
    idle: "#64748b"   // slate-500
  }
};

let simulationState = null;

socket.on("update", (state) => {
  simulationState = state;
  drawSimulation();
  updateStats(state.stats);
});

function drawSimulation() {
  // Clear canvas with modern background
  ctx.fillStyle = colors.background;
  ctx.fillRect(0, 0, canvasWidth, canvasHeight);
  
  // Draw floors with modern styling
  for (let floor = 0; floor <= NUM_FLOORS; floor++) {
    const y = canvasHeight - floor * floorHeight;
    
    // Floor line
    ctx.strokeStyle = colors.floorLine;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvasWidth, y);
    ctx.stroke();
    
    // Floor label with modern typography
    ctx.fillStyle = colors.floorText;
    ctx.font = "14px 'Inter', sans-serif";
    ctx.textBaseline = "bottom";
    ctx.fillText(`Floor ${floor}`, 20, y - 10);
  }
  
  // Draw elevators and onboard passengers
  simulationState.elevators.forEach((elevator, index) => {
    const shaftX = shaftSpacing * (index + 1);
    
    // Elevator shaft with subtle styling
    ctx.strokeStyle = colors.shaft;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(shaftX, 0);
    ctx.lineTo(shaftX, canvasHeight);
    ctx.stroke();
    
    // Elevator car with modern styling
    const elevatorY = canvasHeight - (elevator.current_floor + 0.5) * floorHeight;
    const carWidth = 50;
    const carHeight = floorHeight * 0.7;
    const carX = shaftX - carWidth / 2;
    const carY = elevatorY - carHeight / 2;
    const cornerRadius = 6;
    
    // Draw rounded rectangle for elevator
    ctx.beginPath();
    ctx.moveTo(carX + cornerRadius, carY);
    ctx.lineTo(carX + carWidth - cornerRadius, carY);
    ctx.quadraticCurveTo(carX + carWidth, carY, carX + carWidth, carY + cornerRadius);
    ctx.lineTo(carX + carWidth, carY + carHeight - cornerRadius);
    ctx.quadraticCurveTo(carX + carWidth, carY + carHeight, carX + carWidth - cornerRadius, carY + carHeight);
    ctx.lineTo(carX + cornerRadius, carY + carHeight);
    ctx.quadraticCurveTo(carX, carY + carHeight, carX, carY + carHeight - cornerRadius);
    ctx.lineTo(carX, carY + cornerRadius);
    ctx.quadraticCurveTo(carX, carY, carX + cornerRadius, carY);
    ctx.closePath();
    
    ctx.fillStyle = colors.elevator.body;
    ctx.fill();
    ctx.strokeStyle = colors.elevator.border;
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Elevator number indicator
    ctx.fillStyle = colors.elevator.text;
    ctx.font = "bold 14px 'Inter', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`${index + 1}`, shaftX, carY + carHeight / 2);
    
    // Direction indicator
    const indicatorSize = 8;
    const indicatorX = shaftX;
    const indicatorY = carY - 15;
    
    ctx.fillStyle = elevator.direction === "up" ? colors.indicator.up : 
                    elevator.direction === "down" ? colors.indicator.down : 
                    colors.indicator.idle;
    
    if (elevator.direction === "up") {
      ctx.beginPath();
      ctx.moveTo(indicatorX - indicatorSize, indicatorY + indicatorSize);
      ctx.lineTo(indicatorX, indicatorY - indicatorSize);
      ctx.lineTo(indicatorX + indicatorSize, indicatorY + indicatorSize);
      ctx.closePath();
      ctx.fill();
    } else if (elevator.direction === "down") {
      ctx.beginPath();
      ctx.moveTo(indicatorX - indicatorSize, indicatorY - indicatorSize);
      ctx.lineTo(indicatorX, indicatorY + indicatorSize);
      ctx.lineTo(indicatorX + indicatorSize, indicatorY - indicatorSize);
      ctx.closePath();
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(indicatorX, indicatorY, indicatorSize/2, 0, Math.PI * 2);
      ctx.fill();
    }
    
    // Onboard passengers with modern styling
    const numOnboard = elevator.passengers.length;
    if (numOnboard > 0) {
      const spacing = carWidth / (numOnboard + 1);
      elevator.passengers.forEach((dest, i) => {
        const cx = carX + spacing * (i + 1);
        const cy = carY + carHeight / 2;
        
        // Passenger dot
        ctx.beginPath();
        ctx.arc(cx, cy - 10, 6, 0, 2 * Math.PI);
        ctx.fillStyle = colors.passenger.onboard;
        ctx.fill();
        
        // Destination badge
        ctx.fillStyle = colors.passenger.onboard;
        ctx.beginPath();
        ctx.roundRect(cx - 10, cy + 5, 20, 15, 4);
        ctx.fill();
        
        // Destination text
        ctx.fillStyle = colors.elevator.text;
        ctx.font = "bold 10px 'Inter', sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(dest, cx, cy + 12);
      });
    }
  });
  
  // Draw waiting passengers with modern styling
  Object.keys(simulationState.queues).forEach((floorStr) => {
    const floor = parseInt(floorStr);
    const passengers = simulationState.queues[floor];
    const y = canvasHeight - floor * floorHeight - floorHeight / 2;
    
    if (passengers.length > 0) {
      const startX = 100;
      const spacing = 20;
      
      passengers.forEach((passenger, index) => {
        const cx = startX + index * spacing;
        const parts = passenger.split("->");
        const destination = parts.length === 2 ? parts[1] : "";
        
        // Passenger dot
        ctx.beginPath();
        ctx.arc(cx, y, 6, 0, 2 * Math.PI);
        ctx.fillStyle = colors.passenger.waiting;
        ctx.fill();
        
        // Destination badge
        ctx.fillStyle = colors.passenger.waiting;
        ctx.beginPath();
        ctx.roundRect(cx - 10, y + 10, 20, 15, 4);
        ctx.fill();
        
        // Destination text
        ctx.fillStyle = colors.elevator.text;
        ctx.font = "bold 10px 'Inter', sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(destination, cx, y + 17);
      });
    }
  });
}

function updateStats(stats) {
  if (!stats) return;
  document.getElementById("totalServed").innerText = stats.total_passengers_served;
  document.getElementById("avgWait").innerText = `${stats.average_wait_time.toFixed(1)} s`;
  document.getElementById("avgJourney").innerText = `${stats.average_journey_time.toFixed(1)} s`;
}

// Add Inter font to the page
const style = document.createElement('style');
style.textContent = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
`;
document.head.appendChild(style);