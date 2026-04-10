import socket, asyncio, os, sys, ssl, random
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from utils.protocols_schemas import FinancialProtocol
from utils.log_config import get_logger


cert_file= os.path.abspath(os.path.join(os.path.dirname(__file__), 'cert.pem'))
logger= get_logger()
#logger.info("Client TEST")



class ClientConnection:
    def __init__(self, **kw):
        self.ssock: Optional[socket.socket]= None


    async def connect_to_server(self, host:str, port:int):
        global cert_file

        context= ssl.create_default_context()
        context.check_hostname= False # True for production
        context.verify_mode= ssl.CERT_REQUIRED

        try:
            context.load_verify_locations(cert_file)

        except FileNotFoundError:
            logger.error(f"[CLIENT]: 'cert.pem' file is missing")
            raise 
        
        sock= socket.socket(family=socket.AF_INET, type= socket.SOCK_STREAM)
        # Wrap the socket for SSL/TLS 
        self.ssock= context.wrap_socket(sock, server_hostname= host)

        try:
            self.ssock.connect((host,port))
            logger.info(f"[CLIENT]: SSL/TLS handashake with server {host}:{port} is successful. Porotocl= {self.ssock.version()}")
            print(f"\n[CLIENT]: SSL/TLS handashake with server {host}:{port} is successful. Porotocl= {self.ssock.version()}")

        except ConnectionRefusedError as e:
            logger.debug(f"[CLIENT]: Connection refused: {e}. Is server running?")
            raise ConnectionError("Connection refused. Is server running?")
        except Exception as e:
            logger.debug(f"An Unexpected error occured: {e}")
            raise e

    async def send_packet(self, packet: FinancialProtocol):
        if self.ssock is None:
            logger.error(f"[CLIENT]: sock is None or closed")
            return
        
        try:
            self.ssock.sendall(packet.pack())

        except Exception as e:
            logger.error(f"[CLIENT]: Error sending the packet: {e}")
            raise e 
        

            

async def start_client():
    try:
        client= ClientConnection()
        await client.connect_to_server(host="127.0.0.1", port=2345)

    except Exception as e:
        print(f"\n[CLIENT]: Error in connecting to the server: {e}")
    
    # 1001 (EURUSD), 1002 (Gold), 1003 (Bitcoin)
    symbols= [1001, 1002, 1003]
    prices= {
        1001: 1.17,
        1002: 2300.0,
        1003: 65000.0,
    }

    i =0
    while True:
        try:
            for s_id in symbols:
                prices[s_id] += random.uniform(-0.5, 0.5)
                await client.send_packet(
                    FinancialProtocol(
                        msg_type= 0,
                        symbol_id= s_id,
                        price= round(prices[s_id], 2),
                        volume= 100,
                        side= 0,
                    )
                )
                
                if random.random() < 0.1:
                    trade_side= random.choice([1,2])
                    trade_packet= FinancialProtocol(
                        msg_type= 1,
                        symbol_id= s_id,
                        price= round(prices[s_id], 2),
                        volume= random.randint(1, 10),
                        side= trade_side
                    )

                    await client.send_packet(trade_packet)

            await asyncio.sleep(0.05)
            i +=1
            if i > 150:
                break
        except Exception as e:
            print(f"\n[CLIENT]: Error sending packet: {e}")

    
        


if __name__ == "__main__":
    asyncio.run(start_client())


