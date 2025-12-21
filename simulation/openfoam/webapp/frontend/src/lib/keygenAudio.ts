/**
 * Keygen Audio System
 * 
 * Generates chiptune-style audio using the Web Audio API
 * Inspired by classic demoscene tracker music
 * Now with real-time parameter customization!
 */

export type WaveformType = 'square' | 'sawtooth' | 'triangle' | 'sine'

export interface KeygenAudioParams {
  tempo: number
  arpSpeed: number
  waveform: WaveformType
  filterCutoff: number
  filterResonance: number
  volume: number
  melodyComplexity: number
  bassEnabled: boolean
  drumsEnabled: boolean
}

export const defaultAudioParams: KeygenAudioParams = {
  tempo: 140,
  arpSpeed: 2,
  waveform: 'square',
  filterCutoff: 2000,
  filterResonance: 8,
  volume: 0.3,
  melodyComplexity: 3,
  bassEnabled: true,
  drumsEnabled: true,
}

class KeygenAudio {
  private audioContext: AudioContext | null = null
  private masterGain: GainNode | null = null
  private masterFilter: BiquadFilterNode | null = null
  private isPlaying = false
  private oscillators: OscillatorNode[] = []
  private sequenceInterval: number | null = null
  private params: KeygenAudioParams = { ...defaultAudioParams }

  // Musical scales (pentatonic for that classic chiptune feel)
  private readonly notes: Record<string, number> = {
    C3: 130.81, D3: 146.83, E3: 164.81, G3: 196.00, A3: 220.00,
    C4: 261.63, D4: 293.66, E4: 329.63, G4: 392.00, A4: 440.00,
    C5: 523.25, D5: 587.33, E5: 659.25, G5: 783.99, A5: 880.00,
    C6: 1046.50, D6: 1174.66, E6: 1318.51, G6: 1567.98, A6: 1760.00,
  }

  // Multiple melody patterns for complexity
  private readonly melodies: string[][] = [
    // Simple (complexity 1)
    ['E4', 'G4', 'A4', 'G4'],
    // Medium (complexity 2)
    ['E4', 'G4', 'A4', 'G4', 'E4', 'D4', 'C4', 'D4'],
    // Complex (complexity 3)
    ['E4', 'G4', 'A4', 'G4', 'E4', 'D4', 'C4', 'D4', 'E4', 'E4', 'D4', 'D4', 'E4', 'G4', 'G4', 'E4'],
    // More complex (complexity 4)
    ['A4', 'G4', 'E4', 'D4', 'C4', 'D4', 'E4', 'E4', 'D4', 'D4', 'C4', 'C4', 'D4', 'E4', 'D4', 'C4',
     'E4', 'G4', 'A4', 'G4', 'E4', 'D4', 'C4', 'D4', 'E4', 'E4', 'D4', 'D4', 'E4', 'G4', 'G4', 'E4'],
    // Very complex (complexity 5)
    ['C5', 'A4', 'G4', 'E4', 'D4', 'E4', 'G4', 'A4', 'G4', 'E4', 'D4', 'C4', 'D4', 'E4', 'G4', 'A4',
     'A4', 'G4', 'E4', 'D4', 'C4', 'D4', 'E4', 'E4', 'D4', 'D4', 'C4', 'C4', 'D4', 'E4', 'D4', 'C4'],
  ]

  // Bass patterns
  private readonly bassPatterns: string[][] = [
    ['C3', 'C3', 'G3', 'G3'],
    ['C3', 'G3', 'A3', 'E3'],
    ['C3', 'C3', 'G3', 'G3', 'A3', 'A3', 'E3', 'E3'],
  ]

  // Arpeggio patterns
  private readonly arpPatterns: string[][] = [
    ['C5', 'E5', 'G5', 'E5'],
    ['C5', 'E5', 'G5', 'A5', 'G5', 'E5'],
    ['C5', 'E5', 'G5', 'C6', 'G5', 'E5', 'C5', 'G4'],
  ]

  private stepIndex = 0
  private bassIndex = 0
  private arpIndex = 0

  constructor() {
    // Audio context created on first play
  }

  setParams(newParams: Partial<KeygenAudioParams>): void {
    this.params = { ...this.params, ...newParams }
    
    // Update live audio parameters
    if (this.masterGain) {
      this.masterGain.gain.value = this.params.volume * 0.5
    }
    if (this.masterFilter) {
      this.masterFilter.frequency.value = this.params.filterCutoff
      this.masterFilter.Q.value = this.params.filterResonance
    }
  }

  getParams(): KeygenAudioParams {
    return { ...this.params }
  }

  private initAudio(): boolean {
    if (this.audioContext) return true

    try {
      this.audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
      
      // Master filter
      this.masterFilter = this.audioContext.createBiquadFilter()
      this.masterFilter.type = 'lowpass'
      this.masterFilter.frequency.value = this.params.filterCutoff
      this.masterFilter.Q.value = this.params.filterResonance
      
      // Master volume
      this.masterGain = this.audioContext.createGain()
      this.masterGain.gain.value = this.params.volume * 0.5
      
      this.masterFilter.connect(this.masterGain)
      this.masterGain.connect(this.audioContext.destination)

      return true
    } catch (e) {
      console.error('Failed to initialize audio:', e)
      return false
    }
  }

