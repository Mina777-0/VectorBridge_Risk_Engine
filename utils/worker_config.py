import asyncio, sys, os 
#from protocols_schemas import RiskEngine
from typing import Optional
from queue_config import QueueManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'risk_manager/target/debug')))

#print(sys.path)
from risk_manager import RiskEngine
from utils.log_config import get_logger

logger= get_logger()





class WorkerManager:
    def __init__(self, **kw):
        self.risk_engine:RiskEngine = None
        self.workers= []
        self.qm: Optional[QueueManager]= None    
        self.max_workers= kw.get('max_worker') if kw.get('max_worker') else 2

    def add_queue_manager(self, qm: QueueManager):
        self.qm= qm

    def add_risk_engine(self, risk_engine):
        self.risk_engine= risk_engine

    async def initiate_worker(self):
        #for _ in range(self.max_workers):
        for qname in self.qm._list:
            try:
                task= asyncio.create_task(self.worker(qname))
                self.workers.append(task)
                print(f"\n[WORKER MANAGER]: Started {len(self.workers)} persistent workers")
                logger.info(f"[WM]: Started persistent worker-{task.get_name()}")
            except asyncio.CancelledError as e:
                raise e

    
    async def worker(self, qname:str):

        while True:
            try:
                packet= await self.qm.pull_items(qname)
                print(f"\n[WORKER MANAGER]: {packet}")
                msg_type, symbol_id, price, volume, side= packet

                # Do the RiskEngine work
                if msg_type == 0:
                    self.risk_engine.update_price(symbol_id, price)
                else:
                    self.risk_engine.process_trade(symbol_id, volume, side, price)

                #print(f"[RISK ENGINE]: {self.risk_engine.id_to_idx}")
                #metrics= self.risk_engine.calculate_metrics()
                #print(metrics.symbol_data)
                #print(metrics.to_json())
                
                self.qm.pool[qname].task_done()
                
            except Exception as e:
                continue

            
    
    async def close_worker(self):
        if self.qm is not None:
            for qn in self.qm._list:
                queue= self.qm.pool[qn]
                if not queue.empty():
                    await queue.join()
                    await asyncio.sleep(2.0)


        if self.workers:
            for worker in self.workers:
                logger.info(f"Worker-{worker.get_name()} is closing")
                if not worker.done():
                    worker.cancel()
            await asyncio.gather(*self.workers)
            logger.info("[WM]: workers are cleared")
        self.workers.clear()
        

        
'''
async def demo():
    symbol_id_1= 1001
    symbol_id_2= 1002

    risk_engine= RiskEngine(10)
    risk_engine.get_idx(symbol_id_1)
    risk_engine.get_idx(symbol_id_2)


    print(risk_engine.book[0])
    print(risk_engine.id_to_idx)


if __name__ == "__main__":
    asyncio.run(demo())

'''