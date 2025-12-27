import { useCallback } from 'react'
import { KeygenAudioParams, defaultAudioParams } from '../lib/keygenAudio'
import { KeygenVisualParams, defaultVisualParams } from './KeygenVisualizer'

interface KeygenParamsPanelProps {
  audioParams: KeygenAudioParams
  visualParams: KeygenVisualParams
  onParamsChange: (
    audio: Partial<KeygenAudioParams>,
    visual: Partial<KeygenVisualParams>
  ) => void
  onClose: () => void
}

interface SliderProps {
  label: string
  value: number
  min: number
  max: number
  step?: number
  onChange: (value: number) => void
}

function Slider({ label, value, min, max, step = 0.1, onChange }: SliderProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs">
        <span className="text-white/70">{label}</span>
        <span className="text-white/90 font-mono">{value.toFixed(1)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="keygen-slider"
      />
    </div>
  )
}

interface ToggleProps {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
}

function Toggle({ label, checked, onChange }: ToggleProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <div
        className={`w-8 h-4 rounded-full transition-colors ${
          checked ? 'bg-white/70' : 'bg-white/20'
        }`}
        onClick={() => onChange(!checked)}
      >
        <div
          className={`w-4 h-4 rounded-full bg-white transition-transform ${
            checked ? 'translate-x-4' : 'translate-x-0'
          }`}
        />
      </div>
      <span className="text-xs text-white/70">{label}</span>
    </label>
  )
}

type WaveformType = 'square' | 'sawtooth' | 'triangle' | 'sine'

const PRESETS = {
  classic: {
    audio: {
      tempo: 140,
      arpSpeed: 2,
      waveform: 'square' as WaveformType,
      filterCutoff: 2000,
      filterResonance: 8,
      volume: 0.3,
      melodyComplexity: 3,
    },
    visual: {
      scrollSpeed: 1,
      waveAmplitude: 15,
      colorCycleSpeed: 1,
      glitchIntensity: 0.3,
    },
  },
  aggressive: {
    audio: {
      tempo: 180,
      arpSpeed: 4,
      waveform: 'sawtooth' as WaveformType,
      filterCutoff: 4000,
      filterResonance: 12,
      volume: 0.4,
      melodyComplexity: 5,
    },
    visual: {
      scrollSpeed: 2,
      waveAmplitude: 25,
      colorCycleSpeed: 2,
      glitchIntensity: 0.6,
    },
  },
  chill: {
    audio: {
      tempo: 100,
      arpSpeed: 1,
      waveform: 'triangle' as WaveformType,
      filterCutoff: 1200,
      filterResonance: 4,
      volume: 0.25,
      melodyComplexity: 2,
    },
    visual: {
      scrollSpeed: 0.5,
      waveAmplitude: 8,
      colorCycleSpeed: 0.5,
      glitchIntensity: 0.1,
    },
  },
  random: {
    audio: {
      tempo: Math.floor(Math.random() * 100) + 80,
      arpSpeed: Math.random() * 3 + 0.5,
      waveform: (['square', 'sawtooth', 'triangle', 'sine'] as const)[
        Math.floor(Math.random() * 4)
      ],
      filterCutoff: Math.floor(Math.random() * 6000) + 500,
      filterResonance: Math.random() * 15 + 1,
      volume: 0.3,
      melodyComplexity: Math.floor(Math.random() * 5) + 1,
    },
    visual: {
      scrollSpeed: Math.random() * 2 + 0.5,
      waveAmplitude: Math.random() * 25 + 5,
      colorCycleSpeed: Math.random() * 2 + 0.5,
      glitchIntensity: Math.random() * 0.8,
    },
  },
}

