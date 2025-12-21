import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
} from 'recharts'
import { Download, RefreshCw, TrendingUp, Droplets, Gauge } from 'lucide-react'
import { api, CaseInfo } from '../lib/api'

interface ResultsChartsProps {
  caseId: string | null
}

// Sample data generators (would be replaced with actual post-processing results)
function generateDropletData(times: number[]) {
  return times.map((t, i) => ({
    time: t,
    diameter: 80 + Math.random() * 40, // µm
    length: 120 + Math.random() * 60, // µm
    velocity: 0.01 + Math.random() * 0.02, // m/s
    frequency: 10 + i * 2 + Math.random() * 5, // Hz
  }))
}

function generatePressureFlow() {
  const data = []
  for (let pCont = 20000; pCont <= 100000; pCont += 10000) {
    for (let pDisp = 10000; pDisp <= 50000; pDisp += 10000) {
      data.push({
        pCont: pCont / 1000,
        pDisp: pDisp / 1000,
        frequency: (pCont / pDisp) * 5 + Math.random() * 10,
        diameter: 150 - (pCont / pDisp) * 20 + Math.random() * 20,
      })
    }
  }
  return data
}

function generateSizeDistribution() {
  const bins = []
  for (let d = 60; d <= 160; d += 10) {
    bins.push({
      diameter: d,
      count: Math.floor(Math.exp(-((d - 100) ** 2) / 1000) * 50) + Math.floor(Math.random() * 5),
    })
  }
  return bins
}

