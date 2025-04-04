# Bill of Materials: T-Junction Microfluidic Causal Chamber

This document outlines the components needed to build the T-junction microfluidic Causal Chamber. Costs are estimates and subject to change.

---

**1. Microfluidic Chip Fabrication**

| Item                      | Quantity | Low Cost Option                                    | Medium Cost Option                                | High Cost Option                                                       | Notes                                                                      |
| :------------------------ | :------- | :------------------------------------------------- | :------------------------------------------------ | :--------------------------------------------------------------------- | :------------------------------------------------------------------------- |
| Acrylic Sheet (PMMA)      | 1-2      | ~$10-20 (e.g., 12"x12" sheet, 1-3mm thick)          | ~$10-20 (Same)                                    | ~$10-20 (Same)                                                         | Material cost is low. Needs to be suitable for milling/laser.              |
| Micromilling Machine      | 1        | ~$300-800 (Hobby CNC like 3018 + upgrades)          | **~$1500-5000 (Desktop CNC like Nomad, Bantam Tools)** | ~$10k+ (Professional Micromill). At this point, find a foundary to make the chip for you | The quality jump from a hobby CNC like a 3018 to a Desktop CNC is huge. It's worth it. |
| End Mills                 | Set      | ~$20-50 (Small diameter set for hobby CNC)         | ~$50-150 (Carbide end mills, e.g., 1/64", 1/32")    | $150+ (High-precision micro end mills)                                 | Needed for milling channels. Size determines feature resolution. Don't break the bank here. |
| Interface layer           | 1 Pack   | ~$15-20 (3M 468MP Adhesive Sheet)                | ~$30-50 Pre-made PDMS sheet (aliexpress)          | ~$50-100 Pre-made PDMS sheet (not aliexpress)                           | For bonding chip layers.                                                   |
| 3D Printer                | 1        | ~$150-300 (FDM Bambu Mini)                       | **~$200-500 (Resin like Elegoo Mars, Anycubic Photon)** | $1k+ (Higher-end Resin or FDM)                                         | For printing Luer ports. Resin preferred for detail/sealing. Good FDM printers can work just fine as well. |
| 3D Printer Material       | 1 Spool/Bottle | ~$20-30 (PLA/PETG Filament)                      | ~$30-50 (Standard Resin)                          | $50+ (Engineering grade resin)                                         | For Luer ports.                                                            |

---

**2. Fluid Handling / Actuation (Pressure-Driven Recommended)**

| Item                         | Quantity | Low Cost Option                                       | Medium Cost Option                                          | High Cost Option                                               | Notes                                                                                 |
| :--------------------------- | :------- | :---------------------------------------------------- | :---------------------------------------------------------- | :------------------------------------------------------------- | :------------------------------------------------------------------------------------ |
| Pressure Source              | 1        | ~$50-150 (Small diaphragm pump + small air tank)      | **~$150-400 (Quiet lab compressor or Nitrogen tank + regulator)** | $500+ (High-purity gas line install or high-end compressor)    | Needs stable, clean pressure output. Manual pumps not suitable for AI training       |
| Electronic Pressure Ctrl.    | 2        | ~$100-300 each (DIY Arduino + proportional valves) | **~$500-1500 each (OEM or basic commercial units)**           | $2k+ each (Research-grade e.g., Fluigent, Elveflow)          | **Key component for automated control**. Cost varies hugely. DIY needs significant effort. |
| Liquid Reservoirs            | 2        | ~$10-20 (DIY sealed jars/bottles with fittings)       | ~$30-100 (Lab media bottles w/ pressure caps)                | $100+ (Commercial microfluidic pressure reservoirs)            | Must be airtight to hold pressure.                                                    |
| Tubing                       | ~5-10m   | ~$10-20 (PVC Aquarium Tubing)                         | **~$30-60 (Tygon, Silicone Tubing)**                            | $50-100+ (PEEK or Teflon Tubing)                                | Connects reservoirs to chip. Low compliance (PEEK/Teflon) is better for pressure control. |
| Fittings/Connectors          | Set      | ~$10-30 (Plastic Luer, barbs, T-connectors)           | **~$30-70 (Higher quality Luer locks, possibly metal)**         | $70+ (Microfluidic specific fittings, e.g., Upchurch)          | Connects tubing to ports, reservoirs, sensors.                                        |

---

**3. Sensing / Observation**

