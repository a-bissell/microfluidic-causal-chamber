"""
FastAPI Backend for Microfluidic T-Junction Simulation

Provides REST API endpoints for:
- Starting/stopping simulations
- Real-time status monitoring via WebSocket
- Results retrieval and visualization data
- Parametric sweep management
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from simulation import SimulationManager, SimulationConfig
from websocket_manager import ConnectionManager

# Configuration
OPENFOAM_CASES_DIR = Path.home() / "openfoam_cases"
# Template case directory - relative to this file's location
_BACKEND_DIR = Path(__file__).parent.resolve()
TEMPLATE_CASE_DIR = _BACKEND_DIR.parent.parent / "tjunction_2d"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    OPENFOAM_CASES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"OpenFOAM cases directory: {OPENFOAM_CASES_DIR}")
    print(f"Template case: {TEMPLATE_CASE_DIR}")
    yield
    # Shutdown
    await simulation_manager.cleanup()


app = FastAPI(
    title="Microfluidic Simulation API",
    description="Control OpenFOAM T-junction droplet simulations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Managers
simulation_manager = SimulationManager(OPENFOAM_CASES_DIR, TEMPLATE_CASE_DIR)
ws_manager = ConnectionManager()


# ============================================================================
# Pydantic Models
# ============================================================================

class SimulationParameters(BaseModel):
    """Input parameters for simulation."""
    p_cont: float = Field(50000, ge=10000, le=200000, description="Continuous phase pressure (Pa)")
    p_disp: float = Field(30000, ge=5000, le=100000, description="Dispersed phase pressure (Pa)")
    end_time: float = Field(0.05, ge=0.001, le=1.0, description="Simulation end time (s)")
    write_interval: float = Field(0.001, ge=0.0001, le=0.1, description="Output write interval (s)")
    
    # Optional fluid properties
    nu_oil: float = Field(5e-5, description="Oil kinematic viscosity (m²/s)")
    nu_water: float = Field(1e-6, description="Water kinematic viscosity (m²/s)")
    sigma: float = Field(0.03, description="Surface tension (N/m)")


class SimulationStatus(BaseModel):
    """Current simulation status."""
    case_id: str
    status: str  # "idle", "running", "completed", "failed"
    progress: float  # 0.0 to 1.0
    current_time: float
    end_time: float
    courant_number: Optional[float] = None
    message: str = ""


class SimulationResult(BaseModel):
    """Simulation results summary."""
    case_id: str
    parameters: SimulationParameters
    status: str
    output_times: list[float]
    droplet_count: Optional[int] = None
    mean_frequency: Optional[float] = None
    mean_diameter: Optional[float] = None


class ParametricSweepConfig(BaseModel):
    """Configuration for parametric sweep."""
    p_cont_values: list[float] = Field(default=[20000, 40000, 60000, 80000, 100000])
    p_disp_values: list[float] = Field(default=[10000, 20000, 30000, 40000, 50000])
    end_time: float = 0.05


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root - health check."""
    return {
        "status": "ok",
        "service": "Microfluidic Simulation API",
        "version": "1.0.0"
    }


@app.get("/api/status")
async def get_global_status():
    """Get overall system status."""
    return {
        "openfoam_available": simulation_manager.check_openfoam(),
        "active_simulations": simulation_manager.get_active_count(),
        "cases_directory": str(OPENFOAM_CASES_DIR),
        "template_available": TEMPLATE_CASE_DIR.exists()
    }


@app.post("/api/simulation/start", response_model=SimulationStatus)
async def start_simulation(
    params: SimulationParameters,
    background_tasks: BackgroundTasks
):
    """Start a new simulation with given parameters."""
    try:
        case_id = await simulation_manager.create_case(params)
        background_tasks.add_task(
            simulation_manager.run_simulation,
            case_id,
            ws_manager
        )
        return SimulationStatus(
            case_id=case_id,
            status="starting",
            progress=0.0,
            current_time=0.0,
            end_time=params.end_time,
            message="Simulation starting..."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/simulation/{case_id}/status", response_model=SimulationStatus)
async def get_simulation_status(case_id: str):
    """Get status of a specific simulation."""
    status = simulation_manager.get_status(case_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return status


@app.post("/api/simulation/{case_id}/stop")
async def stop_simulation(case_id: str):
    """Stop a running simulation."""
    success = await simulation_manager.stop_simulation(case_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found or not running")
    return {"status": "stopped", "case_id": case_id}


@app.get("/api/simulation/{case_id}/results")
async def get_simulation_results(case_id: str):
    """Get results from a completed simulation."""
    results = simulation_manager.get_results(case_id)
    if results is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return results


@app.get("/api/simulation/{case_id}/times")
async def get_output_times(case_id: str):
    """Get list of available output time steps."""
    times = simulation_manager.get_output_times(case_id)
    return {"case_id": case_id, "times": times}


@app.get("/api/simulation/{case_id}/field/{time_step}")
async def get_field_data(case_id: str, time_step: float, field: str = "alpha.water"):
    """Get field data for visualization at a specific time step."""
    data = simulation_manager.get_field_data(case_id, time_step, field)
    if data is None:
        raise HTTPException(status_code=404, detail="Field data not found")
    return data


@app.get("/api/simulation/{case_id}/logs")
async def get_simulation_logs(case_id: str, lines: int = 100):
    """Get recent log lines from simulation."""
    logs = simulation_manager.get_logs(case_id, lines)
    return {"case_id": case_id, "logs": logs}


@app.get("/api/cases")
async def list_cases():
    """List all simulation cases."""
    cases = simulation_manager.list_cases()
    return {"cases": cases}


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: str):
    """Delete a simulation case."""
    success = simulation_manager.delete_case(case_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return {"status": "deleted", "case_id": case_id}


# ============================================================================
# Parametric Sweep Endpoints
# ============================================================================

@app.post("/api/sweep/start")
async def start_parametric_sweep(
    config: ParametricSweepConfig,
    background_tasks: BackgroundTasks
):
    """Start a parametric sweep across pressure values."""
    sweep_id = await simulation_manager.create_sweep(config)
    background_tasks.add_task(
        simulation_manager.run_sweep,
        sweep_id,
        ws_manager
    )
    return {
        "sweep_id": sweep_id,
        "total_cases": len(config.p_cont_values) * len(config.p_disp_values),
        "status": "starting"
    }


@app.get("/api/sweep/{sweep_id}/status")
async def get_sweep_status(sweep_id: str):
    """Get status of parametric sweep."""
    status = simulation_manager.get_sweep_status(sweep_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Sweep {sweep_id} not found")
    return status


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/simulation/{case_id}")
async def websocket_endpoint(websocket: WebSocket, case_id: str):
    """WebSocket for real-time simulation updates."""
    await ws_manager.connect(websocket, case_id)
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            # Handle client commands if needed
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, case_id)


@app.websocket("/ws/logs/{case_id}")
async def websocket_logs(websocket: WebSocket, case_id: str):
    """WebSocket for streaming simulation logs."""
    await websocket.accept()
    try:
        while True:
            logs = simulation_manager.get_logs(case_id, lines=10)
            await websocket.send_json({"logs": logs})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