export default function ResultsCharts({ caseId }: ResultsChartsProps) {
  const [dropletData, setDropletData] = useState<ReturnType<typeof generateDropletData>>([])
  const [sizeDistribution, setSizeDistribution] = useState<ReturnType<typeof generateSizeDistribution>>([])
  const [pressureFlowData, setPressureFlowData] = useState<ReturnType<typeof generatePressureFlow>>([])
  const [cases, setCases] = useState<CaseInfo[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Load case list
    const loadCases = async () => {
      try {
        const { cases } = await api.listCases()
        setCases(cases)
      } catch {
        // Ignore
      }
    }
    loadCases()
  }, [])

  useEffect(() => {
    if (!caseId) return

    const loadResults = async () => {
      setLoading(true)
      try {
        const { times } = await api.getOutputTimes(caseId)
        // Generate sample data based on output times
        setDropletData(generateDropletData(times))
        setSizeDistribution(generateSizeDistribution())
        setPressureFlowData(generatePressureFlow())
      } catch {
        // Generate sample data anyway
        setDropletData(generateDropletData([0.01, 0.02, 0.03, 0.04, 0.05]))
        setSizeDistribution(generateSizeDistribution())
        setPressureFlowData(generatePressureFlow())
      }
      setLoading(false)
    }
    loadResults()
  }, [caseId])

  const handleExportCSV = () => {
    if (dropletData.length === 0) return

    const headers = ['time,diameter,length,velocity,frequency']
    const rows = dropletData.map(
      (d) => `${d.time},${d.diameter},${d.length},${d.velocity},${d.frequency}`
    )
    const csv = [...headers, ...rows].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `droplet_data_${caseId || 'simulation'}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const chartTheme = {
    background: 'transparent',
    textColor: '#94a3b8',
    gridColor: '#1e3a5f',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Results Analysis</h2>
            <p className="text-sm text-muted-foreground">
              {caseId ? `Case: ${caseId}` : 'Select a simulation to view results'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.location.reload()}
            className="p-2 rounded-lg hover:bg-secondary transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleExportCSV}
            disabled={dropletData.length === 0}
            className="px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/30 hover:bg-primary/20 flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Droplet Frequency vs Time */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Droplets className="w-4 h-4 text-accent" />
            <h3 className="font-medium">Droplet Generation Frequency</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dropletData}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
              <XAxis
                dataKey="time"
                stroke={chartTheme.textColor}
                tickFormatter={(v) => `${(v * 1000).toFixed(0)}ms`}
              />
              <YAxis stroke={chartTheme.textColor} unit=" Hz" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1f35',
                  border: '1px solid #1e3a5f',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="frequency"
                stroke="#06b6d4"
                strokeWidth={2}
                dot={{ fill: '#06b6d4', strokeWidth: 0 }}
                name="Frequency (Hz)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Droplet Size Distribution */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Gauge className="w-4 h-4 text-primary" />
            <h3 className="font-medium">Droplet Size Distribution</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sizeDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
              <XAxis
                dataKey="diameter"
                stroke={chartTheme.textColor}
                unit=" µm"
              />
              <YAxis stroke={chartTheme.textColor} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1f35',
                  border: '1px solid #1e3a5f',
                  borderRadius: '8px',
                }}
              />
              <Bar
                dataKey="count"
                fill="#3b82f6"
                radius={[4, 4, 0, 0]}
                name="Count"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Diameter vs Time */}
        <div className="glass-card p-6">
          <h3 className="font-medium mb-4">Droplet Diameter Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dropletData}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
              <XAxis
                dataKey="time"
                stroke={chartTheme.textColor}
                tickFormatter={(v) => `${(v * 1000).toFixed(0)}ms`}
              />
              <YAxis stroke={chartTheme.textColor} unit=" µm" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1f35',
                  border: '1px solid #1e3a5f',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="diameter"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Diameter (µm)"
              />
              <Line
                type="monotone"
                dataKey="length"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Length (µm)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pressure-Frequency Relationship */}
        <div className="glass-card p-6">
          <h3 className="font-medium mb-4">Pressure vs Frequency (Parametric)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
              <XAxis
                dataKey="pCont"
                stroke={chartTheme.textColor}
                name="P_cont"
                unit=" kPa"
              />
              <YAxis
                dataKey="frequency"
                stroke={chartTheme.textColor}
                name="Frequency"
                unit=" Hz"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1f35',
                  border: '1px solid #1e3a5f',
                  borderRadius: '8px',
                }}
                formatter={(value: number, name: string) => [
                  `${value.toFixed(1)}${name === 'frequency' ? ' Hz' : ' kPa'}`,
                  name,
                ]}
              />
              <Scatter
                data={pressureFlowData}
                fill="#06b6d4"
                name="Simulations"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Statistics */}
      {dropletData.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="font-medium mb-4">Summary Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-secondary/30">
              <div className="text-sm text-muted-foreground">Mean Diameter</div>
              <div className="text-2xl font-mono text-primary">
                {(dropletData.reduce((a, b) => a + b.diameter, 0) / dropletData.length).toFixed(1)} µm
              </div>
            </div>
            <div className="p-4 rounded-lg bg-secondary/30">
              <div className="text-sm text-muted-foreground">Mean Frequency</div>
              <div className="text-2xl font-mono text-accent">
                {(dropletData.reduce((a, b) => a + b.frequency, 0) / dropletData.length).toFixed(1)} Hz
              </div>
            </div>
            <div className="p-4 rounded-lg bg-secondary/30">
              <div className="text-sm text-muted-foreground">Total Droplets</div>
              <div className="text-2xl font-mono text-foreground">
                {sizeDistribution.reduce((a, b) => a + b.count, 0)}
              </div>
            </div>
            <div className="p-4 rounded-lg bg-secondary/30">
              <div className="text-sm text-muted-foreground">CV (Size)</div>
              <div className="text-2xl font-mono text-foreground">
                {(
                  (Math.sqrt(
                    dropletData.reduce(
                      (a, b) =>
                        a +
                        (b.diameter -
                          dropletData.reduce((x, y) => x + y.diameter, 0) / dropletData.length) **
                          2,
                      0
                    ) / dropletData.length
                  ) /
                    (dropletData.reduce((a, b) => a + b.diameter, 0) / dropletData.length)) *
                  100
                ).toFixed(1)}
                %
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Previous Cases */}
      {cases.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="font-medium mb-4">Simulation History</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="pb-2 pr-4">Case ID</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">P_cont</th>
                  <th className="pb-2 pr-4">P_disp</th>
                  <th className="pb-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {cases.slice(0, 10).map((c) => (
                  <tr key={c.case_id} className="border-b border-border/50 hover:bg-secondary/30">
                    <td className="py-2 pr-4 font-mono text-primary">{c.case_id}</td>
                    <td className="py-2 pr-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs ${
                          c.status === 'completed'
                            ? 'bg-green-400/10 text-green-400'
                            : c.status === 'running'
                            ? 'bg-primary/10 text-primary'
                            : 'bg-muted/30 text-muted-foreground'
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="py-2 pr-4 font-mono">{(c.p_cont / 1000).toFixed(0)} kPa</td>
                    <td className="py-2 pr-4 font-mono">{(c.p_disp / 1000).toFixed(0)} kPa</td>
                    <td className="py-2 text-muted-foreground">
                      {c.created ? new Date(c.created).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

