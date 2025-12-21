# Microfluidic Simulation Web Interface

A modern web application for controlling and visualizing OpenFOAM T-junction droplet generation simulations.

![Microfluidic Simulation UI](https://via.placeholder.com/800x400?text=Microfluidic+Simulation+Interface)

## Features

- **Real-time Simulation Control**: Start, stop, and monitor OpenFOAM simulations
- **Parameter Configuration**: Easy-to-use sliders and presets for pressure settings
- **3D Visualization**: Interactive WebGL viewer for droplet formation
- **Results Dashboard**: Charts for droplet frequency, size distribution, and more
- **Parametric Sweeps**: Automate multiple simulations across parameter ranges
- **WebSocket Updates**: Live progress monitoring and log streaming

## Architecture

```
webapp/
├── backend/               # FastAPI Python backend
│   ├── main.py           # REST API endpoints
│   ├── simulation.py     # OpenFOAM process management
│   ├── websocket_manager.py  # Real-time updates
│   └── requirements.txt
└── frontend/             # React + Vite frontend
    ├── src/
    │   ├── components/
    │   │   ├── ParameterPanel.tsx     # Parameter controls
    │   │   ├── SimulationMonitor.tsx  # Live status
    │   │   ├── DropletViewer3D.tsx    # 3D visualization
    │   │   ├── ResultsCharts.tsx      # Analysis charts
    │   │   └── ParametricSweep.tsx    # Batch runs
    │   ├── lib/
    │   │   ├── api.ts    # API client
    │   │   └── utils.ts  # Utilities
    │   └── App.tsx       # Main application
    └── package.json
```

## Prerequisites

### On Linux/WSL (OpenFOAM host):

1. **OpenFOAM 11** installed and working
2. **Python 3.10+**
3. **Node.js 18+**

### Install Node.js (if not present):

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## Quick Start

### 1. Start the Backend

```bash
cd webapp/backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### 2. Start the Frontend

```bash
cd webapp/frontend

# Install dependencies
npm install

# Start development server
npm run dev -- --host 0.0.0.0
```

The UI will be available at `http://localhost:5173`

### 3. Access from Windows

If running on a remote server (like 3090-server), access via:
- Frontend: `http://<server-ip>:5173`
- API: `http://<server-ip>:8000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/simulation/start` | POST | Start new simulation |
| `/api/simulation/{id}/status` | GET | Get simulation status |
| `/api/simulation/{id}/stop` | POST | Stop simulation |
| `/api/simulation/{id}/results` | GET | Get results |
| `/api/cases` | GET | List all cases |
| `/api/sweep/start` | POST | Start parametric sweep |
| `/ws/simulation/{id}` | WS | Real-time updates |

## Configuration

### Backend Environment

Create `.env` file in `backend/`:

```env
OPENFOAM_CASES_DIR=/home/user/openfoam_cases
TEMPLATE_CASE_DIR=/home/user/tjunction_2d_new
```

### Frontend Environment

Create `.env` file in `frontend/`:

```env
VITE_API_URL=http://localhost:8000
```

## Production Deployment

### Build Frontend

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

### Serve with Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
```

### Run Backend with Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Development

### Frontend Hot Reload

The Vite dev server supports hot module replacement (HMR).

### Backend Auto-reload

Uvicorn with `--reload` watches for file changes.

### Type Checking

```bash
# Frontend
cd frontend
npm run lint

# Backend (optional)
pip install mypy
mypy backend/
```

## Troubleshooting

### OpenFOAM not found

Ensure OpenFOAM is sourced before starting the backend:

```bash
source /opt/openfoam11/etc/bashrc
cd webapp/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### CORS errors

The backend includes CORS middleware allowing all origins in development. For production, configure specific origins in `main.py`.

### WebSocket connection failed

Check that both frontend and backend are accessible from your browser. WebSocket connections require matching host/port or proper proxy configuration.

## License

Part of the Microfluidic Causal Chamber project.

