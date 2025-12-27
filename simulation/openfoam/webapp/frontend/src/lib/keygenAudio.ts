/**
 * Keygen Audio System v2.0
 * 
 * Advanced chiptune-style audio using the Web Audio API
 * Inspired by mid-2000s demoscene tracker music (Fairlight, TPOLM, etc.)
 * Features: multi-voice layering, echo, vibrato, complex progressions, filter envelopes
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
  tempo: 138,
  arpSpeed: 2,
  waveform: 'square',
  filterCutoff: 3000,
  filterResonance: 6,
  volume: 0.35,
  melodyComplexity: 3,
  bassEnabled: true,
  drumsEnabled: true,
}

// Note frequencies for chromatic scale (allows more complex harmonies)
const NOTE_FREQ: Record<string, number> = {
  // Octave 2 (deep bass)
  'C2': 65.41, 'C#2': 69.30, 'D2': 73.42, 'D#2': 77.78, 'E2': 82.41, 'F2': 87.31,
  'F#2': 92.50, 'G2': 98.00, 'G#2': 103.83, 'A2': 110.00, 'A#2': 116.54, 'B2': 123.47,
  // Octave 3 (bass)
  'C3': 130.81, 'C#3': 138.59, 'D3': 146.83, 'D#3': 155.56, 'E3': 164.81, 'F3': 174.61,
  'F#3': 185.00, 'G3': 196.00, 'G#3': 207.65, 'A3': 220.00, 'A#3': 233.08, 'B3': 246.94,
  // Octave 4 (mid)
  'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13, 'E4': 329.63, 'F4': 349.23,
  'F#4': 369.99, 'G4': 392.00, 'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
  // Octave 5 (high)
  'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25, 'E5': 659.25, 'F5': 698.46,
  'F#5': 739.99, 'G5': 783.99, 'G#5': 830.61, 'A5': 880.00, 'A#5': 932.33, 'B5': 987.77,
  // Octave 6 (very high)
  'C6': 1046.50, 'C#6': 1108.73, 'D6': 1174.66, 'D#6': 1244.51, 'E6': 1318.51, 'F6': 1396.91,
  'F#6': 1479.98, 'G6': 1567.98, 'G#6': 1661.22, 'A6': 1760.00, 'A#6': 1864.66, 'B6': 1975.53,
}

// Chord definitions for richer harmony
type ChordType = 'min' | 'maj' | 'min7' | 'maj7' | 'dim' | 'sus4' | 'add9'
interface Chord {
  root: string
  type: ChordType
  notes: string[]
}

// Song sections for structure
interface SongSection {
  name: string
  bars: number
  intensity: number // 0-1
  chordProgression: number[] // indices into chord array
  melodyPattern: number
  hasLead: boolean
  hasPad: boolean
  drumPattern: number
}

class KeygenAudio {
  private audioContext: AudioContext | null = null
  private masterGain: GainNode | null = null
  private masterFilter: BiquadFilterNode | null = null
  private delayNode: DelayNode | null = null
  private delayGain: GainNode | null = null
  private feedbackGain: GainNode | null = null
  private isPlaying = false
  private params: KeygenAudioParams = { ...defaultAudioParams }
  
  // Timing
  private stepIndex = 0
  private barIndex = 0
  private sectionIndex = 0
  private ticksPerBeat = 4 // 16th note resolution
  
  // LFO for filter sweeps
  private filterLFO: OscillatorNode | null = null
  private filterLFOGain: GainNode | null = null
  
  // Sequencer
  private sequenceInterval: number | null = null
  private nextNoteTime = 0
  private scheduleAheadTime = 0.1 // seconds
  private lookAhead = 25 // ms
  
  // Current song state
  private currentChordIndex = 0
  private leadNoteIndex = 0
  private arpNoteIndex = 0
  private bassPatternIndex = 0
  
  // A minor / C major based progressions (classic demoscene)
  private readonly chords: Chord[] = [
    { root: 'A', type: 'min', notes: ['A3', 'C4', 'E4'] },
    { root: 'F', type: 'maj', notes: ['F3', 'A3', 'C4'] },
    { root: 'C', type: 'maj', notes: ['C3', 'E3', 'G3'] },
    { root: 'G', type: 'maj', notes: ['G3', 'B3', 'D4'] },
    { root: 'D', type: 'min', notes: ['D3', 'F3', 'A3'] },
    { root: 'E', type: 'min', notes: ['E3', 'G3', 'B3'] },
    { root: 'A', type: 'min7', notes: ['A3', 'C4', 'E4', 'G4'] },
    { root: 'E', type: 'maj', notes: ['E3', 'G#3', 'B3'] }, // V chord for tension
  ]
  
  // Song structure - builds up over time
  private readonly songSections: SongSection[] = [
    { name: 'intro', bars: 4, intensity: 0.3, chordProgression: [0, 0, 0, 0], melodyPattern: 0, hasLead: false, hasPad: true, drumPattern: 0 },
    { name: 'buildup', bars: 4, intensity: 0.5, chordProgression: [0, 5, 1, 4], melodyPattern: 1, hasLead: true, hasPad: true, drumPattern: 1 },
    { name: 'verse1', bars: 8, intensity: 0.7, chordProgression: [0, 5, 1, 2, 0, 5, 3, 7], melodyPattern: 2, hasLead: true, hasPad: true, drumPattern: 2 },
    { name: 'chorus', bars: 8, intensity: 1.0, chordProgression: [1, 2, 0, 7, 1, 2, 4, 7], melodyPattern: 3, hasLead: true, hasPad: true, drumPattern: 3 },
    { name: 'breakdown', bars: 4, intensity: 0.4, chordProgression: [0, 6, 0, 6], melodyPattern: 1, hasLead: false, hasPad: true, drumPattern: 0 },
    { name: 'verse2', bars: 8, intensity: 0.8, chordProgression: [0, 5, 1, 2, 4, 5, 3, 7], melodyPattern: 2, hasLead: true, hasPad: true, drumPattern: 2 },
    { name: 'finalChorus', bars: 8, intensity: 1.0, chordProgression: [1, 2, 0, 7, 1, 2, 3, 7], melodyPattern: 4, hasLead: true, hasPad: true, drumPattern: 3 },
    { name: 'outro', bars: 4, intensity: 0.5, chordProgression: [0, 0, 6, 0], melodyPattern: 0, hasLead: false, hasPad: true, drumPattern: 1 },
  ]
  
  // Lead melody patterns (relative to chord root, in semitones)
  private readonly leadPatterns: number[][] = [
    // Pattern 0: Simple hold
    [0, -1, 0, -1, 0, -1, 0, -1, 0, -1, 0, -1, 0, -1, 0, -1],
    // Pattern 1: Gentle movement
    [0, 2, 4, 2, 0, -1, 2, 4, 7, 4, 2, 0, -1, 0, 2, 0],
    // Pattern 2: Active melody
    [0, 2, 4, 7, 9, 7, 4, 2, 0, 4, 7, 12, 9, 7, 4, 0],
    // Pattern 3: Energetic (chorus)
    [12, 11, 9, 7, 9, 11, 12, 14, 12, 9, 7, 4, 7, 9, 11, 12],
    // Pattern 4: Final climax
    [12, 14, 16, 14, 12, 11, 9, 7, 12, 14, 16, 19, 16, 14, 12, 11],
  ]
  
  // Arpeggio patterns (chord tone indices + octave shifts)
  private readonly arpPatterns: { tone: number; octave: number }[][] = [
    // Pattern 0: Simple up
    [{ tone: 0, octave: 0 }, { tone: 1, octave: 0 }, { tone: 2, octave: 0 }, { tone: 1, octave: 0 }],
    // Pattern 1: Up-down
    [{ tone: 0, octave: 0 }, { tone: 1, octave: 0 }, { tone: 2, octave: 0 }, { tone: 2, octave: 1 }, { tone: 2, octave: 0 }, { tone: 1, octave: 0 }],
    // Pattern 2: Wide sweep
    [{ tone: 0, octave: 0 }, { tone: 2, octave: 0 }, { tone: 0, octave: 1 }, { tone: 2, octave: 1 }, { tone: 0, octave: 2 }, { tone: 2, octave: 1 }, { tone: 0, octave: 1 }, { tone: 2, octave: 0 }],
    // Pattern 3: Rapid
    [{ tone: 0, octave: 0 }, { tone: 1, octave: 0 }, { tone: 2, octave: 0 }, { tone: 0, octave: 1 }, { tone: 1, octave: 1 }, { tone: 2, octave: 1 }],
  ]
  
  // Bass patterns (rhythmic, with octave drops)
  private readonly bassPatterns: { step: number; octave: number; duration: number }[][] = [
    // Pattern 0: Simple quarter notes
    [{ step: 0, octave: 0, duration: 4 }, { step: 8, octave: 0, duration: 4 }],
    // Pattern 1: Eighth notes
    [{ step: 0, octave: 0, duration: 2 }, { step: 4, octave: 0, duration: 2 }, { step: 8, octave: 0, duration: 2 }, { step: 12, octave: 0, duration: 2 }],
    // Pattern 2: Syncopated
    [{ step: 0, octave: 0, duration: 3 }, { step: 3, octave: -1, duration: 1 }, { step: 6, octave: 0, duration: 2 }, { step: 10, octave: 0, duration: 2 }, { step: 14, octave: -1, duration: 2 }],
    // Pattern 3: Driving eighths with octave jumps
    [{ step: 0, octave: 0, duration: 2 }, { step: 2, octave: -1, duration: 2 }, { step: 4, octave: 0, duration: 2 }, { step: 6, octave: 0, duration: 2 }, 
     { step: 8, octave: 0, duration: 2 }, { step: 10, octave: -1, duration: 2 }, { step: 12, octave: 0, duration: 2 }, { step: 14, octave: -1, duration: 2 }],
  ]
  
  // Drum patterns (16 steps per bar)
  private readonly drumPatterns: { kick: number[]; snare: number[]; hihat: number[]; openhat: number[] }[] = [
    // Pattern 0: Minimal
    { kick: [0, 8], snare: [], hihat: [0, 4, 8, 12], openhat: [] },
    // Pattern 1: Basic beat
    { kick: [0, 8], snare: [4, 12], hihat: [0, 2, 4, 6, 8, 10, 12, 14], openhat: [] },
    // Pattern 2: Four on floor
    { kick: [0, 4, 8, 12], snare: [4, 12], hihat: [0, 2, 4, 6, 8, 10, 12, 14], openhat: [6, 14] },
    // Pattern 3: Energetic
    { kick: [0, 3, 6, 8, 11, 14], snare: [4, 12], hihat: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], openhat: [2, 6, 10, 14] },
  ]
  
  constructor() {}

  setParams(newParams: Partial<KeygenAudioParams>): void {
    const oldTempo = this.params.tempo
    this.params = { ...this.params, ...newParams }
    
    // Update live audio parameters
    if (this.masterGain) {
      this.masterGain.gain.value = this.params.volume * 0.4
    }
    if (this.masterFilter) {
      this.masterFilter.frequency.value = this.params.filterCutoff
      this.masterFilter.Q.value = this.params.filterResonance
    }
    
    // Restart sequencer if tempo changed
    if (oldTempo !== this.params.tempo && this.isPlaying) {
      this.restartSequencer()
    }
  }

  getParams(): KeygenAudioParams {
    return { ...this.params }
  }

  private initAudio(): boolean {
    if (this.audioContext) return true

    try {
      this.audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
      
      // Master filter with LFO modulation
      this.masterFilter = this.audioContext.createBiquadFilter()
      this.masterFilter.type = 'lowpass'
      this.masterFilter.frequency.value = this.params.filterCutoff
      this.masterFilter.Q.value = this.params.filterResonance
      
      // Filter LFO for subtle movement
      this.filterLFO = this.audioContext.createOscillator()
      this.filterLFOGain = this.audioContext.createGain()
      this.filterLFO.type = 'sine'
      this.filterLFO.frequency.value = 0.2 // Slow sweep
      this.filterLFOGain.gain.value = 500 // Modulation depth
      this.filterLFO.connect(this.filterLFOGain)
      this.filterLFOGain.connect(this.masterFilter.frequency)
      this.filterLFO.start()
      
      // Delay/echo effect
      this.delayNode = this.audioContext.createDelay(1.0)
      this.delayNode.delayTime.value = 60 / this.params.tempo / 2 // Sync to tempo (8th note)
      
      this.delayGain = this.audioContext.createGain()
      this.delayGain.gain.value = 0.25 // Delay mix
      
      this.feedbackGain = this.audioContext.createGain()
      this.feedbackGain.gain.value = 0.3 // Feedback amount
      
      // Master volume
      this.masterGain = this.audioContext.createGain()
      this.masterGain.gain.value = this.params.volume * 0.4
      
      // Routing: filter -> delay -> master
      this.masterFilter.connect(this.delayNode)
      this.delayNode.connect(this.delayGain)
      this.delayGain.connect(this.masterGain)
      
      // Feedback loop
      this.delayNode.connect(this.feedbackGain)
      this.feedbackGain.connect(this.delayNode)
      
      // Dry signal
      this.masterFilter.connect(this.masterGain)
      
      this.masterGain.connect(this.audioContext.destination)

      return true
    } catch (e) {
      console.error('Failed to initialize audio:', e)
      return false
    }
  }
  
  // Get frequency with semitone offset
  private getFrequency(baseNote: string, semitones: number = 0): number {
    const baseFreq = NOTE_FREQ[baseNote] || 440
    return baseFreq * Math.pow(2, semitones / 12)
  }
  
  // Play a single voice with ADSR and optional vibrato
  private playVoice(
    frequency: number, 
    duration: number, 
    waveform: OscillatorType,
    volume: number,
    attack: number = 0.01,
    decay: number = 0.1,
    sustain: number = 0.7,
    release: number = 0.1,
    vibrato: number = 0,
    vibratoSpeed: number = 5,
    detune: number = 0,
    filterEnvAmount: number = 0
  ): void {
    if (!this.audioContext || !this.masterFilter) return
    
    const now = this.audioContext.currentTime
    
    // Main oscillator
    const osc = this.audioContext.createOscillator()
    const gain = this.audioContext.createGain()
    
    // Per-voice filter for filter envelope
    const voiceFilter = this.audioContext.createBiquadFilter()
    voiceFilter.type = 'lowpass'
    voiceFilter.Q.value = 2
    
    osc.type = waveform
    osc.frequency.value = frequency
    osc.detune.value = detune
    
    // Vibrato LFO
    if (vibrato > 0) {
      const vibratoLFO = this.audioContext.createOscillator()
      const vibratoGain = this.audioContext.createGain()
      vibratoLFO.type = 'sine'
      vibratoLFO.frequency.value = vibratoSpeed
      vibratoGain.gain.value = vibrato
      vibratoLFO.connect(vibratoGain)
      vibratoGain.connect(osc.frequency)
      vibratoLFO.start(now)
      vibratoLFO.stop(now + duration + release)
    }
    
    // ADSR envelope
    const peakTime = now + attack
    const decayEndTime = peakTime + decay
    const releaseStart = now + duration
    const endTime = releaseStart + release
    
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(volume, peakTime)
    gain.gain.linearRampToValueAtTime(volume * sustain, decayEndTime)
    gain.gain.setValueAtTime(volume * sustain, releaseStart)
    gain.gain.linearRampToValueAtTime(0, endTime)
    
    // Filter envelope
    const filterBase = Math.min(this.params.filterCutoff, 2000)
    voiceFilter.frequency.setValueAtTime(filterBase, now)
    voiceFilter.frequency.linearRampToValueAtTime(filterBase + filterEnvAmount, peakTime)
    voiceFilter.frequency.linearRampToValueAtTime(filterBase + filterEnvAmount * 0.3, decayEndTime)
    
    osc.connect(voiceFilter)
    voiceFilter.connect(gain)
    gain.connect(this.masterFilter)
    
    osc.start(now)
    osc.stop(endTime)
  }
  
  // Play a rich, detuned chord pad
  private playPad(notes: string[], duration: number, volume: number): void {
    const detunes = [-8, 0, 8] // Slight detuning for richness
    
    notes.forEach((note, i) => {
      const freq = NOTE_FREQ[note]
      if (!freq) return
      
      // Multiple detuned voices per note
      detunes.forEach(detune => {
        this.playVoice(
          freq,
          duration,
          'sawtooth',
          volume * 0.15,
          0.3,  // Slow attack
          0.2,
          0.8,
          0.5,  // Long release
          2,    // Subtle vibrato
          4,
          detune + (i * 2), // Spread detuning
          200
        )
      })
    })
  }
  
  // Play lead with expression
  private playLead(note: string, duration: number, volume: number, slideFrom?: string): void {
    const freq = NOTE_FREQ[note]
    if (!freq || !this.audioContext || !this.masterFilter) return
    
    const now = this.audioContext.currentTime
    const osc = this.audioContext.createOscillator()
    const gain = this.audioContext.createGain()
    
    osc.type = this.params.waveform
    
    // Pitch slide (portamento)
    if (slideFrom && NOTE_FREQ[slideFrom]) {
      osc.frequency.setValueAtTime(NOTE_FREQ[slideFrom], now)
      osc.frequency.exponentialRampToValueAtTime(freq, now + 0.05)
    } else {
      osc.frequency.value = freq
    }
    
    // Add a second detuned oscillator for thickness
    const osc2 = this.audioContext.createOscillator()
    osc2.type = this.params.waveform === 'square' ? 'sawtooth' : 'square'
    osc2.frequency.value = freq
    osc2.detune.value = 7
    
    // Vibrato
    const vibratoLFO = this.audioContext.createOscillator()
    const vibratoGain = this.audioContext.createGain()
    vibratoLFO.type = 'sine'
    vibratoLFO.frequency.value = 5.5
    vibratoGain.gain.setValueAtTime(0, now)
    vibratoGain.gain.linearRampToValueAtTime(6, now + 0.2) // Delayed vibrato
    vibratoLFO.connect(vibratoGain)
    vibratoGain.connect(osc.frequency)
    vibratoGain.connect(osc2.frequency)
    vibratoLFO.start(now)
    vibratoLFO.stop(now + duration + 0.2)
    
    // Envelope
    const peakTime = now + 0.02
    const endTime = now + duration + 0.15
    
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(volume, peakTime)
    gain.gain.linearRampToValueAtTime(volume * 0.7, now + 0.1)
    gain.gain.setValueAtTime(volume * 0.6, now + duration)
    gain.gain.linearRampToValueAtTime(0, endTime)
    
    osc.connect(gain)
    osc2.connect(gain)
    gain.connect(this.masterFilter)
    
    osc.start(now)
    osc2.start(now)
    osc.stop(endTime)
    osc2.stop(endTime)
  }
  
  // Play bass with optional slide
  private playBass(note: string, duration: number, volume: number, octaveShift: number = 0): void {
    const freq = NOTE_FREQ[note]
    if (!freq) return
    
    const shiftedFreq = freq * Math.pow(2, octaveShift)
    
    // Fat bass: fundamental + sub octave
    this.playVoice(
      shiftedFreq,
      duration,
      'sawtooth',
      volume,
      0.01,
      0.15,
      0.6,
      0.1,
      0,
      0,
      0,
      800 // Strong filter envelope
    )
    
    // Sub bass
    this.playVoice(
      shiftedFreq / 2,
      duration,
      'sine',
      volume * 0.8,
      0.01,
      0.05,
      0.9,
      0.05,
      0,
      0,
      0,
      0
    )
  }
  
  // Arpeggiator voice
  private playArp(note: string, duration: number, volume: number): void {
    const freq = NOTE_FREQ[note]
    if (!freq) return
    
    this.playVoice(
      freq,
      duration,
      'triangle',
      volume,
      0.005,
      0.05,
      0.5,
      0.08,
      0,
      0,
      0,
      600
    )
  }
  
  // Drum sounds
  private playKick(): void {
    if (!this.audioContext || !this.masterGain || !this.params.drumsEnabled) return
    
    const now = this.audioContext.currentTime
    
    // Kick body (pitch-dropping sine)
    const kickOsc = this.audioContext.createOscillator()
    const kickGain = this.audioContext.createGain()
    
    kickOsc.type = 'sine'
    kickOsc.frequency.setValueAtTime(160, now)
    kickOsc.frequency.exponentialRampToValueAtTime(40, now + 0.12)
    
    kickGain.gain.setValueAtTime(0.7, now)
    kickGain.gain.exponentialRampToValueAtTime(0.01, now + 0.2)
    
    kickOsc.connect(kickGain)
    kickGain.connect(this.masterGain)
    kickOsc.start(now)
    kickOsc.stop(now + 0.2)
    
    // Kick click (short noise burst)
    const clickOsc = this.audioContext.createOscillator()
    const clickGain = this.audioContext.createGain()
    clickOsc.type = 'square'
    clickOsc.frequency.value = 1200
    clickGain.gain.setValueAtTime(0.15, now)
    clickGain.gain.exponentialRampToValueAtTime(0.001, now + 0.02)
    clickOsc.connect(clickGain)
    clickGain.connect(this.masterGain)
    clickOsc.start(now)
    clickOsc.stop(now + 0.02)
  }
  
  private playSnare(): void {
    if (!this.audioContext || !this.masterGain || !this.params.drumsEnabled) return
    
    const now = this.audioContext.currentTime
    
    // Snare body
    const bodyOsc = this.audioContext.createOscillator()
    const bodyGain = this.audioContext.createGain()
    bodyOsc.type = 'triangle'
    bodyOsc.frequency.setValueAtTime(220, now)
    bodyOsc.frequency.exponentialRampToValueAtTime(120, now + 0.05)
    bodyGain.gain.setValueAtTime(0.4, now)
    bodyGain.gain.exponentialRampToValueAtTime(0.01, now + 0.15)
    bodyOsc.connect(bodyGain)
    bodyGain.connect(this.masterGain)
    bodyOsc.start(now)
    bodyOsc.stop(now + 0.15)
    
    // Snare noise
    const bufferSize = this.audioContext.sampleRate * 0.15
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
    noiseFilter.frequency.value = 2000
    noiseGain.gain.setValueAtTime(0.3, now)
    noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.12)
    
    noise.connect(noiseFilter)
    noiseFilter.connect(noiseGain)
    noiseGain.connect(this.masterGain)
    noise.start(now)
    noise.stop(now + 0.15)
  }
  
  private playHihat(open: boolean = false): void {
    if (!this.audioContext || !this.masterGain || !this.params.drumsEnabled) return
    
    const now = this.audioContext.currentTime
    const duration = open ? 0.15 : 0.05
    
    const bufferSize = this.audioContext.sampleRate * duration
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
    noiseFilter.frequency.value = open ? 6000 : 9000
    
    const vol = open ? 0.12 : 0.08
    noiseGain.gain.setValueAtTime(vol, now)
    noiseGain.gain.exponentialRampToValueAtTime(0.001, now + duration)
    
    noise.connect(noiseFilter)
    noiseFilter.connect(noiseGain)
    noiseGain.connect(this.masterGain)
    noise.start(now)
    noise.stop(now + duration)
  }
  
  // Main sequencer step
  private sequence = (): void => {
    if (!this.isPlaying || !this.audioContext) return
    
    const section = this.songSections[this.sectionIndex % this.songSections.length]
    const stepsPerBar = 16
    const stepInBar = this.stepIndex % stepsPerBar
    const intensity = section.intensity * (0.7 + this.params.melodyComplexity * 0.1)
    
    // Calculate timing
    const secondsPerBeat = 60 / this.params.tempo
    const secondsPerStep = secondsPerBeat / 4 // 16th notes
    
    // Get current chord
    const barInSection = this.barIndex % section.bars
    const chordIndex = section.chordProgression[barInSection % section.chordProgression.length]
    const chord = this.chords[chordIndex]
    const rootNote = chord.root + '3'
    
    // === PAD (sustained chords) ===
    if (section.hasPad && stepInBar === 0) {
      const padNotes = chord.notes.map(n => {
        // Shift to higher octave
        const note = n.replace(/\d/, (d) => String(parseInt(d) + 1))
        return note
      })
      this.playPad(padNotes, secondsPerStep * 14, 0.25 * intensity)
    }
    
    // === LEAD MELODY ===
    if (section.hasLead && stepInBar % 2 === 0) {
      const pattern = this.leadPatterns[Math.min(section.melodyPattern, this.leadPatterns.length - 1)]
      const noteOffset = pattern[this.leadNoteIndex % pattern.length]
      
      if (noteOffset >= 0) {
        const leadFreq = this.getFrequency(rootNote, noteOffset + 12) // One octave up
        const duration = secondsPerStep * (noteOffset === pattern[(this.leadNoteIndex + 1) % pattern.length] ? 3 : 1.5)
        
        // Find previous note for slide
        const prevOffset = pattern[(this.leadNoteIndex - 1 + pattern.length) % pattern.length]
        const prevNote = prevOffset >= 0 ? Object.keys(NOTE_FREQ).find(k => 
          Math.abs(NOTE_FREQ[k] - this.getFrequency(rootNote, prevOffset + 12)) < 1
        ) : undefined
        
        const leadNote = Object.keys(NOTE_FREQ).find(k => Math.abs(NOTE_FREQ[k] - leadFreq) < 1) || 'A4'
        this.playLead(leadNote, duration, 0.28 * intensity, prevNote)
      }
      this.leadNoteIndex++
    }
    
    // === ARPEGGIO ===
    const arpSpeedSteps = Math.max(1, Math.floor(4 / this.params.arpSpeed))
    if (stepInBar % arpSpeedSteps === 0) {
      const arpPatternIndex = Math.min(Math.floor(section.intensity * 3), this.arpPatterns.length - 1)
      const arpPattern = this.arpPatterns[arpPatternIndex]
      const arpNote = arpPattern[this.arpNoteIndex % arpPattern.length]
      
      const chordTone = chord.notes[arpNote.tone % chord.notes.length]
      const arpOctave = parseInt(chordTone.slice(-1)) + arpNote.octave + 1
      const arpNoteName = chordTone.slice(0, -1) + arpOctave
      
      if (NOTE_FREQ[arpNoteName]) {
        this.playArp(arpNoteName, secondsPerStep * 0.8, 0.15 * intensity)
      }
      this.arpNoteIndex++
    }
    
    // === BASS ===
    if (this.params.bassEnabled) {
      const bassPatternIndex = Math.min(Math.floor(section.intensity * 3), this.bassPatterns.length - 1)
      const bassPattern = this.bassPatterns[bassPatternIndex]
      const bassHit = bassPattern.find(b => b.step === stepInBar)
      
      if (bassHit) {
        const bassNote = chord.root + '2'
        this.playBass(bassNote, secondsPerStep * bassHit.duration * 0.9, 0.35 * intensity, bassHit.octave)
      }
    }
    
    // === DRUMS ===
    if (this.params.drumsEnabled) {
      const drumPattern = this.drumPatterns[Math.min(section.drumPattern, this.drumPatterns.length - 1)]
      
      if (drumPattern.kick.includes(stepInBar)) {
        this.playKick()
      }
      if (drumPattern.snare.includes(stepInBar)) {
        this.playSnare()
      }
      if (drumPattern.openhat.includes(stepInBar)) {
        this.playHihat(true)
      } else if (drumPattern.hihat.includes(stepInBar)) {
        this.playHihat(false)
      }
    }
    
    // Advance step
    this.stepIndex++
    
    // Check for bar change
    if (this.stepIndex % stepsPerBar === 0) {
      this.barIndex++
      this.currentChordIndex++
      
      // Check for section change
      if (this.barIndex >= section.bars) {
        this.barIndex = 0
        this.sectionIndex++
        
        // Reset pattern indices on section change
        this.leadNoteIndex = 0
        this.arpNoteIndex = 0
        this.bassPatternIndex = 0
      }
    }
  }
  
  private restartSequencer(): void {
    if (this.sequenceInterval) {
      clearInterval(this.sequenceInterval)
    }
    const msPerStep = (60 / this.params.tempo / 4) * 1000
    this.sequenceInterval = window.setInterval(this.sequence, msPerStep)
    
    // Update delay time to match tempo
    if (this.delayNode) {
      this.delayNode.delayTime.value = 60 / this.params.tempo / 2
    }
  }

  play(): void {
    if (this.isPlaying) return
    if (!this.initAudio()) return

    this.isPlaying = true
    this.stepIndex = 0
    this.barIndex = 0
    this.sectionIndex = 0
    this.currentChordIndex = 0
    this.leadNoteIndex = 0
    this.arpNoteIndex = 0
    this.bassPatternIndex = 0

    this.restartSequencer()
  }

  stop(): void {
    this.isPlaying = false

    if (this.sequenceInterval) {
      clearInterval(this.sequenceInterval)
      this.sequenceInterval = null
    }

    // Fade out master
    if (this.masterGain && this.audioContext) {
      this.masterGain.gain.linearRampToValueAtTime(0, this.audioContext.currentTime + 0.2)
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
