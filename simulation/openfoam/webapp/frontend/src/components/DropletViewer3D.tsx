import { useState, useEffect, useRef, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Grid, Text } from '@react-three/drei'
import { Play, Pause, SkipBack, SkipForward, Maximize2 } from 'lucide-react'
import * as THREE from 'three'
import { api } from '../lib/api'

interface DropletViewer3DProps {
  caseId: string | null
}

// T-Junction geometry component
function TJunctionGeometry() {
  const geometry = useRef<THREE.Group>(null)
  
  // Channel dimensions (matching OpenFOAM case)
  const channelWidth = 0.00015 // 150 µm
  const channelHeight = 0.00008 // 80 µm
  const mainLength = 0.00165 // 1.65 mm
  const sideLength = 0.0003 // 300 µm
  
  // Scale up for visibility
  const scale = 5000

  return (
    <group ref={geometry} scale={[scale, scale, scale]}>
      {/* Main channel (oil inlet to outlet) */}
      <mesh position={[mainLength / 2, channelHeight / 2, channelWidth / 2]}>
        <boxGeometry args={[mainLength, channelHeight, channelWidth]} />
        <meshStandardMaterial 
          color="#1e3a5f" 
          transparent 
          opacity={0.3}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Side channel (water inlet) */}
      <mesh position={[mainLength * 0.35, channelHeight / 2 + sideLength / 2, channelWidth / 2]}>
        <boxGeometry args={[channelWidth * 0.5, sideLength, channelWidth]} />
        <meshStandardMaterial 
          color="#1e3a5f" 
          transparent 
          opacity={0.3}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Inlet/Outlet labels */}
      <Text
        position={[-0.0001, channelHeight / 2, channelWidth]}
        fontSize={0.00005}
        color="#3b82f6"
        anchorX="center"
      >
        Oil In
      </Text>
      <Text
        position={[mainLength + 0.0001, channelHeight / 2, channelWidth]}
        fontSize={0.00005}
        color="#3b82f6"
        anchorX="center"
      >
        Out
      </Text>
      <Text
        position={[mainLength * 0.35, channelHeight + sideLength + 0.00005, channelWidth]}
        fontSize={0.00005}
        color="#06b6d4"
        anchorX="center"
      >
        Water In
      </Text>
    </group>
  )
}

// Animated droplets (placeholder - would be replaced with actual VTK data)
function AnimatedDroplets({ timeStep, playing }: { timeStep: number; playing: boolean }) {
  const dropletsRef = useRef<THREE.Group>(null)
  const [droplets, setDroplets] = useState<{ x: number; size: number }[]>([])
  
  // Generate sample droplets based on time
  useEffect(() => {
    const numDroplets = Math.floor(timeStep / 0.01) + 1
    const newDroplets = []
    for (let i = 0; i < numDroplets; i++) {
      newDroplets.push({
        x: 3 + i * 1.5, // Position along channel
        size: 0.3 + Math.random() * 0.2,
      })
    }
    setDroplets(newDroplets)
  }, [timeStep])

  useFrame(() => {
    if (dropletsRef.current && playing) {
      // Animate droplets moving along channel
      dropletsRef.current.children.forEach((child, i) => {
        child.position.x += 0.02
        if (child.position.x > 8) {
          child.position.x = 3 + i * 0.5
        }
      })
    }
  })

  return (
    <group ref={dropletsRef}>
      {droplets.map((droplet, i) => (
        <mesh key={i} position={[droplet.x, 0.4, 0.4]}>
          <sphereGeometry args={[droplet.size, 16, 16]} />
          <meshStandardMaterial
            color="#06b6d4"
            transparent
            opacity={0.8}
            roughness={0.1}
            metalness={0.2}
          />
        </mesh>
      ))}
    </group>
  )
}

