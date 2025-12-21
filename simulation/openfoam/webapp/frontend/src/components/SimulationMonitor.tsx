import { useRef, useEffect, useState, useCallback } from 'react'
import { Square, Terminal, Activity, Clock, Zap } from 'lucide-react'
import { SimulationStatus } from '../lib/api'
import { formatTime } from '../lib/utils'
import KeygenVisualizer from './KeygenVisualizer'
import { getKeygenAudio } from '../lib/keygenAudio'

interface SimulationMonitorProps {
  status: SimulationStatus | null
  logs: string[]
  onStop: () => void
}

type KeygenPhase = 'normal' | 'glitch' | 'colorshift' | 'full'

// Phase timing configuration (in seconds)
const PHASE_TIMING = {
  normalDuration: 10,    // Normal terminal for 10s
  glitchDuration: 2,     // Glitch transition for 2s
  colorshiftDuration: 2, // Color shift for 2s
  // After that: full keygen mode
}

export default function SimulationMonitor({ status, logs, onStop }: SimulationMonitorProps) {
  const logRef = useRef<HTMLDivElement>(null)
  const [keygenPhase, setKeygenPhase] = useState<KeygenPhase>('normal')
  const [phaseProgress, setPhaseProgress] = useState(0)
  const [keygenExited, setKeygenExited] = useState(false)
  const timerRef = useRef<number | null>(null)
  const startTimeRef = useRef<number | null>(null)

  // Auto-scroll logs
  useEffect(() => {
    if (logRef.current && keygenPhase === 'normal') {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs, keygenPhase])

  // Keygen timer logic
  useEffect(() => {
    // Only activate keygen during running simulation
    if (status?.status !== 'running') {
      // Reset keygen state when simulation stops
      setKeygenPhase('normal')
      setPhaseProgress(0)
      setKeygenExited(false)
      startTimeRef.current = null
      if (timerRef.current) {
        cancelAnimationFrame(timerRef.current)
        timerRef.current = null
      }
      // Stop audio when simulation ends
      getKeygenAudio().stop()
      return
    }

    // Don't restart if user manually exited keygen
    if (keygenExited) return

    // Start timing
    if (!startTimeRef.current) {
      startTimeRef.current = Date.now()
    }

    const updatePhase = () => {
      if (!startTimeRef.current) return

      const elapsed = (Date.now() - startTimeRef.current) / 1000
      const { normalDuration, glitchDuration, colorshiftDuration } = PHASE_TIMING

      if (elapsed < normalDuration) {
        setKeygenPhase('normal')
        setPhaseProgress(elapsed / normalDuration)
      } else if (elapsed < normalDuration + glitchDuration) {
        setKeygenPhase('glitch')
        setPhaseProgress((elapsed - normalDuration) / glitchDuration)
      } else if (elapsed < normalDuration + glitchDuration + colorshiftDuration) {
        setKeygenPhase('colorshift')
        setPhaseProgress(
          (elapsed - normalDuration - glitchDuration) / colorshiftDuration
        )
      } else {
        setKeygenPhase('full')
        setPhaseProgress(1)
      }

      timerRef.current = requestAnimationFrame(updatePhase)
    }

    timerRef.current = requestAnimationFrame(updatePhase)

    return () => {
      if (timerRef.current) {
        cancelAnimationFrame(timerRef.current)
      }
    }
  }, [status?.status, keygenExited])

  const handleKeygenExit = useCallback(() => {
    setKeygenExited(true)
    setKeygenPhase('normal')
    getKeygenAudio().stop()
  }, [])

  const getStatusColor = (s: string) => {
    switch (s) {
      case 'running':
        return 'text-green-400'
      case 'completed':
        return 'text-accent'
      case 'failed':
        return 'text-destructive'
      case 'meshing':
        return 'text-yellow-400'
      default:
        return 'text-muted-foreground'
    }
  }

  const getStatusBg = (s: string) => {
    switch (s) {
      case 'running':
        return 'bg-green-400/10 border-green-400/30'
      case 'completed':
        return 'bg-accent/10 border-accent/30'
      case 'failed':
        return 'bg-destructive/10 border-destructive/30'
      case 'meshing':
        return 'bg-yellow-400/10 border-yellow-400/30'
      default:
        return 'bg-muted/10 border-muted/30'
    }
  }

  const progress = status?.progress ?? 0
  const progressPercent = Math.min(progress * 100, 100)

  // Show keygen visualizer during transition phases or full mode
  const showKeygen = keygenPhase !== 'normal' && status?.status === 'running'

  return (
    <div className="glass-card p-6 flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Simulation Monitor</h2>
            <p className="text-sm text-muted-foreground">Real-time progress</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Re-enable keygen button (if exited) */}
          {keygenExited && status?.status === 'running' && (
            <button
              onClick={() => {
                setKeygenExited(false)
                startTimeRef.current = Date.now() - (PHASE_TIMING.normalDuration * 1000)
              }}
              className="px-3 py-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/30 hover:bg-purple-500/20 text-sm flex items-center gap-1.5 transition-colors"
              title="Activate keygen mode"
            >
              <span className="font-mono text-xs">▶</span>
              Keygen
            </button>
          )}

          {status?.status === 'running' && (
            <button
              onClick={onStop}
              className="px-4 py-2 rounded-lg bg-destructive/10 text-destructive border border-destructive/30 hover:bg-destructive/20 flex items-center gap-2 transition-colors"
            >
              <Square className="w-4 h-4" />
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Status Card */}
      {status && (
        <div className={`p-4 rounded-lg border mb-4 ${getStatusBg(status.status)}`}>
          <div className="flex items-center justify-between mb-3">
            <span className={`text-sm font-medium uppercase tracking-wide ${getStatusColor(status.status)}`}>
              {status.status}
            </span>
            <span className="text-xs text-muted-foreground font-mono">
              {status.case_id}
            </span>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-background/50 rounded-full overflow-hidden mb-3">
            <div
              className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-300 relative"
              style={{ width: `${progressPercent}%` }}
            >
              {status.status === 'running' && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-flow" />
              )}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <Clock className="w-3 h-3" />
                <span className="text-xs">Time</span>
              </div>
              <span className="font-mono text-sm">
                {formatTime(status.current_time)} / {formatTime(status.end_time)}
              </span>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <Activity className="w-3 h-3" />
                <span className="text-xs">Progress</span>
              </div>
              <span className="font-mono text-sm text-primary">
                {progressPercent.toFixed(1)}%
              </span>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <Zap className="w-3 h-3" />
                <span className="text-xs">Courant</span>
              </div>
              <span className={`font-mono text-sm ${
                (status.courant_number ?? 0) > 0.5 ? 'text-yellow-400' : 'text-green-400'
              }`}>
                {status.courant_number?.toFixed(3) ?? '-'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Log viewer / Keygen Visualizer */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center gap-2 mb-2">
          <Terminal className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            {showKeygen ? 'Keygen Mode Active' : 'OpenFOAM Output'}
          </span>
          {showKeygen && (
            <span className="ml-auto text-xs text-purple-400 font-mono animate-pulse">
              ▓▒░ DEMOSCENE ░▒▓
            </span>
          )}
        </div>

        {showKeygen ? (
          <KeygenVisualizer
            phase={keygenPhase}
            progress={phaseProgress}
            terminalLines={logs.slice(-20)}
            onExit={handleKeygenExit}
          />
        ) : (
          <div
            ref={logRef}
            className="flex-1 bg-background/50 rounded-lg p-3 font-mono text-xs overflow-auto min-h-[200px] max-h-[400px] border border-border/50"
          >
            {logs.length === 0 ? (
              <div className="text-muted-foreground italic">
                No simulation output yet. Start a simulation to see logs.
              </div>
            ) : (
              logs.map((line, i) => (
                <div
                  key={i}
                  className={`
                    ${line.includes('ERROR') || line.includes('FATAL') ? 'text-destructive' : ''}
                    ${line.includes('Warning') ? 'text-yellow-400' : ''}
                    ${line.includes('Time =') ? 'text-accent' : ''}
                    ${line.includes('Courant') ? 'text-primary' : ''}
                    whitespace-pre-wrap break-all
                  `}
                >
                  {line}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* No simulation message */}
      {!status && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-muted-foreground">
            <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No simulation running</p>
            <p className="text-sm">Configure parameters and start a simulation</p>
          </div>
        </div>
      )}
    </div>
  )
}