export default function KeygenParamsPanel({
  audioParams,
  visualParams,
  onParamsChange,
  onClose,
}: KeygenParamsPanelProps) {
  const applyPreset = useCallback(
    (presetName: keyof typeof PRESETS) => {
      const preset =
        presetName === 'random'
          ? {
              audio: {
                tempo: Math.floor(Math.random() * 100) + 80,
                arpSpeed: Math.random() * 3 + 0.5,
                waveform: (['square', 'sawtooth', 'triangle', 'sine'] as const)[
                  Math.floor(Math.random() * 4)
                ],
                filterCutoff: Math.floor(Math.random() * 6000) + 500,
                filterResonance: Math.random() * 15 + 1,
                volume: 0.3,
                melodyComplexity: Math.floor(Math.random() * 5) + 1,
              },
              visual: {
                scrollSpeed: Math.random() * 2 + 0.5,
                waveAmplitude: Math.random() * 25 + 5,
                colorCycleSpeed: Math.random() * 2 + 0.5,
                glitchIntensity: Math.random() * 0.8,
              },
            }
          : PRESETS[presetName]
      onParamsChange(preset.audio, preset.visual)
    },
    [onParamsChange]
  )

  const resetToDefaults = useCallback(() => {
    onParamsChange(defaultAudioParams, defaultVisualParams)
  }, [onParamsChange])

  return (
    <div
      className="keygen-params-panel absolute top-12 right-3 w-72 max-h-[80%] overflow-y-auto rounded-lg bg-black/90 border border-white/20 p-4 z-20"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-white/90 font-mono uppercase tracking-wider">
          Parameters
        </h3>
        <button
          onClick={onClose}
          className="text-white/50 hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Presets */}
      <div className="mb-4">
        <div className="text-xs text-white/50 mb-2 uppercase tracking-wider">
          Presets
        </div>
        <div className="grid grid-cols-4 gap-1">
          {(Object.keys(PRESETS) as (keyof typeof PRESETS)[]).map((preset) => (
            <button
              key={preset}
              onClick={() => applyPreset(preset)}
              className="px-2 py-1 text-xs font-mono rounded bg-white/10 text-white/70 hover:bg-white/20 hover:text-white transition-colors capitalize"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>

      {/* Audio Section */}
      <div className="mb-4">
        <div className="text-xs text-magenta-400 mb-3 uppercase tracking-wider flex items-center gap-2">
          <span className="text-pink-400">♫</span> Audio
        </div>
        <div className="space-y-3">
          <Slider
            label="Tempo (BPM)"
            value={audioParams.tempo}
            min={60}
            max={200}
            step={1}
            onChange={(v) => onParamsChange({ tempo: v }, {})}
          />
          <Slider
            label="Arp Speed"
            value={audioParams.arpSpeed}
            min={0.5}
            max={4}
            onChange={(v) => onParamsChange({ arpSpeed: v }, {})}
          />
          <Slider
            label="Filter Cutoff"
            value={audioParams.filterCutoff}
            min={200}
            max={8000}
            step={100}
            onChange={(v) => onParamsChange({ filterCutoff: v }, {})}
          />
          <Slider
            label="Resonance"
            value={audioParams.filterResonance}
            min={0.5}
            max={20}
            onChange={(v) => onParamsChange({ filterResonance: v }, {})}
          />
          <Slider
            label="Volume"
            value={audioParams.volume}
            min={0}
            max={1}
            onChange={(v) => onParamsChange({ volume: v }, {})}
          />
          <Slider
            label="Complexity"
            value={audioParams.melodyComplexity}
            min={1}
            max={5}
            step={1}
            onChange={(v) => onParamsChange({ melodyComplexity: v }, {})}
          />

          {/* Waveform selector */}
          <div className="flex flex-col gap-1">
            <span className="text-xs text-white/70">Waveform</span>
            <div className="grid grid-cols-4 gap-1">
              {(['square', 'sawtooth', 'triangle', 'sine'] as const).map((wave) => (
                <button
                  key={wave}
                  onClick={() => onParamsChange({ waveform: wave }, {})}
                  className={`px-2 py-1 text-xs font-mono rounded transition-colors ${
                    audioParams.waveform === wave
                      ? 'bg-white/80 text-black'
                      : 'bg-white/10 text-white/70 hover:bg-white/20'
                  }`}
                >
                  {wave.slice(0, 3)}
                </button>
              ))}
            </div>
          </div>

          {/* Audio toggles */}
          <div className="flex gap-4 pt-1">
            <Toggle
              label="Bass"
              checked={audioParams.bassEnabled}
              onChange={(v) => onParamsChange({ bassEnabled: v }, {})}
            />
            <Toggle
              label="Drums"
              checked={audioParams.drumsEnabled}
              onChange={(v) => onParamsChange({ drumsEnabled: v }, {})}
            />
          </div>
        </div>
      </div>

      {/* Visual Section */}
      <div className="mb-4">
        <div className="text-xs mb-3 uppercase tracking-wider flex items-center gap-2">
          <span className="text-white/70">◈</span>
          <span className="text-white/70">Visual</span>
        </div>
        <div className="space-y-3">
          <Slider
            label="Flow Speed"
            value={visualParams.scrollSpeed}
            min={0.5}
            max={3}
            onChange={(v) => onParamsChange({}, { scrollSpeed: v })}
          />
          <Slider
            label="Wave Amplitude"
            value={visualParams.waveAmplitude}
            min={0}
            max={30}
            step={1}
            onChange={(v) => onParamsChange({}, { waveAmplitude: v })}
          />
          <Slider
            label="Wave Frequency"
            value={visualParams.waveFrequency}
            min={1}
            max={5}
            onChange={(v) => onParamsChange({}, { waveFrequency: v })}
          />
          <Slider
            label="Density Cycle"
            value={visualParams.colorCycleSpeed}
            min={0.5}
            max={3}
            onChange={(v) => onParamsChange({}, { colorCycleSpeed: v })}
          />
          <Slider
            label="Glitch"
            value={visualParams.glitchIntensity}
            min={0}
            max={1}
            onChange={(v) => onParamsChange({}, { glitchIntensity: v })}
          />

          {/* Visual toggles */}
          <div className="flex gap-4 pt-1">
            <Toggle
              label="Stars"
              checked={visualParams.starfieldEnabled}
              onChange={(v) => onParamsChange({}, { starfieldEnabled: v })}
            />
          </div>
        </div>
      </div>

      {/* Reset button */}
      <button
        onClick={resetToDefaults}
        className="w-full py-2 text-xs font-mono rounded bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/70 transition-colors uppercase tracking-wider"
      >
        Reset to Defaults
      </button>
    </div>
  )
}

