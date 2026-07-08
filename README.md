# Solo Space Station Simulator

A text-based exploration game set on a space station, built with Python and Tkinter.

## Core Features

- **Character System**: Create a character with unique jobs (Staff Assistant to Captain), each with special access and starting credits
- **Station Navigation**: Explore interconnected rooms and hallways with random events
- **Inventory System**: Collect, store, and manage items throughout the station
- **Health System**: Track limb health, manage injuries, and seek medical treatment
- **Save System**: Save and load game progress at any time

## Station Systems

### Power Management
- Monitor and manage station power levels
- Control system power allocation (life support, lighting, security, communications)
- Solar panel charging system
- Emergency power modes
- Battery level monitoring and management

### Medical System
- Comprehensive health tracking (limbs, burns, poison, oxygen)
- Professional medical treatment options
- Detailed health reports and recommendations
- Advanced treatment for medical staff
- Emergency trauma care

### Security System
- Access control for restricted areas
- Door locking/unlocking for authorized personnel
- Security monitoring and alerts
- Guard interaction and assistance

### Stock Market
- Real-time market simulation with automatic updates
- Buy/sell shares in various companies
- Price history tracking and visualization
- Portfolio management and profit tracking
- Filtering and sorting options
- Detailed transaction history

### Bar System
- Order drinks from menu
- Special bartender drink mixing abilities
- Ingredient discovery and experimentation
- Recipe system with effects
- Social interactions

### Botany System
- Seed collection and management
- Plant growth and cultivation
- Multiple planter management
- Growth monitoring
- Special access for botanists

### Life Support
- Oxygen level monitoring
- Emergency protocols
- System damage effects
- Crew safety management

## Getting Started

1. Install Python 3.x and required packages:
```
pip install -r requirements.txt
```

2. Run the game:
```
python run_game.py
```

## Station Layout

The station features a circular layout with:
- Central quarters at (0,0)
- Connected hallways forming a complete circuit
- Special rooms:
  - Engineering Bay (5,3)
  - Bar (0,3)
  - Botany Lab (3,0)
  - MedBay, Security, and Bridge at strategic locations

## Job Access Levels

- **Staff Assistant**: Basic access
- **Engineer**: Engineering Bay + power management
- **Security**: Security systems + door control
- **Doctor**: MedBay + advanced treatment
- **Bartender**: Bar + drink mixing
- **Botanist**: Botany Lab + plant cultivation
- **Head of Personnel**: Multiple department access
- **Captain**: Full station access

## Tips

- Monitor your health and seek treatment when needed
- Keep track of power levels and oxygen status
- Use the stock market to earn additional credits
- Explore all rooms to discover new features and items
- Save regularly using your bed or the save button 