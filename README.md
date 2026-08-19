#  MAVLink Relay Drone Communication System

A MAVLink-based communication and routing system designed to enable communication between a **Ground Control Station (GCS)** and multiple **Mission Drones** through an intermediate **Relay Drone**.

The project was developed during my internship at **C-DAC, Noida**, with a focus on UAV communication, MAVLink routing, telemetry systems, and Raspberry Pi-based communication infrastructure.

---

##  Overview

In a multi-drone system, direct communication between the Ground Control Station and mission drones can become unreliable due to distance, obstacles, or limited communication range.

This project introduces a **Relay Drone** that acts as an intermediate communication node.

```text
                  ┌─────────────────────┐
                  │   Ground Station    │
                  │   QGroundControl    │
                  └──────────┬──────────┘
                             │
                       SiK Telemetry
                             │
                             ▼
                  ┌─────────────────────┐
                  │     Relay Drone     │
                  │                     │
                  │    Raspberry Pi     │
                  │   MAVLink Router    │
                  └──────────┬──────────┘
                             │
                       MAVLink Traffic
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌───────────┐  ┌───────────┐  ┌───────────┐
        │ Mission   │  │ Mission   │  │ Mission   │
        │ Drone 1   │  │ Drone 2   │  │ Drone 3   │
        │ SYSID: 2  │  │ SYSID: 3  │  │ SYSID: 4  │
        └───────────┘  └───────────┘  └───────────┘
