# Buried Pipe Leakage Detection with TDR

This is a graduation project developed under the Department of Electrical and Electronics Engineering at Eskişehir Osmangazi University and funded by **TÜBİTAK 2209-A**.

## 📌 Project Overview

The project aims to detect leaks in **underground water distribution networks** using **Time Domain Reflectometry (TDR)** technology. A modular sensor system was developed where multiple TDR units communicate over a single RS-485 line, which also carries power. This reduces the need for additional infrastructure and increases system scalability.

Two graphical user interfaces (GUIs) were created using Python for testing and visualization purposes.

## 🧠 Key Features

- 📡 Leak detection using high-frequency signal reflections (TDR)
- 🔌 Power and data communication on a single RS-485 cable
- 🧮 STM32-based microcontroller integration
- 💻 Baudrate stability testing
- 📊 Real-time TDR signal visualization
- 🧪 Tested in air, water, and soil environments

## 📁 Folder Structure
📦 buried-pipe-leakage-detection-tdr
├── README.md
├── /docs
│ └── thesis.pdf # Full thesis report
│ └── TUBITAK_2209A_Proposal.pdf # Project proposal (optional)
│ └── TUBITAK_Support_Proof.png # Screenshot or image showing TUBITAK funding
├── /py_interfaces
│ └── baudrate_test_gui.py # GUI for serial communication testing
│ └── tdr_interface_gui.py # GUI for TDR signal visualization
.
.

## 🖥️ Interfaces (Python GUI)

- **Baudrate Test Interface:** Allows reliable RS-485 communication testing at various baudrates.
- **TDR Interface:** Plots signal reflections and shows the position of leaks along the cable using ADC data.

Both interfaces are located in the `py_interfaces` folder and built using **PyQt5** and **PySerial**.

## 🧪 Experimental Setup

- A physical testbed of 10.5 meters with 14 sections (air, water, soil)
- TDR tests were conducted under different dielectric conditions
- Capable of detecting impedance changes at up to 100 meters distance

## 🏅 Funding

This project was supported by **TÜBİTAK 2209-A**: University Students Research Projects Support Program.

![TUBITAK Support](docs/TUBITAK_Support_Proof.png)

## 👨‍💻 Contributors

- Yunus Emre Selen  
- Batuhan Zülkadiroğlu  
- Mert Civan  
- Alper Osman Gençer  

**Supervisor:** Assist. Prof. Dr. Gökhan Dındış

---

