import sys, os, asyncio 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))
from utils.protocols_schemas import RiskEngine
from utils.log_config import get_logger
from server_sim import ConnectionHandler
from ws_handlers import start_aiohttp

logger= get_logger()



async def main():
    conn_hand= ConnectionHandler()
    risk_engine= RiskEngine()
    conn_hand.add_risk_engine(risk_engine)

    try:
        await asyncio.gather(
            conn_hand.start_server(),
            start_aiohttp(risk_engine)
        )

    except Exception as e:
        logger.debug(f"Critical System Failure: {e}")
        print(f"Critical System Failure: {e}")

    except KeyboardInterrupt:
        await conn_hand.clear_connection()
    
    finally:
        await conn_hand.clear_connection()
        
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupted - closed the event loop")
        
