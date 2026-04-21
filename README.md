High-Performance Risk Management Infrastructure 

An industrial-grade, multi-language risk engine designed for high-frequency trading environments. This system utilizes a decoupled architecture to ingest binary market data, manage risk state in Rust, and provide real-time updates via a throttled WebSocket dashboard.


🏗 System Architecture
The project implements a Producer-Consumer pattern to ensure maximum stability and zero data loss during market volatility.
* Ingestion Layer (Python): A secure TCP server receives custom binary packets and instantly pushes them into an asyncio.Queue.
* The Hot Path (Rust): Background workers pull packets from the queue and interface with a Rust-based Risk Engine. This ensures thread-safe, nanosecond-latency updates to the internal book state.
* The Reporting Layer (WebSockets): A throttled aiohttp server samples the Rust engine's state at 1Hz, delivering vectorized metrics to the dashboard without impacting the performance of the ingestion workers.



🚀 Key Features
* Binary Transport Layer: Uses Python struct and SSL/TLS sockets for memory-efficient, high-speed data ingestion.
* Binary Protocol: Custom packet framing (!BIdQq) using Python’s struct module for minimal network overhead.
* Zero-Copy Strategy: Implemented a custom Circular Buffer to handle packet framing and avoid memory fragmentation.
* Memory Safety: Risk state managed in Rust (via PyO3/Maturin), providing high-speed field validation and arithmetic.
* Backpressure Management: Utilizes asyncio.Queue to decouple data receipt from processing, preventing "lag spikes" during high-volume bursts.
* Vectorized Reporting: Leverages optimized data structures to calculate Total PnL and Exposure across the entire book in a single pass.
* Unified Async Architecture: Concurrent execution of the Secure Socket Server (Inbound) and an aiohttp WebSocket Server (Outbound) on a single event loop.
* Automated Accounting: Handles Realized/Unrealized PnL, Weighted Average Entry Price, and Net Exposure with "Counterparty Logic" (Client Buy = House Short).



🛠 Tech Stack
* Languages: Python 3.11+, Rust (Edition 2021)
* Interoperability: PyO3 / Maturin
* Math: NumPy (Vectorized Risk Processing)
* Data Transport: Secure TCP Sockets (TLS/SSL)
* Templating: Jinja2 (Dynamic Dashboard)



📋 Installation & Setup
1. Clone the Repository:

git clone <repository-url>
cd <repository-folder>

2. Install Dependencies:
uv sync

3. Run the System: To simplify local testing, the system is designed to run in three parts:
    * Server: python main.py (Starts Ingestion + Queue Manager + Dashboard along with both the Socket Server and the Dashboard)
    * Market Streamer: python client_sim.py (Feeds live price updates)

4. View the Dashboard: Open your browser and navigate to: http://127.0.0.1:8080/index/


🧠 Design Philosophy
This project was built to exceed the standard "Python-only" approach. By offloading the "Hot Path" to Rust and utilizing a queue-based decoupling strategy, the system remains stable at 10x scale. The architecture prioritizes Ingestion Integrity—ensuring that not a single market tick is missed while the UI remains fluid and responsive.


🤝 Acknowledgments
* Gemini AI: Special thanks to the Gemini AI model for collaboration on architectural debugging, asynchronous queue management, and the logic behind Python-to-Rust memory bridging, refining the financial logic/accounting calculations behind the Risk Engine, also in debugging the JavaScript conditions, and in writing this README.md 
