import { useState, useEffect, useCallback, useRef } from 'react'
import { Droplet, Settings, BarChart3, Activity, Grid3X3 } from 'lucide-react'
import ParameterPanel from './components/ParameterPanel'
import SimulationMonitor from './components/SimulationMonitor'
import DropletViewer3D from './components/DropletViewer3D'
import ResultsCharts from './components/ResultsCharts'
import ParametricSweep from './components/ParametricSweep'
import { api, SimulationParameters, SimulationStatus, simulationWs } from './lib/api'

type Tab = 'control' | 'visualization' | 'results' | 'sweep'

// Fake log messages for demo mode
const DEMO_LOG_MESSAGES = [
  'Starting OpenFOAM simulation...',
  'blockMesh: Creating block mesh topology',
  'blockMesh: Creating cells',
  'blockMesh: Creating patches',
  'setFields: Setting initial alpha.water field',
  'interFoam: Reading field p_rgh',
  'interFoam: Reading field U',
  'interFoam: Reading transportProperties',
  'PIMPLE: Operating in PISO mode',
  'Time = 0.0001s',
  'Courant Number mean: 0.0234 max: 0.142',
  'DILUPBiCGStab: Solving for alpha.water, Initial residual = 0.00234',
  'Phase-1 volume fraction = 0.0156 Min(alpha.water) = 0 Max(alpha.water) = 1',
  'GAMG: Solving for p_rgh, Initial residual = 0.0891',
  'time step continuity errors: sum local = 1.234e-09',
  'ExecutionTime = 2.34 s  ClockTime = 3 s',
  'Time = 0.0002s',
  'Courant Number mean: 0.0256 max: 0.156',
  'Interface capturing with MULES',
  'Droplet formation detected at T-junction',
  'Time = 0.0003s',
  'Calculating surface tension forces...',
  'VOF phase fraction updated',
  'Pressure-velocity coupling: PIMPLE iteration 1',
  'Time = 0.0004s',
  'Courant Number mean: 0.0312 max: 0.178',
  'Droplet pinch-off imminent...',
  'Time = 0.0005s',
  'DROPLET FORMED - Volume: 2.34e-12 m³',
  'Continuing simulation...',
]

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('control')
  const [isConnected, setIsConnected] = useState(false)
  const [currentCase, setCurrentCase] = useState<string | null>(null)
  const [simulationStatus, setSimulationStatus] = useState<SimulationStatus | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [demoMode, setDemoMode] = useState(false)
  const demoIntervalRef = useRef<number | null>(null)
  const demoLogIndexRef = useRef(0)

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const status = await api.getStatus()
        setIsConnected(status.openfoam_available)
      } catch {
        setIsConnected(false)
      }
    }
    checkConnection()
    const interval = setInterval(checkConnection, 10000)
    return () => clearInterval(interval)
  }, [])

  // WebSocket connection for current case
  useEffect(() => {
    if (!currentCase) return

    const disconnect = simulationWs.connect(
      currentCase,
      (data) => {
        const update = data as { type: string; [key: string]: unknown }
        if (update.type === 'progress' || update.type === 'status') {
          setSimulationStatus((prev) => ({
            ...prev,
            case_id: currentCase,
            status: (update.status as SimulationStatus['status']) ?? prev?.status ?? 'idle',
            progress: (update.progress as number) ?? prev?.progress ?? 0,
            current_time: (update.current_time as number) ?? prev?.current_time ?? 0,
            end_time: (update.end_time as number) ?? prev?.end_time ?? 0.05,
            courant_number: update.courant_number as number | undefined,
            message: (update.message as string) ?? '',
          }))
        }
      },
      () => console.error('WebSocket error'),
      () => console.log('WebSocket closed')
    )

    return () => disconnect()
  }, [currentCase])

  // Fetch logs periodically
  useEffect(() => {
    if (!currentCase) return

    const fetchLogs = async () => {
      try {
        const { logs: newLogs } = await api.getSimulationLogs(currentCase, 50)
        setLogs(newLogs)
      } catch {
        // Ignore errors
      }
    }

    fetchLogs()
    const interval = setInterval(fetchLogs, 2000)
    return () => clearInterval(interval)
  }, [currentCase])

  const handleStartSimulation = useCallback(async (params: SimulationParameters) => {
    try {
      const status = await api.startSimulation(params)
      setCurrentCase(status.case_id)
      setSimulationStatus(status)
      setActiveTab('control')
    } catch (error) {
      console.error('Failed to start simulation:', error)
    }
  }, [])

  const handleStopSimulation = useCallback(async () => {
    // Handle demo mode stop
    if (demoMode) {
      if (demoIntervalRef.current) {
        clearInterval(demoIntervalRef.current)
        demoIntervalRef.current = null
      }
      setDemoMode(false)
      setSimulationStatus((prev) => prev ? { ...prev, status: 'stopped' } : null)
      return
    }

    if (!currentCase) return
    try {
      await api.stopSimulation(currentCase)
      setSimulationStatus((prev) => prev ? { ...prev, status: 'stopped' } : null)
    } catch (error) {
      console.error('Failed to stop simulation:', error)
    }
  }, [currentCase, demoMode])

  // Demo mode - simulated simulation for testing keygen visualizer
  const handleStartDemo = useCallback(() => {
    setDemoMode(true)
    setCurrentCase('demo-simulation')
    setLogs(['═══════════════════════════════════════════════', 
             '  DEMO MODE - Simulated Simulation',
             '  Testing Keygen Visualizer',
             '═══════════════════════════════════════════════',
             ''])
    demoLogIndexRef.current = 0
    
    const demoEndTime = 0.05
    const demoDuration = 120 // 2 minutes of demo time
    const startTime = Date.now()

    setSimulationStatus({
      case_id: 'demo-simulation',
      status: 'running',
      progress: 0,
      current_time: 0,
      end_time: demoEndTime,
      courant_number: 0.15,
      message: 'Demo mode active',
    })

    // Update progress and add logs periodically
    demoIntervalRef.current = window.setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000
      const progress = Math.min(elapsed / demoDuration, 1)
      const currentTime = progress * demoEndTime

      // Add a new log message every ~2 seconds
      if (Math.random() > 0.7) {
        const logMessage = DEMO_LOG_MESSAGES[demoLogIndexRef.current % DEMO_LOG_MESSAGES.length]
        setLogs((prev) => [...prev.slice(-50), `Time = ${currentTime.toFixed(4)}s`])
        demoLogIndexRef.current++
        
        // Add the actual message after a tiny delay for effect
        setTimeout(() => {
          setLogs((prev) => [...prev.slice(-50), logMessage])
        }, 100)
      }

      // Vary courant number slightly
      const courant = 0.15 + Math.sin(elapsed * 0.5) * 0.1 + Math.random() * 0.05

      setSimulationStatus({
        case_id: 'demo-simulation',
        status: 'running',
        progress,
        current_time: currentTime,
        end_time: demoEndTime,
        courant_number: courant,
        message: progress > 0.5 ? 'Droplet formation in progress...' : 'Initializing flow field...',
      })

      // End demo after duration
      if (progress >= 1) {
        if (demoIntervalRef.current) {
          clearInterval(demoIntervalRef.current)
          demoIntervalRef.current = null
        }
        setSimulationStatus((prev) => prev ? { ...prev, status: 'completed' } : null)
        setDemoMode(false)
        setLogs((prev) => [...prev, '', '═══════════════════════════════════════════════',
                                       '  DEMO COMPLETE',
                                       '═══════════════════════════════════════════════'])
      }
    }, 200)
  }, [])

  // Cleanup demo interval on unmount
  useEffect(() => {
    return () => {
      if (demoIntervalRef.current) {
        clearInterval(demoIntervalRef.current)
      }
    }
  }, [])

  const tabs = [
    { id: 'control' as Tab, label: 'Control', icon: Settings },
    { id: 'visualization' as Tab, label: '3D View', icon: Droplet },
    { id: 'results' as Tab, label: 'Results', icon: BarChart3 },
    { id: 'sweep' as Tab, label: 'Sweep', icon: Grid3X3 },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-border/50 bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Droplet className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold gradient-text">
                Microfluidic Simulation
              </h1>
              <p className="text-xs text-muted-foreground">
                T-Junction Droplet Generator
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Connection status */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-card border border-border">
              <Activity 
                className={`w-4 h-4 ${isConnected ? 'text-green-400' : 'text-destructive'}`} 
              />
              <span className="text-sm text-muted-foreground">
                {isConnected ? 'OpenFOAM Ready' : 'Disconnected'}
              </span>
            </div>

            {/* Current case indicator */}
            {currentCase && (
              <div className="px-3 py-1.5 rounded-full bg-primary/10 border border-primary/30">
                <span className="text-sm text-primary font-mono">
                  {currentCase}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tab navigation */}
        <nav className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium
                  border-b-2 transition-all duration-200
                  ${activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                  }
                `}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </nav>
      </header>

      {/* Main content */}
      <main className="relative z-10 max-w-7xl mx-auto p-4">
        {activeTab === 'control' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ParameterPanel
              onStart={handleStartSimulation}
              onStartDemo={handleStartDemo}
              disabled={simulationStatus?.status === 'running'}
              demoRunning={demoMode}
            />
            <SimulationMonitor
              status={simulationStatus}
              logs={logs}
              onStop={handleStopSimulation}
            />
          </div>
        )}

        {activeTab === 'visualization' && (
          <DropletViewer3D caseId={currentCase} />
        )}

        {activeTab === 'results' && (
          <ResultsCharts caseId={currentCase} />
        )}

        {activeTab === 'sweep' && (
          <ParametricSweep />
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border/50 mt-8 py-4">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-muted-foreground">
          Microfluidic Causal Chamber Project • OpenFOAM 11 • Volume of Fluid Method
        </div>
      </footer>
    </div>
  )
}

export default App

