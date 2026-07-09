# Solo Space Station Simulator

A text-based exploration game set on a space station, built with Python and Tkinter (in-game title: Space Station Explorer).

## Core Features

- **Character System**: Create a character with unique jobs (Staff Assistant to Captain), each with special access and starting credits
- **Station Navigation**: Explore a donut-shaped ring of hallways and department rooms with random events
- **Inventory System**: Carry items, store them in your quarters locker, and examine, read, drop, or drink them
- **Health System**: Track limb damage plus burns, poison, and oxygen; seek treatment in MedBay
- **Crew Roster**: Start alongside procedurally staffed NPC crew (department heads and assistants)
- **Save System**: Save and load game progress at any time

## Station Systems

### Power Management
- Monitor and manage station battery levels
- Control system power allocation (life support, lighting, security, communications)
- Solar panel charging system
- Power modes including emergency settings
- Engineering panel access for Engineers and the Captain

### Medical System
- Health tracking for limbs, burns, poison, and oxygen
- Paid medical treatment and health assessments in MedBay
- Free self-treatment and crew vitals monitoring for Doctors
- Oxygen damage when life support is underpowered, with emergency revive if it reaches critical levels

### Security System
- Access control for restricted areas
- Door locking and unlocking for authorized personnel
- Crew manifest for Security staff

### Stock Market
- Real-time market simulation with automatic updates
- Buy and sell shares in various companies from your quarters computer
- Price history tracking and visualization
- Portfolio management and profit tracking
- Filtering options and detailed transaction history

### Bar System
- Order drinks from the menu
- Bartender drink mixing and recipe list
- Alcohol tracking on your character sheet
- Social interactions

### Botany System
- Seed collection from the botanist station
- Plant seeds across multiple planters
- Planter status monitoring
- Special access for Botanists

### Life Support
- Oxygen levels tied to power allocation
- Emergency protocols from Engineering
- Effects on player and crew safety when systems are underpowered

### Bridge and Personnel
- Talk to ship leadership when present
- Crew manifest and NPC job assignment for the Head of Personnel
- Public Access Control terminal for job-change requests
- Captain and HoP door control for the Bridge

### Engineering
- Fabricator for creating tools, books, and components
- Full power management panel for authorized staff

## Getting Started

1. Install Python 3.6+ (with tkinter available; on Linux install `python3-tk`) and required packages:
```
cd Code
pip install -r requirements.txt
```

2. Run the game:
```
python run_game.py
```

For standalone Windows and Linux builds, see `Code/BUILD_INSTRUCTIONS.md`.

## Station Layout

The station uses a hollow-square hallway ring with special rooms branching off it:
- Quarters attached at the hallway junction
- Connected hallways forming a complete circuit
- Special rooms:
  - Bridge
  - MedBay
  - Security
  - Engineering Bay
  - Bar
  - Botany Lab

## Job Access Levels

- **Staff Assistant**: Basic access
- **Engineer**: Engineering Bay + power management
- **Security Guard**: Security systems + door control
- **Doctor**: MedBay + advanced treatment
- **Bartender**: Bar + drink mixing
- **Botanist**: Botany Lab + plant cultivation
- **Head of Personnel**: Multiple department access + personnel tools
- **Captain**: Full station access

## Tips

- Monitor your health and seek treatment in MedBay when needed
- Keep track of power levels and oxygen status from Engineering
- Use the stock market on your quarters computer to earn additional credits
- Explore all rooms to discover features, items, and job-specific stations
- Save regularly using your bed or the Save and Exit button
