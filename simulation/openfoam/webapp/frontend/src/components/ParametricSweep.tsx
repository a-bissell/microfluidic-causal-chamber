import { useState, useEffect } from 'react'
import { Play, Grid3X3, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { api, ParametricSweepConfig } from '../lib/api'

interface SweepStatus {
  id: string
  status: string
  completed: number
  total: number
  cases: string[]
}

export default function ParametricSweep() {
  const [pContValues, setPContValues] = useState<number[]>([20000, 40000, 60000, 80000, 100000])
  const [pDispValues, setPDispValues] = useState<number[]>([10000, 20000, 30000, 40000])
  const [endTime, setEndTime] = useState(0.05)
  const [sweepId, setSweepId] = useState<string | null>(null)
  const [sweepStatus, setSweepStatus] = useState<SweepStatus | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  // Poll sweep status
  useEffect(() => {
    if (!sweepId) return

    const pollStatus = async () => {
      try {
        const status = await api.getSweepStatus(sweepId)
        setSweepStatus(status)
        if (status.status === 'completed') {
          setIsRunning(false)
        }
      } catch {
        // Ignore errors
      }
    }

    const interval = setInterval(pollStatus, 2000)
    pollStatus()

    return () => clearInterval(interval)
  }, [sweepId])

  const handleStartSweep = async () => {
    setIsRunning(true)
    try {
      const config: ParametricSweepConfig = {
        p_cont_values: pContValues,
        p_disp_values: pDispValues,
        end_time: endTime,
      }
      const result = await api.startSweep(config)
      setSweepId(result.sweep_id)
    } catch (error) {
      console.error('Failed to start sweep:', error)
      setIsRunning(false)
    }
  }

  const handleValueChange = (
    setter: React.Dispatch<React.SetStateAction<number[]>>,
    index: number,
    value: number
  ) => {
    setter((prev) => {
      const newValues = [...prev]
      newValues[index] = value
      return newValues.sort((a, b) => a - b)
    })
  }

  const addValue = (setter: React.Dispatch<React.SetStateAction<number[]>>, values: number[]) => {
    const max = Math.max(...values)
    setter((prev) => [...prev, max + 10000].sort((a, b) => a - b))
  }

  const removeValue = (setter: React.Dispatch<React.SetStateAction<number[]>>, index: number) => {
    setter((prev) => prev.filter((_, i) => i !== index))
  }

  const totalCases = pContValues.length * pDispValues.length
  const progress = sweepStatus ? (sweepStatus.completed / sweepStatus.total) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Grid3X3 className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Parametric Sweep</h2>
            <p className="text-sm text-muted-foreground">
              Run simulations across parameter ranges
            </p>
          </div>
        </div>

        {/* Parameter Grid Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* P_cont values */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">
              Continuous Phase Pressures (P_cont)
            </label>
            <div className="space-y-2">
              {pContValues.map((value, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => handleValueChange(setPContValues, i, Number(e.target.value))}
                    className="flex-1 px-3 py-2 bg-secondary border border-border rounded-lg font-mono text-sm"
                  />
                  <span className="text-sm text-muted-foreground w-12">Pa</span>
                  {pContValues.length > 2 && (
                    <button
                      onClick={() => removeValue(setPContValues, i)}
                      className="p-2 text-muted-foreground hover:text-destructive"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={() => addValue(setPContValues, pContValues)}
                className="text-sm text-primary hover:underline"
              >
                + Add value
              </button>
            </div>
          </div>

          {/* P_disp values */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">
              Dispersed Phase Pressures (P_disp)
            </label>
            <div className="space-y-2">
              {pDispValues.map((value, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => handleValueChange(setPDispValues, i, Number(e.target.value))}
                    className="flex-1 px-3 py-2 bg-secondary border border-border rounded-lg font-mono text-sm"
                  />
                  <span className="text-sm text-muted-foreground w-12">Pa</span>
                  {pDispValues.length > 2 && (
                    <button
                      onClick={() => removeValue(setPDispValues, i)}
                      className="p-2 text-muted-foreground hover:text-destructive"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={() => addValue(setPDispValues, pDispValues)}
                className="text-sm text-primary hover:underline"
              >
                + Add value
              </button>
            </div>
          </div>
        </div>

        {/* End time */}
        <div className="mb-6">
          <label className="text-sm text-muted-foreground mb-2 block">
            Simulation End Time (per case)
          </label>
          <div className="flex items-center gap-2 max-w-xs">
            <input
              type="number"
              value={endTime}
              onChange={(e) => setEndTime(Number(e.target.value))}
              step={0.01}
              min={0.01}
              max={1}
              className="flex-1 px-3 py-2 bg-secondary border border-border rounded-lg font-mono text-sm"
            />
            <span className="text-sm text-muted-foreground">seconds</span>
          </div>
        </div>

        {/* Summary and Start */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/30">
          <div>
            <span className="text-sm text-muted-foreground">Total simulations: </span>
            <span className="font-mono text-primary text-lg">{totalCases}</span>
            <span className="text-sm text-muted-foreground ml-4">
              Estimated time: ~{Math.ceil(totalCases * endTime * 60)} minutes
            </span>
          </div>
          <button
            onClick={handleStartSweep}
            disabled={isRunning}
            className={`
              px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-all
              ${isRunning
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-gradient-to-r from-primary to-accent text-white hover:shadow-lg glow-primary'
              }
            `}
          >
            {isRunning ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Start Sweep
              </>
            )}
          </button>
        </div>
      </div>

      {/* Sweep Progress */}
      {sweepStatus && (
        <div className="glass-card p-6">
          <h3 className="font-medium mb-4">Sweep Progress</h3>

          {/* Progress bar */}
          <div className="h-4 bg-secondary rounded-full overflow-hidden mb-4">
            <div
              className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="flex items-center justify-between mb-6">
            <span className="text-sm text-muted-foreground">
              {sweepStatus.completed} of {sweepStatus.total} complete
            </span>
            <span className={`text-sm font-medium ${
              sweepStatus.status === 'completed' ? 'text-green-400' : 'text-primary'
            }`}>
              {sweepStatus.status === 'completed' ? (
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Complete
                </span>
              ) : (
                `${progress.toFixed(1)}%`
              )}
            </span>
          </div>

          {/* Parameter Grid Visualization */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="p-2 text-left text-muted-foreground">P_cont \ P_disp</th>
                  {pDispValues.map((p) => (
                    <th key={p} className="p-2 text-center font-mono">
                      {(p / 1000).toFixed(0)} kPa
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pContValues.map((pCont, i) => (
                  <tr key={pCont}>
                    <td className="p-2 font-mono">{(pCont / 1000).toFixed(0)} kPa</td>
                    {pDispValues.map((pDisp, j) => {
                      const caseIndex = i * pDispValues.length + j
                      const isComplete = caseIndex < sweepStatus.completed
                      const isCurrent = caseIndex === sweepStatus.completed && isRunning
                      return (
                        <td key={pDisp} className="p-2 text-center">
                          <div
                            className={`
                              w-8 h-8 mx-auto rounded-lg flex items-center justify-center
                              ${isComplete
                                ? 'bg-green-400/20 text-green-400'
                                : isCurrent
                                ? 'bg-primary/20 text-primary animate-pulse'
                                : 'bg-secondary'
                              }
                            `}
                          >
                            {isComplete ? (
                              <CheckCircle2 className="w-4 h-4" />
                            ) : isCurrent ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <span className="text-xs text-muted-foreground">-</span>
                            )}
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Results Preview (when complete) */}
      {sweepStatus?.status === 'completed' && (
        <div className="glass-card p-6">
          <h3 className="font-medium mb-4">Sweep Complete</h3>
          <p className="text-muted-foreground mb-4">
            All {sweepStatus.total} simulations have finished. View the Results tab for detailed analysis.
          </p>
          <div className="flex gap-2">
            <button className="px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/30 hover:bg-primary/20">
              View Results
            </button>
            <button className="px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80">
              Export All Data
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

