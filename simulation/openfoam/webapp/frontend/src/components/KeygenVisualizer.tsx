/**
 * Keygen Mode Visualizer
 * 
 * Demoscene-inspired visual effects that activate during simulation
 * Features: ASCII wave animations, plasma effects, 3D text, starfield
 * Focus on ASCII character art with size/position waves for visual depth
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
}

export const defaultVisualParams: KeygenVisualParams = {
  scrollSpeed: 1,
  waveAmplitude: 15,
  waveFrequency: 2,
  colorCycleSpeed: 1,
  glitchIntensity: 0.3,
  starfieldEnabled: true,
}

interface KeygenVisualizerProps {
  phase: KeygenPhase
  progress: number
  terminalLines: string[]
  onExit: () => void
}

// ASCII characters for wave effects (ordered by visual density - light to dark)
const ASCII_CHARS = ' .\'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'

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

  // Draw ASCII wave field - characters that undulate in size/position (greyscale density)
  const drawASCIIWaveField = useCallback((
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    time: number,
    intensity: number, // 0-1 transition intensity
    params: KeygenVisualParams
  ) => {
    const cols = Math.floor(width / 14)
    const rows = Math.floor(height / 18)
    
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const x = col * 14 + 7
        const y = row * 18 + 9
        
        // Multiple wave functions for complexity
        const wave1 = Math.sin(col * 0.2 + time * params.scrollSpeed) 
        const wave2 = Math.sin(row * 0.15 + time * params.scrollSpeed * 0.7)
        const wave3 = Math.sin((col + row) * 0.1 + time * params.colorCycleSpeed)
        const wave4 = Math.sin(Math.sqrt(col * col + row * row) * 0.08 + time * 0.8)
        
        // Combine waves
        const combinedWave = (wave1 + wave2 + wave3 + wave4) / 4
        
        // Character based on wave value (density mapping)
        const charIndex = Math.floor((combinedWave + 1) / 2 * (ASCII_CHARS.length - 1))
        const char = ASCII_CHARS[Math.max(0, Math.min(charIndex, ASCII_CHARS.length - 1))]
        
        // Font size varies with wave for depth effect
        const baseSize = 11
        const sizeWave = Math.sin(col * 0.25 - row * 0.15 + time * 1.5) * params.waveAmplitude * 0.25
        const fontSize = Math.max(6, baseSize + sizeWave * intensity)
        
        // Position offset for 3D-like depth
        const depthOffset = combinedWave * params.waveAmplitude * intensity
        const xOffset = Math.sin(row * 0.4 + time * 0.8) * depthOffset * 0.25
        const yOffset = depthOffset * 0.4
        
        // Greyscale brightness based on density (denser chars = brighter)
        const brightness = 30 + (charIndex / ASCII_CHARS.length) * 60
        const alpha = 0.4 + intensity * 0.6
        
        ctx.font = `${fontSize}px "JetBrains Mono", monospace`
        ctx.fillStyle = `rgba(${brightness + 20}, ${brightness + 20}, ${brightness}, ${alpha})`
        ctx.fillText(char, x + xOffset, y + yOffset)
      }
    }
  }, [])

  // Draw terminal text with progressive ASCII corruption (greyscale)
  const drawTerminalWithTransition = useCallback((
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    lines: string[],
    corruptionLevel: number, // 0 = normal, 1 = fully ASCII
    time: number,
    params: KeygenVisualParams
  ) => {
    const visibleLines = lines.slice(-18)
    const lineHeight = 14
    const startY = 25
    const startX = 15
    const maxWidth = Math.min(450, width - 30)
    
    // Background with variable transparency
    const bgAlpha = 0.75 - corruptionLevel * 0.35
    ctx.fillStyle = `rgba(8, 8, 12, ${bgAlpha})`
    ctx.fillRect(10, 10, maxWidth + 10, height - 50)
    
    // Border - greyscale, fades with corruption
    const borderBright = 100 - corruptionLevel * 50
    ctx.strokeStyle = `rgba(${borderBright}, ${borderBright}, ${borderBright + 10}, ${0.6 - corruptionLevel * 0.3})`
    ctx.lineWidth = 1
    ctx.strokeRect(10, 10, maxWidth + 10, height - 50)
    
    visibleLines.forEach((line, i) => {
      const y = startY + i * lineHeight
      
      // Determine if this line should be corrupted
      const lineCorruption = Math.max(0, corruptionLevel - (i / visibleLines.length) * 0.5)
      
      // Base brightness levels for different content types
      let baseBrightness = 130
      if (line.includes('Time =')) baseBrightness = 200
      else if (line.includes('Courant')) baseBrightness = 180
      else if (line.includes('ERROR')) baseBrightness = 220
      else if (line.includes('DROPLET') || line.includes('droplet')) baseBrightness = 200
      
      if (lineCorruption < 0.3) {
        // Mostly normal text with slight glitch
        ctx.font = '11px "JetBrains Mono", monospace'
        const xOffset = lineCorruption > 0.1 ? (Math.random() - 0.5) * lineCorruption * 8 : 0
        ctx.fillStyle = `rgb(${baseBrightness}, ${baseBrightness}, ${baseBrightness})`
        ctx.fillText(line.slice(0, 55), startX + xOffset, y)
      } else if (lineCorruption < 0.7) {
        // Partially corrupted - mix of normal and ASCII
        ctx.font = '11px "JetBrains Mono", monospace'
        const chars = line.slice(0, 55).split('')
        let x = startX
        
        chars.forEach((char, j) => {
          const charCorrupt = Math.random() < lineCorruption - 0.3
          const waveOffset = Math.sin(j * 0.3 + time * 2) * lineCorruption * 4
          
          if (charCorrupt && char !== ' ') {
            // Replace with wave-based ASCII
            const waveVal = Math.sin(j * 0.5 + i * 0.3 + time * 3)
            const asciiIdx = Math.floor((waveVal + 1) / 2 * 30) + 30
            const replacementChar = ASCII_CHARS[Math.min(asciiIdx, ASCII_CHARS.length - 1)]
            // Greyscale brightness based on character density
            const bright = 80 + (asciiIdx / ASCII_CHARS.length) * 120
            ctx.fillStyle = `rgb(${bright}, ${bright}, ${bright})`
            ctx.fillText(replacementChar, x, y + waveOffset)
          } else {
            ctx.fillStyle = `rgb(${baseBrightness}, ${baseBrightness}, ${baseBrightness})`
            ctx.fillText(char, x, y + waveOffset * 0.3)
          }
          x += 6.6
        })
      } else {
        // Heavily corrupted - almost all ASCII with wave motion
        const fontSize = 10 + Math.sin(i + time * 2) * 2
        ctx.font = `${fontSize}px "JetBrains Mono", monospace`
        
        const chars = line.slice(0, 55).split('')
        let x = startX
        
        chars.forEach((char, j) => {
          const waveY = Math.sin(j * 0.4 + time * 3) * params.waveAmplitude * 0.4
          const waveX = Math.cos(j * 0.3 + time * 2) * 2
          
          // Convert to density-based ASCII
          const density = ((j + i) * 17 + Math.floor(time * 10)) % ASCII_CHARS.length
          const displayChar = char === ' ' ? ' ' : ASCII_CHARS[density]
          
          // Greyscale based on density
          const bright = 60 + (density / ASCII_CHARS.length) * 140
          ctx.fillStyle = `rgb(${bright}, ${bright}, ${bright})`
          ctx.fillText(displayChar, x + waveX, y + waveY)
          x += 6.6
        })
      }
    })
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

  const drawStarfield = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, speed: number, alpha: number = 1) => {
    if (!paramsRef.current.starfieldEnabled) return
    
    const cx = width / 2
    const cy = height / 2
    
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
      
      const brightness = (1 - star.z / 1000) * alpha
      ctx.fillStyle = `rgba(255, 255, 255, ${brightness})`
      ctx.beginPath()
      ctx.arc(sx, sy, size, 0, Math.PI * 2)
      ctx.fill()
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

      // Clear with dark background
      ctx.fillStyle = '#0a0a12'
      ctx.fillRect(0, 0, width, height)

      // Draw based on phase with smooth transitions
      if (phase === 'normal') {
        // Pure terminal - should not reach here but just in case
        drawTerminalWithTransition(ctx, width, height, terminalLines, 0, time, params)
        
      } else if (phase === 'glitch') {
        // Smooth transition: terminal starts corrupting, stars appear
        const starAlpha = progress * 0.25
        drawStarfield(ctx, width, height, 3 + progress * 5, starAlpha)
        
        // Terminal with increasing corruption
        drawTerminalWithTransition(ctx, width, height, terminalLines, progress * 0.5, time, params)
        
      } else if (phase === 'colorshift') {
        // ASCII field fades in behind corrupting terminal
        const asciiAlpha = progress
        ctx.globalAlpha = asciiAlpha * 0.4
        drawASCIIWaveField(ctx, width, height, time, progress, params)
        ctx.globalAlpha = 1
        
        // Stars getting faster
        drawStarfield(ctx, width, height, 8 + progress * 7, 0.25 + progress * 0.15)
        
        // Terminal continues corrupting
        const corruption = 0.5 + progress * 0.5
        drawTerminalWithTransition(ctx, width, height, terminalLines, corruption, time, params)
        
      } else if (phase === 'full') {
        // Full keygen mode - ASCII density waves dominate
        
        // Background ASCII wave field
        ctx.globalAlpha = 0.7
        drawASCIIWaveField(ctx, width, height, time, 1, params)
        ctx.globalAlpha = 1
        
        // Subtle starfield overlay
        drawStarfield(ctx, width, height, 10, 0.3)
        
        // Terminal still visible but heavily stylized
        drawTerminalWithTransition(ctx, width, height, terminalLines, 0.85, time, params)
      }

      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      cancelAnimationFrame(animationRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [phase, progress, terminalLines, drawASCIIWaveField, drawTerminalWithTransition, drawStarfield, initStars])

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
                ? 'text-white border-white/50 bg-white/10' 
                : 'text-white/70 border-white/30 hover:bg-white/10 hover:text-white'
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
          className="px-2 py-1 text-xs font-mono bg-black/50 text-white/80 border border-white/30 rounded hover:bg-white/10 transition-colors"
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
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs font-mono text-white/40 animate-pulse z-10">
          Click to enable audio
        </div>
      )}
      
      {/* Phase indicator - subtle during transitions */}
      {phase !== 'normal' && phase !== 'full' && (
        <div className="absolute bottom-2 left-2 text-xs font-mono text-white/30 z-10">
          {phase === 'glitch' && '░▒▓'}
          {phase === 'colorshift' && '▓▒░ INITIALIZING ░▒▓'}
        </div>
      )}
    </div>
  )
}