  private playNote(frequency: number, duration: number, type?: OscillatorType, volume: number = 0.3): void {
    if (!this.audioContext || !this.masterFilter) return

    const osc = this.audioContext.createOscillator()
    const gain = this.audioContext.createGain()

    osc.type = type || this.params.waveform
    osc.frequency.value = frequency

    const now = this.audioContext.currentTime
    
    // ADSR envelope (simplified)
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(volume, now + 0.01) // Attack
    gain.gain.linearRampToValueAtTime(volume * 0.7, now + 0.05) // Decay
    gain.gain.linearRampToValueAtTime(volume * 0.5, now + duration - 0.05) // Sustain
    gain.gain.linearRampToValueAtTime(0, now + duration) // Release

    osc.connect(gain)
    gain.connect(this.masterFilter)

    osc.start(now)
    osc.stop(now + duration)

    this.oscillators.push(osc)
  }

  private playDrum(): void {
    if (!this.audioContext || !this.masterGain || !this.params.drumsEnabled) return

    const now = this.audioContext.currentTime

    // Kick drum (sine wave pitch drop)
    const kickOsc = this.audioContext.createOscillator()
    const kickGain = this.audioContext.createGain()
    
    kickOsc.type = 'sine'
    kickOsc.frequency.setValueAtTime(150, now)
    kickOsc.frequency.exponentialRampToValueAtTime(50, now + 0.1)
    
    kickGain.gain.setValueAtTime(0.5, now)
    kickGain.gain.exponentialRampToValueAtTime(0.01, now + 0.15)
    
    kickOsc.connect(kickGain)
    kickGain.connect(this.masterGain)
    kickOsc.start(now)
    kickOsc.stop(now + 0.15)

    // Hi-hat (noise burst)
    const bufferSize = this.audioContext.sampleRate * 0.05
    const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate)
    const data = buffer.getChannelData(0)
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1
    }
    
    const noise = this.audioContext.createBufferSource()
    const noiseGain = this.audioContext.createGain()
    const noiseFilter = this.audioContext.createBiquadFilter()
    
    noise.buffer = buffer
    noiseFilter.type = 'highpass'
    noiseFilter.frequency.value = 8000
    noiseGain.gain.setValueAtTime(0.1, now + 0.1)
    noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.15)
    
    noise.connect(noiseFilter)
    noiseFilter.connect(noiseGain)
    noiseGain.connect(this.masterGain)
    noise.start(now + 0.1)
    noise.stop(now + 0.15)
  }

  private sequence = (): void => {
    if (!this.isPlaying) return

    const stepDuration = 60 / this.params.tempo / 2 // 8th notes
    
    // Get melody based on complexity
    const melodyIndex = Math.min(this.params.melodyComplexity - 1, this.melodies.length - 1)
    const melody = this.melodies[melodyIndex]
    const bassPattern = this.bassPatterns[Math.min(melodyIndex, this.bassPatterns.length - 1)]
    const arpPattern = this.arpPatterns[Math.min(melodyIndex, this.arpPatterns.length - 1)]

    // Melody (every other step)
    if (this.stepIndex % 2 === 0) {
      const noteIndex = Math.floor(this.stepIndex / 2) % melody.length
      const note = melody[noteIndex]
      if (this.notes[note]) {
        this.playNote(this.notes[note], stepDuration * 1.5, this.params.waveform, 0.25)
      }
    }

    // Bass (every 4 steps)
    if (this.stepIndex % 4 === 0 && this.params.bassEnabled) {
      const bassNote = bassPattern[this.bassIndex % bassPattern.length]
      if (this.notes[bassNote]) {
        this.playNote(this.notes[bassNote], stepDuration * 3, 'sawtooth', 0.2)
      }
      this.bassIndex++
    }

    // Arpeggio (configurable speed)
    if (this.stepIndex % Math.max(1, Math.floor(4 / this.params.arpSpeed)) === 0) {
      const arpNote = arpPattern[this.arpIndex % arpPattern.length]
      if (this.notes[arpNote]) {
        this.playNote(this.notes[arpNote], stepDuration * 0.8, 'triangle', 0.1)
      }
      this.arpIndex++
    }

    // Drums (every 4 steps on beats 0 and 2)
    if (this.stepIndex % 4 === 0) {
      this.playDrum()
    }

    this.stepIndex++
  }

  play(): void {
    if (this.isPlaying) return
    if (!this.initAudio()) return

    this.isPlaying = true
    this.stepIndex = 0
    this.bassIndex = 0
    this.arpIndex = 0

    // Start sequencer
    const stepDuration = (60 / this.params.tempo / 2) * 1000 // ms
    this.sequenceInterval = window.setInterval(this.sequence, stepDuration)
    
    // Initial update for tempo changes
    this.updateTempo()
  }

  private updateTempo(): void {
    if (!this.isPlaying || !this.sequenceInterval) return
    
    // Clear and restart with new tempo
    clearInterval(this.sequenceInterval)
    const stepDuration = (60 / this.params.tempo / 2) * 1000
    this.sequenceInterval = window.setInterval(this.sequence, stepDuration)
  }

  stop(): void {
    this.isPlaying = false

    if (this.sequenceInterval) {
      clearInterval(this.sequenceInterval)
      this.sequenceInterval = null
    }

    // Stop all oscillators
    this.oscillators.forEach(osc => {
      try {
        osc.stop()
      } catch {
        // Already stopped
      }
    })
    this.oscillators = []

    // Fade out master
    if (this.masterGain && this.audioContext) {
      this.masterGain.gain.linearRampToValueAtTime(0, this.audioContext.currentTime + 0.1)
    }
  }

  toggle(): void {
    if (this.isPlaying) {
      this.stop()
    } else {
      this.play()
    }
  }
  
  isActive(): boolean {
    return this.isPlaying
  }
}

// Singleton instance
let keygenAudioInstance: KeygenAudio | null = null

export function getKeygenAudio(): KeygenAudio {
  if (!keygenAudioInstance) {
    keygenAudioInstance = new KeygenAudio()
  }
  return keygenAudioInstance
}
