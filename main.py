import sys, os, asyncio 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))
from utils.protocols_schemas import RiskEngine
from utils.log_config import get_logger
from server_sim import ConnectionHandler
from ws_handlers import start_aiohttp
from utils.queue_config import QueueManager
from utils.worker_config import WorkerManager

logger= get_logger()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'rust_config/risk_manager', 'target/debug')))
import risk_manager



async def main():
    conn_hand= ConnectionHandler()
    #risk_engine= RiskEngine()
    risk_engine= risk_manager.RiskEngine(5)
    qm= QueueManager()
    qm.initiate_queues()
    conn_hand.add_risk_engine(risk_engine)
    conn_hand.add_queue_manager(qm)
    wm= WorkerManager()
    wm.add_queue_manager(qm)
    wm.add_risk_engine(risk_engine)
    
    try:
        await asyncio.gather(
            wm.initiate_worker(),
            conn_hand.start_server(),
            start_aiohttp(risk_engine)
        )

    except Exception as e:
        logger.debug(f"Critical System Failure: {e}")
        print(f"Critical System Failure: {e}")

    except KeyboardInterrupt:
        await conn_hand.clear_connection()
        await wm.close_worker()
    
    finally:
        await conn_hand.clear_connection()
        await wm.close_worker()
        
        
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupted - closed the event loop")
        