// Scene setup
function Scene({ timeStep, playing }: { timeStep: number; playing: boolean }) {
  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} />
      
      <TJunctionGeometry />
      <AnimatedDroplets timeStep={timeStep} playing={playing} />
      
      <Grid
        position={[4, 0, 0]}
        args={[20, 20]}
        cellSize={0.5}
        cellThickness={0.5}
        cellColor="#1e3a5f"
        sectionSize={2}
        sectionThickness={1}
        sectionColor="#3b82f6"
        fadeDistance={30}
        fadeStrength={1}
      />
      
      <OrbitControls 
        enableDamping
        dampingFactor={0.05}
        minDistance={2}
        maxDistance={20}
      />
      <PerspectiveCamera makeDefault position={[4, 5, 8]} fov={50} />
    </>
  )
}

export default function DropletViewer3D({ caseId }: DropletViewer3DProps) {
  const [timeStep, setTimeStep] = useState(0)
  const [maxTime, setMaxTime] = useState(0.05)
  const [playing, setPlaying] = useState(false)
  const [, setOutputTimes] = useState<number[]>([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Fetch available time steps
  useEffect(() => {
    if (!caseId) return
    
    const fetchTimes = async () => {
      try {
        const { times } = await api.getOutputTimes(caseId)
        setOutputTimes(times)
        if (times.length > 0) {
          setMaxTime(times[times.length - 1])
        }
      } catch {
        // Use default times
      }
    }
    fetchTimes()
  }, [caseId])

  // Animation loop
  useEffect(() => {
    if (!playing) return
    
    const interval = setInterval(() => {
      setTimeStep((prev) => {
        const next = prev + 0.001
        return next > maxTime ? 0 : next
      })
    }, 50)
    
    return () => clearInterval(interval)
  }, [playing, maxTime])

  const toggleFullscreen = () => {
    if (!containerRef.current) return
    
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  return (
    <div 
      ref={containerRef}
      className={`glass-card overflow-hidden ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      {/* Controls header */}
      <div className="p-4 border-b border-border/50 flex items-center justify-between bg-background/50">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold">3D Droplet Visualization</h2>
          <div className="text-sm text-muted-foreground font-mono">
            t = {timeStep.toFixed(4)} s
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Playback controls */}
          <button
            onClick={() => setTimeStep(0)}
            className="p-2 rounded-lg hover:bg-secondary transition-colors"
            title="Reset"
          >
            <SkipBack className="w-4 h-4" />
          </button>
          <button
            onClick={() => setPlaying(!playing)}
            className={`p-2 rounded-lg transition-colors ${
              playing ? 'bg-primary text-white' : 'hover:bg-secondary'
            }`}
            title={playing ? 'Pause' : 'Play'}
          >
            {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setTimeStep(maxTime)}
            className="p-2 rounded-lg hover:bg-secondary transition-colors"
            title="End"
          >
            <SkipForward className="w-4 h-4" />
          </button>
          
          <div className="w-px h-6 bg-border mx-2" />
          
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg hover:bg-secondary transition-colors"
            title="Fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Time slider */}
      <div className="px-4 py-2 bg-background/30">
        <input
          type="range"
          min={0}
          max={maxTime}
          step={0.0001}
          value={timeStep}
          onChange={(e) => setTimeStep(Number(e.target.value))}
          className="w-full h-1 bg-secondary rounded-lg appearance-none cursor-pointer accent-accent"
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>0 s</span>
          <span>{maxTime.toFixed(3)} s</span>
        </div>
      </div>

      {/* 3D Canvas */}
      <div className={`${isFullscreen ? 'h-[calc(100%-120px)]' : 'h-[500px]'}`}>
        <Canvas>
          <Suspense fallback={null}>
            <Scene timeStep={timeStep} playing={playing} />
          </Suspense>
        </Canvas>
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-border/50 bg-background/50 flex items-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-cyan-400" />
          <span className="text-sm text-muted-foreground">Water Droplets</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-primary/30 border border-primary/50" />
          <span className="text-sm text-muted-foreground">Channel Walls</span>
        </div>
        <div className="ml-auto text-xs text-muted-foreground">
          Drag to rotate • Scroll to zoom • Shift+drag to pan
        </div>
      </div>
    </div>
  )
}

