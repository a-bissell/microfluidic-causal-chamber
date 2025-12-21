/**
 * Keygen Mode Visualizer
 * 
 * Demoscene-inspired visual effects that activate during simulation
 * Features: plasma effects, scrolling text, starfield, and more
 * Now with real-time parameter customization!
 */

import { useRef, useEffect, useCallback, useState } from 'react'
import { Settings } from 'lucide-react'
import { getKeygenAudio, KeygenAudioParams, defaultAudioParams } from '../lib/keygenAudio'
import KeygenParamsPanel from './KeygenParamsPanel'

type KeygenPhase = 'normal' | 'glitch' | 'colorshift' | 'full'

// Configurable visual parameters
export interface KeygenVisualParams {
  scrollSpeed: number
  waveAmplitude: number
  waveFrequency: number
  colorCycleSpeed: number
  glitchIntensity: number
  starfieldEnabled: boolean
  scanlines: boolean
}

export const defaultVisualParams: KeygenVisualParams = {
  scrollSpeed: 1,
  waveAmplitude: 15,
  waveFrequency: 2,
  colorCycleSpeed: 1,
  glitchIntensity: 0.3,
  starfieldEnabled: true,
  scanlines: true,
}

interface KeygenVisualizerProps {
  phase: KeygenPhase
  progress: number
  terminalLines: string[]
  onExit: () => void
}

// Plasma color palette (demoscene style)
const PALETTE = [
  '#000033', '#000066', '#000099', '#0000cc', '#0000ff',
  '#0033ff', '#0066ff', '#0099ff', '#00ccff', '#00ffff',
  '#00ffcc', '#00ff99', '#00ff66', '#00ff33', '#00ff00',
  '#33ff00', '#66ff00', '#99ff00', '#ccff00', '#ffff00',
  '#ffcc00', '#ff9900', '#ff6600', '#ff3300', '#ff0000',
  '#ff0033', '#ff0066', '#ff0099', '#ff00cc', '#ff00ff',
  '#cc00ff', '#9900ff', '#6600ff', '#3300ff', '#0000ff',
]

// Scrolltext messages
const SCROLL_TEXTS = [
  '>>> MICROFLUIDIC SIMULATION RUNNING <<<',
  'GREETS TO: OpenFOAM • ParaView • CFD Community',
  'T-JUNCTION DROPLET GENERATOR v1.0',
  '♦ VOF METHOD ♦ CSF MODEL ♦ PIMPLE ALGORITHM ♦',
  'SOLVING NAVIER-STOKES EQUATIONS...',
  '>>> DROPLETS FORMING AT THE JUNCTION <<<',
]

