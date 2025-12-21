import { useState } from 'react'
import { Play, Beaker, Gauge, Clock, Droplets, Music } from 'lucide-react'
import { SimulationParameters } from '../lib/api'
import { formatPressure } from '../lib/utils'

interface ParameterPanelProps {
  onStart: (params: SimulationParameters) => void
  onStartDemo?: () => void
  disabled?: boolean
  demoRunning?: boolean
}

interface Preset {
  name: string
  description: string
  params: Partial<SimulationParameters>
}

const presets: Preset[] = [
  {
    name: 'Dripping Regime',
    description: 'Low flow rate, large droplets',
    params: { p_cont: 30000, p_disp: 20000, end_time: 0.05 },
  },
  {
    name: 'Squeezing Regime',
    description: 'Moderate flow, regular droplets',
    params: { p_cont: 50000, p_disp: 30000, end_time: 0.05 },
  },
  {
    name: 'Jetting Regime',
    description: 'High flow rate, small droplets',
    params: { p_cont: 100000, p_disp: 40000, end_time: 0.03 },
  },
]

export default function ParameterPanel({ onStart, onStartDemo, disabled, demoRunning }: ParameterPanelProps) {
  const [params, setParams] = useState<SimulationParameters>({
    p_cont: 50000,
    p_disp: 30000,
    end_time: 0.05,
    write_interval: 0.001,
    nu_oil: 5e-5,
    nu_water: 1e-6,
    sigma: 0.03,
  })

  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSliderChange = (key: keyof SimulationParameters, value: number) => {
    setParams((prev) => ({ ...prev, [key]: value }))
  }

  const applyPreset = (preset: Preset) => {
    setParams((prev) => ({ ...prev, ...preset.params }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onStart(params)
  }

  // Calculate flow ratio
  const flowRatio = params.p_cont / params.p_disp

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <Beaker className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">Simulation Parameters</h2>
          <p className="text-sm text-muted-foreground">Configure T-junction settings</p>
        </div>
      </div>

      {/* Presets */}
      <div className="mb-6">
        <label className="text-sm text-muted-foreground mb-2 block">Quick Presets</label>
        <div className="grid grid-cols-3 gap-2">
          {presets.map((preset) => (
            <button
              key={preset.name}
              onClick={() => applyPreset(preset)}
              className="p-3 rounded-lg bg-secondary/50 hover:bg-secondary border border-border/50 hover:border-primary/50 transition-all text-left group"
            >
              <span className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                {preset.name}
              </span>
              <span className="text-xs text-muted-foreground block mt-1">
                {preset.description}
              </span>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Pressure Controls */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-3">
            <Gauge className="w-4 h-4 text-accent" />
            <span className="text-sm font-medium">Pressure Settings</span>
          </div>

          {/* Continuous Phase Pressure */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-sm text-muted-foreground">
                Continuous Phase (Oil) Pressure
              </label>
              <span className="text-sm font-mono text-primary">
                {formatPressure(params.p_cont)}
              </span>
            </div>
            <input
              type="range"
              min={10000}
              max={200000}
              step={5000}
              value={params.p_cont}
              onChange={(e) => handleSliderChange('p_cont', Number(e.target.value))}
              className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>10 kPa</span>
              <span>200 kPa</span>
            </div>
          </div>

          {/* Dispersed Phase Pressure */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-sm text-muted-foreground">
                Dispersed Phase (Water) Pressure
              </label>
              <span className="text-sm font-mono text-accent">
                {formatPressure(params.p_disp)}
              </span>
            </div>
            <input
              type="range"
              min={5000}
              max={100000}
              step={2500}
              value={params.p_disp}
              onChange={(e) => handleSliderChange('p_disp', Number(e.target.value))}
              className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-accent"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>5 kPa</span>
              <span>100 kPa</span>
            </div>
          </div>

          {/* Flow ratio indicator */}
          <div className="p-3 rounded-lg bg-secondary/30 flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Flow Ratio (P_cont/P_disp)</span>
            <span className={`font-mono font-medium ${
              flowRatio > 3 ? 'text-destructive' : 
              flowRatio > 2 ? 'text-yellow-400' : 
              'text-green-400'
            }`}>
              {flowRatio.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Time Settings */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-accent" />
            <span className="text-sm font-medium">Time Settings</span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">End Time (s)</label>
              <input
                type="number"
                min={0.001}
                max={1}
                step={0.01}
                value={params.end_time}
                onChange={(e) => handleSliderChange('end_time', Number(e.target.value))}
                className="w-full px-3 py-2 bg-secondary border border-border rounded-lg font-mono text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Write Interval (s)</label>
              <input
                type="number"
                min={0.0001}
                max={0.1}
                step={0.0005}
                value={params.write_interval}
                onChange={(e) => handleSliderChange('write_interval', Number(e.target.value))}
                className="w-full px-3 py-2 bg-secondary border border-border rounded-lg font-mono text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Advanced Settings */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-2"
          >
            <Droplets className="w-4 h-4" />
            {showAdvanced ? 'Hide' : 'Show'} Fluid Properties
          </button>

          {showAdvanced && (
            <div className="mt-4 p-4 rounded-lg bg-secondary/30 space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Oil Viscosity (m²/s)</label>
                  <input
                    type="number"
                    step={1e-6}
                    value={params.nu_oil}
                    onChange={(e) => handleSliderChange('nu_oil', Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-secondary border border-border rounded font-mono text-xs"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Water Viscosity (m²/s)</label>
                  <input
                    type="number"
                    step={1e-7}
                    value={params.nu_water}
                    onChange={(e) => handleSliderChange('nu_water', Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-secondary border border-border rounded font-mono text-xs"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Surface Tension (N/m)</label>
                  <input
                    type="number"
                    step={0.001}
                    value={params.sigma}
                    onChange={(e) => handleSliderChange('sigma', Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-secondary border border-border rounded font-mono text-xs"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={disabled || demoRunning}
          className={`
            w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2
            transition-all duration-200
            ${disabled || demoRunning
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'bg-gradient-to-r from-primary to-primary/80 text-white hover:shadow-lg hover:shadow-primary/25 glow-primary'
            }
          `}
        >
          <Play className="w-5 h-5" />
          {disabled ? 'Simulation Running...' : 'Start Simulation'}
        </button>

        {/* Demo Mode Button */}
        {onStartDemo && (
          <button
            type="button"
            onClick={onStartDemo}
            disabled={disabled || demoRunning}
            className={`
              w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2
              transition-all duration-200 mt-2
              ${disabled || demoRunning
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg hover:shadow-purple-500/25 border border-purple-400/30'
              }
            `}
            title="Start a simulated simulation to test the keygen visualizer"
          >
            <Music className="w-5 h-5" />
            {demoRunning ? 'Demo Running...' : '▶ Demo Mode (Keygen Test)'}
          </button>
        )}
      </form>
    </div>
  )
}

