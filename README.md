# Multi-Server TCP/IP Monitor

A Python-based distributed network monitoring system using persistent TCP connections. This project simulates a centralized **Management Service** overseeing multiple **Monitoring Services**—each responsible for checking remote network services (HTTP, HTTPS, ICMP, DNS, NTP, TCP, UDP)—and reporting back real-time operational status.

---

## Repository Structure

```bash
- Management_Service.py       # Central service that distributes tasks and receives results
- Monitoring_Service.py       # Simulates a remote node monitoring network services
- UDP_echo_server.py          # Optional echo server to simulate a testable service
- requirements.txt            # Python dependencies
- README.md                   # Project documentation
- /docs
  - final_report.pdf          # Final report with screenshots and code explanations
  - screenshots/              # Directory for labeled screenshots
```

---

## How to Run

### Option 1: Terminal (Default Setup)

Use three terminals for default Berlin station configuration.

**Terminal 1: Monitoring Service (Berlin)**
```bash
python Monitoring_Service.py
```

**Terminal 2: Management Service**
```bash
python Management_Service.py
# Enter "Berlin" when prompted
```

**Terminal 3: UDP Echo Server**
```bash
python UDP_echo_server.py
```

---

### Option 2: Alternate Configuration (e.g., Hong Kong)

```bash
python Monitoring_Service.py "Hong Kong" "127.0.0.1" 10202
```

---

### Option 3: Visual Studio 2022 (Run Without Debug)

1. Right-click on each `.py` file.
2. Choose "Run Without Debug".
3. Type "Berlin" or "Hong Kong" when prompted by Management_Service.py.

---

## Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

---

## Project Design

### Architecture Overview

- **Management Service** (central controller)
  - Maintains persistent TCP connections to **multiple Monitoring Services**
  - Distributes tasks to each monitoring service based on user input
  - Uses **multithreading** to concurrently handle communications for each connected station
  - Accepts configurable task intervals for each service
  - Displays real-time status (validating, idle, online/offline, reconnecting)
  - Supports dynamic reconnection and keepalive

- **Monitoring Service** (edge nodes)
  - Identified by unique user-defined station name (e.g., "Berlin", "Hong Kong", etc.)
  - Receives and acknowledges tasks sent from the management controller
  - Executes assigned monitoring tasks (HTTP, DNS, TCP, etc.)
  - Sends results back at the user-specified interval (e.g., every 5 seconds)
  - Queues data during disconnection and resends once reconnected

- **UDP Echo Server**
  - A simple always-on UDP server used to test and validate UDP-based monitoring tasks.
  - Enables Monitoring Services to run connectivity tests as part of their task configuration.
---

### Concurrent Monitoring with Multi-Threading

The Management Service creates a **dedicated thread for each Monitoring Service** it connects to. This allows:

- Simultaneous task distribution and result collection
- Scalable design—add more stations without bottlenecks
- Independent failure recovery: if one station goes down, others continue unaffected

Each thread handles:
- Receiving confirmation and task results
- Periodic status printing
- Managing keepalive and reconnection logic

---

### User-Configurable Task Intervals

Each task configuration includes:
- The type of network check (e.g., TCP, ICMP, NTP)
- The destination address and port
- A **user-defined interval** for how often the check is repeated

This means:
- Station "Berlin" might ping every 3 seconds
- Station "Hong Kong" might do an HTTP check every 10 seconds
- Management Service tracks and adapts to these frequencies independently

---

### Example Config Dictionary (Pseudocode)

```python
task_config = {
    "Berlin": [
        {"type": "ICMP", "target": "8.8.8.8", "interval": 5},
        {"type": "TCP", "target": "example.com", "port": 80, "interval": 10}
    ],
    "Hong Kong": [
        {"type": "DNS", "target": "1.1.1.1", "interval": 8}
    ]
}
```

Each station's thread will:
1. Send its configuration to the monitoring service
2. Listen for acknowledgment
3. Collect results at defined intervals

---

## Screenshots

> Screenshots inside `docs/screenshots/` and embed below.

### Management Dashboard (Terminal)
![Management Service](docs/screenshots/management_dashboard.png)

### Monitoring Service Status
![Monitoring Service](docs/screenshots/monitoring_status.png)

---

## Final Report

> Final report inside `docs/final_report.pdf`

[View Final Report (PDF)](docs/Sockets_Project_2_SPP2_051524_v01.pdf)

The report includes:
- Run commands and setup
- Screenshots with labels
- Code snippets showing SRS fulfillment
- Commentary on design decisions and implementation

---

## Author

**Tony Chan**  
[GitHub Repo](https://github.com/Luckygoldjade/multi-server-tcpip-monitor.git)

---

## License

This project is licensed for educational and demonstration purposes.