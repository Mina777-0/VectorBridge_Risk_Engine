import asyncio, socket, ssl, sys, os 
from typing import Optional, List
from dotenv import load_dotenv
import time 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))
from utils.protocols_schemas import CircularBuffer, RiskEngine
from utils.log_config import get_logger
from utils.queue_config import QueueManager


logger= get_logger()
#logger.info("Engine TEST")

key_file= os.path.abspath(os.path.join(os.path.dirname(__file__), "key.pem"))
cert_file= os.path.abspath(os.path.join(os.path.dirname(__file__), "cert.pem"))
env_file= os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(env_file)

password= os.environ.get('PASSWORD')
password_bytes= bytes(password, encoding="utf-8")




class ConnectionHandler:
    def __init__(self):
        self.ssock: Optional[socket.socket]= None
        self.cb: Optional[CircularBuffer]= CircularBuffer(2800) # Socket buffer is 64 KB
        self.ip_address= ("127.0.0.1", 2345)
        self.loop= asyncio.get_running_loop()
        self.tasks: List[asyncio.Task]= []
        self.risk_engine: Optional[RiskEngine]= None
        self.qm: QueueManager= None
        self.max_tasks= 3


    # Add risk engine instance 
    def add_risk_engine(self, risk_engine: RiskEngine):
        self.risk_engine= risk_engine

    def add_queue_manager(self, qm: QueueManager):
        self.qm= qm 
        

    async def start_server(self):
        global password_bytes

        context= ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        try:
            context.load_cert_chain(certfile=cert_file, keyfile=key_file, password=password_bytes)
        except FileNotFoundError:
            logger.error(f"[SERVER]: 'cert.pem' or 'key.pem' file is missing")
            raise
        except Exception as e:
            logger.error(f"[SERVER]: Unexpecred error occured: {e}")
            raise

        # Socket settings
        sock= socket.socket(family=socket.AF_INET, type= socket.SOCK_STREAM)
        sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.bind(self.ip_address)
        sock.listen(3)
        print(f"\n[SERVER]: Server is listing on {self.ip_address[0]}:{self.ip_address[1]}. Waiting for connections ..")
        logger.info("[SERVER]: Server is running!")


        try:
            while True:
                try:
                    conn, addr= sock.accept()
                    print(f"\n[SERVER]: Unencrypted connection accepted from {addr}")

                    self.ssock= context.wrap_socket(conn, server_side=True)
                    print(f"\n[SERVER]: SSL handashke is complete with {addr}. Protocol: {self.ssock.version()}")
                    logger.info(f"[SERVER]: Handhshake is complete with {addr}")

                    # Run the socket handler at the backgroud and add it to tasks to clean at the end to avoid zombie-tasks
                    try:
                        task= asyncio.create_task(self.handler())
                        self.tasks.append(task)
                        logger.info(f"[SERVER]: Task {task.get_name()} is created and added to list")
                    except asyncio.CancelledError as e:
                        logger.debug(f"Task {task.get_name()} is cancelled")
                        raise e

                # If connection is not accepted or takes time, create a waiter and add it to the file discriptor of the OS through asyncio event loop.
                # Don't close the socket
                except (InterruptedError, BlockingIOError):
                    waiter= self.loop.create_future()
                    fd= sock.fileno()
                    self.loop.add_reader(fd, lambda: waiter.set_result(None) or waiter.done())

                    try:
                        logger.info("[SERVER]: Waiter is created in waiting for connection to accept")
                        await waiter
                        
                    finally:
                        logger.info("[SERVER]: fd is removed. Connection is accepted")
                        self.loop.remove_reader(fd)
                    continue

        except ConnectionAbortedError as e:
            logger.error(f"[SERVER]; Connection is aborted: {e}")
            raise
        except BrokenPipeError as e:
            logger.error(f"[SERVER]: Pipe is broken: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occured: {e}")
            raise
        
    

    async def handler(self):
        
        if self.ssock is None:
            logger.debug("[HANDLER]: Socket is None")
            raise ConnectionError("Socket is None or closed")
        
        try:

            while True:
                try:
                    #t0= time.perf_counter_ns()
                    nbytes= self.ssock.recv_into(self.cb.write_to())
                    print(f"nbyes= {nbytes}")
                    if nbytes == 0:
                        logger.debug("[HANDLER]: bytes received = 0")
                        break

                    self.cb.did_write(nbytes)

                    while self.cb.count >= self.cb.packet_size:
                        
                        fields= self.cb.peek()
                        t2= time.perf_counter_ns()
                        print(fields)
                        try:
                            await self.qm.add_items(fields)
                        except Exception as e:
                            print(f"\n[SERVER]: QM: {e}")
                        '''
                        if fields[0] == 0:
                            self.risk_engine.update_market_price(fields[1], fields[2])
                            logger.info("[RISK MANAGER]: Book prices are updated")
                            print(self.risk_engine.book)
                            #print(self.risk_engine.id_to_idx)
                        
                        else:
                            self.risk_engine.process_trade(fields[1], fields[2], fields[3], fields[4])
                            logger.info("[RISK MANAGER]: trade is processed")
                            print(self.risk_engine.book)
                            #print(self.risk_engine.id_to_idx)
                        '''
                        t3= time.perf_counter_ns()
                        print(f"\n[CALCULATIONS TIME]: ({(t3 - t2) / 1000 :.2f}")
                        self.cb.advance()
                    #t1= time.perf_counter_ns()
                    #print(f"\n[SOCKET TIME]: ({(t1 - t0) / 1000 :.2f}")

                # Try to read the binary data except reader or writer want to read but no data. Wait and don't close the socket
                except (ssl.SSLWantReadError, ssl.SSLWantWriteError):
                    if self.ssock.pending() > 0:
                        await asyncio.sleep(0)
                        continue
                        
                    waiter= self.loop.create_future()
                    # Get the socket stream number from OS
                    fd= self.ssock.fileno()
                    self.loop.add_reader(fd, lambda: waiter.set_result(None) or waiter.done())

                    try:
                        logger.info("[HANDLER]: Waiter is created for data")
                        await waiter
                    finally:
                        logger.info("[HANDLER]: File discriptor is closing")
                        self.loop.remove_reader(fd)
                    continue
                
        except ConnectionResetError:
            print(f"Connection reset by client peer")


    async def clear_connection(self):
        try:
            # Clear the background tasks  
            if self.tasks:
                for task in self.tasks:
                    logger.info(f"[SERVER]: Task-{task.get_name()} is closing")
                    if not task.done():
                        task.cancel()
            await asyncio.gather(*self.tasks)
            logger.info("[SERVER]: Tasks are cleared")

        except Exception as e:
            logger.debug(f"[SERVER]:Error in closing the scheduled tasks: {e}")

        try:
            # Close the socket
            if self.ssock:
                logger.info(f"[SERVER]: ssock {self.ssock.getsockname()} is closing")
                self.ssock.close()

        except Exception as e:
            logger.debug(f"[SERVER]:Error in closing the scheduled tasks: {e}")

        finally:
            print("f\n[SERVER]: Server shut down gracefully")
            logger.info("[SERVER]: Server shut down gracefully")



'''
async def main():
    conn_hand= ConnectionHandler()
    risk_engine= RiskEngine()
    try:
        conn_hand.add_risk_engine(risk_engine)
        await conn_hand.start_server()

    except Exception as e:
        logger.debug(f"Error in opening the socket: {e}")
        print(f"[SERVER]: Error in opening the socket: {e}")
    except KeyboardInterrupt:
        await conn_hand.clear_connection()
    
    finally:
        await conn_hand.clear_connection()
        
    

if __name__ == "__main__":
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupted - closed the event loop")
'''



            


    

                        
                    
                    

