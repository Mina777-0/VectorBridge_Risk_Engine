High-Performance Risk Management Simulator

A real-time, low-latency risk engine built to handle high-frequency market data and trade execution using a custom binary protocol and vectorized calculations.

🚀 Key Features
* Binary Transport Layer: Uses Python struct and SSL/TLS sockets for memory-efficient, high-speed data ingestion.
* Zero-Copy Strategy: Implemented a custom Circular Buffer to handle packet framing and avoid memory fragmentation.
* Vectorized Risk Engine: Built on NumPy Structured Arrays, allowing for $O(1)$ lookups and $O(N)$ vectorized PnL/Exposure calculations, ensuring the system remains lag-free at 10x scale.
* Unified Async Architecture: Concurrent execution of the Secure Socket Server (Inbound) and an aiohttp WebSocket Server (Outbound) on a single event loop.
* Automated Accounting: Handles Realized/Unrealized PnL, Weighted Average Entry Price, and Net Exposure with "Counterparty Logic" (Client Buy = House Short).

🛠 Tech Stack
* Language: Python 3.11+
* Math: NumPy (Vectorized Risk Processing)
* Networking: asyncio (Asynchronous I/O), aiohttp (WebSockets)
* Templating: Jinja2 (Dynamic Dashboard)
* Protocol: Custom Binary TCP (!IddQ format)


📋 Installation & Setup
1. Clone the Repository:

git clone <repository-url>
cd <repository-folder>

2. Install Dependencies:
pip install -r requirements.txt

3. Run the System: To simplify local testing, the system is designed to run in three parts:
    * Server: python main.py (Starts both the Socket Server and the Dashboard)
    * Market Streamer: python client_sim.py (Feeds live price updates)

4. View the Dashboard: Open your browser and navigate to: http://127.0.0.1:8080/index/


🧠 Design Philosophy
The system was designed with Scalability as a core pillar. By moving away from standard JSON/REST for data ingestion and utilizing NumPy for state management, the backend can easily handle a 10x increase in message throughput without increasing the CPU overhead.
The dashboard utilizes a Throttling Strategy via WebSockets, ensuring the UI stays responsive by pushing updates at a fixed interval (1Hz), regardless of the raw message rate at the socket level.


🤝 Acknowledgments
* Gemini AI: Special thanks to the Gemini AI model for collaboration in debugging complex asynchronous race conditions and refining the financial logic/accounting calculations behind the Risk Engine, also in debugging the JavaScript conditions, and in writing this README.md 