export default function KeygenVisualizer({ 
  phase, 
  progress, 
  terminalLines, 
  onExit,
}: KeygenVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>(0)
  const timeRef = useRef(0)
  const [audioStarted, setAudioStarted] = useState(false)
  const [showParamsPanel, setShowParamsPanel] = useState(false)
  
  // Audio and visual parameters state
  const [audioParams, setAudioParams] = useState<KeygenAudioParams>(defaultAudioParams)
  const [visualParams, setVisualParams] = useState<KeygenVisualParams>(defaultVisualParams)
  
  // Use refs for params to avoid re-creating callbacks
  const paramsRef = useRef(visualParams)
  paramsRef.current = visualParams
  
  // Sync audio params with the audio engine
  useEffect(() => {
    const audio = getKeygenAudio()
    audio.setParams(audioParams)
  }, [audioParams])
  
  // Handle params change from panel
  const handleParamsChange = useCallback((
    newAudioParams: Partial<KeygenAudioParams>,
    newVisualParams: Partial<KeygenVisualParams>
  ) => {
    if (Object.keys(newAudioParams).length > 0) {
      setAudioParams(prev => ({ ...prev, ...newAudioParams }))
    }
    if (Object.keys(newVisualParams).length > 0) {
      setVisualParams(prev => ({ ...prev, ...newVisualParams }))
    }
  }, [])

  // Start audio on first interaction
  const startAudio = useCallback(() => {
    if (!audioStarted) {
      getKeygenAudio().play()
      setAudioStarted(true)
    }
  }, [audioStarted])

  // Plasma effect with configurable wave
  const drawPlasma = useCallback((
    ctx: CanvasRenderingContext2D, 
    width: number, 
    height: number, 
    time: number,
    colorSpeed: number,
    waveAmp: number,
    waveFreq: number
  ) => {
    const imageData = ctx.createImageData(width, height)
    const data = imageData.data
    
    const adjustedTime = time * colorSpeed
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // Classic plasma formula with configurable parameters
        const v1 = Math.sin(x / (16 / waveFreq) + adjustedTime)
        const v2 = Math.sin((y / (8 / waveFreq) + adjustedTime) / 2)
        const v3 = Math.sin((x / (16 / waveFreq) + y / (8 / waveFreq) + adjustedTime) / 2)
        const v4 = Math.sin(Math.sqrt(x * x + y * y) / (8 / waveFreq) + adjustedTime)
        
        const value = (v1 + v2 + v3 + v4 + 4) / 8
        const colorIndex = Math.floor(value * (PALETTE.length - 1))
        const color = PALETTE[colorIndex]
        
        // Parse hex color
        const r = parseInt(color.slice(1, 3), 16)
        const g = parseInt(color.slice(3, 5), 16)
        const b = parseInt(color.slice(5, 7), 16)
        
        const i = (y * width + x) * 4
        data[i] = r
        data[i + 1] = g
        data[i + 2] = b
        data[i + 3] = 255
      }
    }
    
    ctx.putImageData(imageData, 0, 0)
  }, [])

  // Starfield effect
  const stars = useRef<Array<{ x: number; y: number; z: number }>>([])
  
  const initStars = useCallback((count: number, width: number, height: number) => {
    stars.current = []
    for (let i = 0; i < count; i++) {
      stars.current.push({
        x: Math.random() * width - width / 2,
        y: Math.random() * height - height / 2,
        z: Math.random() * 1000,
      })
    }
  }, [])

  const drawStarfield = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, speed: number) => {
    if (!paramsRef.current.starfieldEnabled) return
    
    const cx = width / 2
    const cy = height / 2
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)'
    ctx.fillRect(0, 0, width, height)
    
    for (const star of stars.current) {
      star.z -= speed
      
      if (star.z <= 0) {
        star.x = Math.random() * width - width / 2
        star.y = Math.random() * height - height / 2
        star.z = 1000
      }
      
      const sx = (star.x / star.z) * 200 + cx
      const sy = (star.y / star.z) * 200 + cy
      const size = (1 - star.z / 1000) * 3
      
      const brightness = 1 - star.z / 1000
      ctx.fillStyle = `rgba(255, 255, 255, ${brightness})`
      ctx.beginPath()
      ctx.arc(sx, sy, size, 0, Math.PI * 2)
      ctx.fill()
    }
  }, [])

  // Scrolling text with wave effect
  const drawScrollText = useCallback((
    ctx: CanvasRenderingContext2D, 
    width: number, 
    height: number, 
    time: number,
    scrollSpeed: number,
    waveAmp: number
  ) => {
    const text = SCROLL_TEXTS.join('     ♦     ')
    const speed = 100 * scrollSpeed // pixels per second
    const offset = (time * speed) % (text.length * 16)
    
    ctx.font = 'bold 14px "JetBrains Mono", monospace'
    ctx.shadowColor = '#00ffff'
    ctx.shadowBlur = 10
    
    // Draw each character with wave effect
    const textWidth = ctx.measureText(text).width
    const baseY = height - 20
    
    for (let i = 0; i < text.length; i++) {
      const charX = i * 10 - offset
      // Wave effect on Y position
      const waveY = Math.sin((charX + time * 100) / 30) * waveAmp
      
      // Color cycling per character
      const hue = (i * 10 + time * 50) % 360
      ctx.fillStyle = `hsl(${hue}, 100%, 60%)`
      
      ctx.fillText(text[i], charX, baseY + waveY)
      // Second copy for seamless loop
      ctx.fillText(text[i], charX + textWidth, baseY + waveY)
    }
    
    ctx.shadowBlur = 0
  }, [])

  // Terminal overlay with glitch effect
  const drawTerminalOverlay = useCallback((
    ctx: CanvasRenderingContext2D, 
    width: number, 
    height: number, 
    lines: string[],
    glitchIntensity: number
  ) => {
    const effectiveGlitch = glitchIntensity * paramsRef.current.glitchIntensity
    
    // Semi-transparent background
    ctx.fillStyle = `rgba(0, 0, 0, ${0.3 + effectiveGlitch * 0.3})`
    ctx.fillRect(10, 10, Math.min(400, width - 20), height - 60)
    
    // Border with glitch color shift
    const borderHue = effectiveGlitch > 0.5 ? 300 : 180 // magenta or cyan
    ctx.strokeStyle = `hsl(${borderHue + Math.random() * effectiveGlitch * 60}, 100%, 50%)`
    ctx.lineWidth = 1
    ctx.strokeRect(10, 10, Math.min(400, width - 20), height - 60)
    
    // Terminal lines
    ctx.font = '11px "JetBrains Mono", monospace'
    const visibleLines = lines.slice(-15)
    
    visibleLines.forEach((line, i) => {
      // Glitch offset
      const xOffset = effectiveGlitch > 0 ? (Math.random() - 0.5) * effectiveGlitch * 20 : 0
      const yOffset = effectiveGlitch > 0.3 ? (Math.random() - 0.5) * effectiveGlitch * 5 : 0
      
      // Random glitch skipping
      if (effectiveGlitch > 0.5 && Math.random() < effectiveGlitch * 0.3) {
        return // Skip this line for glitch effect
      }
      
      // Color based on content
      if (line.includes('ERROR') || line.includes('FATAL')) {
        ctx.fillStyle = '#ff4444'
      } else if (line.includes('Time =')) {
        ctx.fillStyle = '#00ffff'
      } else if (line.includes('Courant')) {
        ctx.fillStyle = '#00ff00'
      } else {
        ctx.fillStyle = '#aaaaaa'
      }
      
      // RGB split effect during heavy glitch
      if (effectiveGlitch > 0.7) {
        ctx.fillStyle = '#ff0000'
        ctx.fillText(line.slice(0, 50), 18 + xOffset, 30 + i * 14 + yOffset)
        ctx.fillStyle = '#00ff00'
        ctx.fillText(line.slice(0, 50), 20 + xOffset, 30 + i * 14 + yOffset)
        ctx.fillStyle = '#0000ff'
        ctx.fillText(line.slice(0, 50), 22 + xOffset, 30 + i * 14 + yOffset)
      } else {
        ctx.fillText(line.slice(0, 50), 20 + xOffset, 30 + i * 14 + yOffset)
      }
    })
  }, [])

  // Scanline effect
  const drawScanlines = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number) => {
    if (!paramsRef.current.scanlines) return
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.03)'
    for (let y = 0; y < height; y += 2) {
      ctx.fillRect(0, y, width, 1)
    }
  }, [])

  // Main render loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect()
      if (rect) {
        canvas.width = rect.width
        canvas.height = rect.height
        initStars(200, canvas.width, canvas.height)
      }
    }
    resize()
    window.addEventListener('resize', resize)

    // Animation loop
    const animate = () => {
      timeRef.current += 0.016 // ~60fps
      const time = timeRef.current
      const { width, height } = canvas
      const params = paramsRef.current

      // Clear
      ctx.fillStyle = '#0a0a0f'
      ctx.fillRect(0, 0, width, height)

      // Draw based on phase
      if (phase === 'glitch') {
        // Glitchy transition - mix terminal with noise
        drawStarfield(ctx, width, height, 5 + progress * 10)
        drawTerminalOverlay(ctx, width, height, terminalLines, progress)
        
      } else if (phase === 'colorshift') {
        // RGB shift transition
        ctx.save()
        ctx.globalAlpha = progress
        drawPlasma(
          ctx, 
          Math.floor(width / 4), 
          Math.floor(height / 4), 
          time,
          params.colorCycleSpeed,
          params.waveAmplitude,
          params.waveFrequency
        )
        ctx.drawImage(canvas, 0, 0, width / 4, height / 4, 0, 0, width, height)
        ctx.restore()
        
        ctx.globalAlpha = 1 - progress
        drawTerminalOverlay(ctx, width, height, terminalLines, 1 - progress)
        ctx.globalAlpha = 1
        
      } else if (phase === 'full') {
        // Full keygen mode
        // Background plasma (scaled for performance)
        const plasmaCanvas = document.createElement('canvas')
        plasmaCanvas.width = Math.floor(width / 4)
        plasmaCanvas.height = Math.floor(height / 4)
        const plasmaCtx = plasmaCanvas.getContext('2d')
        if (plasmaCtx) {
          drawPlasma(
            plasmaCtx, 
            plasmaCanvas.width, 
            plasmaCanvas.height, 
            time,
            params.colorCycleSpeed,
            params.waveAmplitude,
            params.waveFrequency
          )
          ctx.drawImage(plasmaCanvas, 0, 0, plasmaCanvas.width, plasmaCanvas.height, 0, 0, width, height)
        }
        
        // Starfield overlay
        ctx.globalAlpha = 0.5
        drawStarfield(ctx, width, height, 15)
        ctx.globalAlpha = 1
        
        // Terminal overlay (semi-transparent)
        drawTerminalOverlay(ctx, width, height, terminalLines, 0)
        
        // Scrolling text with wave
        drawScrollText(ctx, width, height, time, params.scrollSpeed, params.waveAmplitude)
      }

      // Scanline effect
      drawScanlines(ctx, width, height)

      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      cancelAnimationFrame(animationRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [phase, progress, terminalLines, drawPlasma, drawStarfield, drawScrollText, drawTerminalOverlay, drawScanlines, initStars])

  return (
    <div 
      className="relative flex-1 min-h-[200px] max-h-[400px] rounded-lg overflow-hidden keygen-container cursor-pointer"
      onClick={startAudio}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full"
      />
      
      {/* Top bar with controls */}
      <div className="absolute top-2 right-2 flex items-center gap-2 z-10">
        {/* Settings button - only show in full keygen mode */}
        {phase === 'full' && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowParamsPanel(!showParamsPanel)
            }}
            className={`p-1.5 rounded bg-black/50 border transition-colors ${
              showParamsPanel 
                ? 'text-cyan-400 border-cyan-400 bg-cyan-400/20' 
                : 'text-cyan-400/70 border-cyan-400/50 hover:bg-cyan-400/20 hover:text-cyan-400'
            }`}
            title="Adjust audio & visual parameters"
          >
            <Settings className="w-4 h-4" />
          </button>
        )}
        
        {/* Exit button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onExit()
          }}
          className="px-2 py-1 text-xs font-mono bg-black/50 text-cyan-400 border border-cyan-400/50 rounded hover:bg-cyan-400/20 transition-colors"
        >
          [ESC] EXIT
        </button>
      </div>

      {/* Parameters Panel */}
      {showParamsPanel && phase === 'full' && (
        <KeygenParamsPanel
          audioParams={audioParams}
          visualParams={visualParams}
          onParamsChange={handleParamsChange}
          onClose={() => setShowParamsPanel(false)}
        />
      )}

      {/* Click to start audio hint */}
      {!audioStarted && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs font-mono text-cyan-400/50 animate-pulse z-10">
          Click to enable audio
        </div>
      )}
      
      {/* Phase indicator */}
      {phase !== 'normal' && phase !== 'full' && (
        <div className="absolute bottom-2 left-2 text-xs font-mono text-purple-400/70 z-10">
          ▓▒░ {phase.toUpperCase()} ░▒▓
        </div>
      )}
    </div>
  )
}