| Item                         | Quantity | Low Cost Option                                     | Medium Cost Option                                             | High Cost Option                                           | Notes                                                                                   |
| :--------------------------- | :------- | :-------------------------------------------------- | :------------------------------------------------------------- | :--------------------------------------------------------- | :-------------------------------------------------------------------------------------- |
| Camera                       | 1        | ~$50-150 (USB Microscope or modified Webcam+Lens) | **~$200-600 (Mid-range Machine Vision USB Camera, >100fps)**       | $1k+++ (High-speed camera)                                 | Needs sufficient resolution & frame rate (>100fps recommended) for droplets.              |
| Lens / Optics                | 1        | ~$20-50 (Included lens or basic macro adapter)    | **~$50-200 (Decent C-Mount lens or low-power microscope objective)** | $200+ (Higher quality objectives/telecentric lenses)       | To achieve required magnification.                                                      |
| Illumination                 | 1        | ~$10-30 (LED strip/panel)                           | **~$30-100 (Microscope ring light or adjustable LED source)**     | $100+ (Fiber optic illuminator or controlled backlight)    | Needs to be stable and bright. Backlighting often best.                               |
| Pressure Sensors (Inlet)     | 2        | ~$10-50 each (Basic digital sensor modules)     | **~$100-300 each (Industrial digital pressure transducers)**      | $300+ each (High-accuracy lab-grade transducers)         | **Highly recommended** for measuring actual input pressure. Needs appropriate range.      |
| Mounting / Stage             | 1        | ~$20-50 (Lab stand + clamps or basic 3D print)    | ~$50-150 (Simple XY manual stage or robust 3D print)          | $150+ (Stable microscope stage or vibration-damped mount) | Holds chip securely under camera, allows focusing.                                      |

---

**4. Control & Data Acquisition**

| Item                          | Quantity | Low Cost Option                            | Medium Cost Option                         | High Cost Option                                   | Notes                                                                                 |
| :---------------------------- | :------- | :----------------------------------------- | :----------------------------------------- | :------------------------------------------------- | :------------------------------------------------------------------------------------ |
| Computer                      | 1        | ~$50-150 (Raspberry Pi 4/5)                | **Existing Laptop/Desktop PC**                 | High-performance Workstation                       | Runs AI, main control software, data logging. RPi might limit video processing/AI. |
| Microcontroller (Optional)    | 1        | ~$5-20 (Arduino Nano, Pico, ESP32)       | ~$20-50 (Teensy, more capable ARM boards)  | $50+ (FPGA dev board)                              | For handling fast real-time sensor/actuator interfacing if PC latency is an issue.    |
| Interfacing Hardware          | Set      | ~$20-40 (Breadboard, jumper wires, PSU)    | ~$40-80 (Proto boards, cleaner wiring)     | $100+ (Custom PCB or DAQ card)                     | Connecting sensors/controllers to computer/microcontroller.                           |
| Software                      | -        | Free (Python, OpenCV, Arduino IDE, etc.) | Free (Same)                                | Free (Same)                                        | CAD/CAM software may have costs unless using free versions (e.g., Fusion 360 Personal). |

---

**5. Consumables & Miscellaneous**

| Item                   | Quantity    | Low Cost Option                   | Medium Cost Option                | High Cost Option                   | Notes                                                |
| :--------------------- | :---------- | :-------------------------------- | :-------------------------------- | :--------------------------------- | :--------------------------------------------------- |
| Water (Dispersed)      | As needed   | ~$1 (Tap/Distilled Water + Dye) | ~$5 (DI Water + Dye)              | ~$5 (Same)                         | Use food coloring for visualization.                 |
| Oil (Continuous)       | ~100-500mL  | ~$10-20 (Mineral Oil)             | **~$20-40 (Silicone Oil, low cSt)**   | $40+ (Fluorinated oils)            | Choose based on compatibility and properties.      |
| Surfactant             | ~5-10mL     | **~$10-20 (Span 80)**                 | ~$20-40 (Higher purity Span 80)   | $50+ (Specialty microfluidic surfactant) | Crucial for stable droplets.                         |
| Waste Container        | 1           | ~$1 (Beaker, bottle)              | ~$5 (Lab wash bottle)             | ~$5 (Same)                         | To collect outlet fluid.                             |
| Cleaning Supplies      | As needed   | ~$10 (Isopropyl alcohol, wipes) | ~$20 (Ethanol, lab-grade wipes)   | $20+ (Same)                        | For cleaning chip and components.                  |
| Safety Glasses         | 1           | **~$5-10**                             | ~$10-20                           | $20+                               | **Essential**.                                       |
| Gloves                 | Box         | **~$10-15 (Nitrile gloves)**          | ~$15-25 (Better quality nitrile)  | $25+                               | Good practice when handling chemicals/oils.        |
| Misc. Hardware         | Set         | ~$10 (Tape, fasteners)            | ~$20 (Assorted screws, clamps)   | $20+                               | For assembly and mounting.                           |

---

**Summary of Estimated Total Costs (Very Rough):**

*   Low Cost: ~$700 - $1500 (Heavily reliant on DIY for controllers, basic CNC, webcam/microscope, existing PC). *Requires significant user effort and troubleshooting.*
*   **Medium Cost: ~$3000 - $8000** (Using desktop CNC, basic commercial pressure controllers, machine vision camera, existing PC). *Balances cost and usability.* **(Recommended)**
*   High Cost: $10,000 - $25,000+ (Using professional controllers, high-speed camera, potentially better CNC/printer, dedicated workstation). *Highest performance and reliability, turnkey approach.*

**Key Cost Drivers:**
*   Electronic Pressure Controllers
*   Camera (especially high-speed)
*   Micromilling Machine