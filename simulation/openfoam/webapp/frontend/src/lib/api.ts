/**
 * API client for the Microfluidic Simulation backend
 */

const API_BASE = '/api'
const WS_BASE = `ws://${window.location.host}`

export interface SimulationParameters {
  p_cont: number
  p_disp: number
  end_time: number
  write_interval: number
  nu_oil?: number
  nu_water?: number
  sigma?: number
}

export interface SimulationStatus {
  case_id: string
  status: 'idle' | 'starting' | 'meshing' | 'running' | 'completed' | 'failed' | 'stopped'
  progress: number
  current_time: number
  end_time: number
  courant_number?: number
  message: string
}

export interface CaseInfo {
  case_id: string
  status: string
  created: string | null
  p_cont: number
  p_disp: number
}

export interface SimulationResult {
  case_id: string
  status: string
  parameters: SimulationParameters
  output_times: number[]
  case_dir: string
}

export interface ParametricSweepConfig {
  p_cont_values: number[]
  p_disp_values: number[]
  end_time: number
}

class ApiClient {
  private async fetch<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    
    return response.json()
  }

  // Status endpoints
  async getStatus(): Promise<{ openfoam_available: boolean; active_simulations: number }> {
    return this.fetch('/status')
  }

  // Simulation endpoints
  async startSimulation(params: SimulationParameters): Promise<SimulationStatus> {
    return this.fetch('/simulation/start', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async getSimulationStatus(caseId: string): Promise<SimulationStatus> {
    return this.fetch(`/simulation/${caseId}/status`)
  }

  async stopSimulation(caseId: string): Promise<{ status: string; case_id: string }> {
    return this.fetch(`/simulation/${caseId}/stop`, { method: 'POST' })
  }

  async getSimulationResults(caseId: string): Promise<SimulationResult> {
    return this.fetch(`/simulation/${caseId}/results`)
  }

  async getOutputTimes(caseId: string): Promise<{ case_id: string; times: number[] }> {
    return this.fetch(`/simulation/${caseId}/times`)
  }

  async getSimulationLogs(caseId: string, lines: number = 100): Promise<{ logs: string[] }> {
    return this.fetch(`/simulation/${caseId}/logs?lines=${lines}`)
  }

  // Case management
  async listCases(): Promise<{ cases: CaseInfo[] }> {
    return this.fetch('/cases')
  }

  async deleteCase(caseId: string): Promise<{ status: string }> {
    return this.fetch(`/cases/${caseId}`, { method: 'DELETE' })
  }

  // Parametric sweep
  async startSweep(config: ParametricSweepConfig): Promise<{ sweep_id: string; total_cases: number }> {
    return this.fetch('/sweep/start', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async getSweepStatus(sweepId: string): Promise<{
    id: string
    status: string
    completed: number
    total: number
    cases: string[]
  }> {
    return this.fetch(`/sweep/${sweepId}/status`)
  }
}

export const api = new ApiClient()

// WebSocket connection for real-time updates
export class SimulationWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnects = 5

  connect(
    caseId: string,
    onMessage: (data: unknown) => void,
    onError?: (error: Event) => void,
    onClose?: () => void
  ): () => void {
    const url = `${WS_BASE}/ws/simulation/${caseId}`
    
    this.ws = new WebSocket(url)
    
    this.ws.onopen = () => {
      console.log(`WebSocket connected to ${caseId}`)
      this.reconnectAttempts = 0
    }
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onError?.(error)
    }
    
    this.ws.onclose = () => {
      console.log('WebSocket closed')
      onClose?.()
      
      // Auto-reconnect
      if (this.reconnectAttempts < this.maxReconnects) {
        this.reconnectAttempts++
        setTimeout(() => {
          this.connect(caseId, onMessage, onError, onClose)
        }, 1000 * this.reconnectAttempts)
      }
    }
    
    // Return disconnect function
    return () => this.disconnect()
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.reconnectAttempts = this.maxReconnects // Prevent reconnect
  }

  send(message: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message)
    }
  }
}

export const simulationWs = new SimulationWebSocket()

