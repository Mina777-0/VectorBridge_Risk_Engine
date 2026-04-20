import asyncio 
from typing import Dict, Any
import uuid 
import numpy as np
from collections import deque


PoolFormat= Dict[str, asyncio.Queue]

class QueueInitError(Exception):
    '''Failed to initiate new queue'''
    pass 

class QueueAddError(Exception):
    '''Item failed to be added to the queue'''
    pass 

class QueueEmptyError(Exception):
    '''Queue is empty'''
    pass 

class QueueNameError(Exception):
    '''Queue name is error'''
    pass 


class QueueManager:
    def __init__(self, **kw):
        self.pool: PoolFormat= {}
        self._list= []
        self.capapcity= kw.get('capacity') if kw.get('capacity') else 4
        self.timeout: float= kw.get('timeout') if kw.get('timeout') else 2.0
        self.current_idx= 0
    

    def initiate_queues(self):
        # Check if the pool is full of queues 
        if len(self._list) >= self.capapcity:
            raise QueueInitError(f"\n[QUEUE MANAGER]: Cannot initialise new queue")
        
        for _ in range(self.capapcity):
            queue_name= uuid.uuid4().hex
            self.pool[queue_name]= asyncio.Queue(maxsize=10)
            self._list.append(queue_name)
            print(f"\n[QUEUE MANAGER]: New queue {queue_name} is initiated")
        


    async def add_items(self, item: Any) -> None:
        for _ in range(len(self._list)):
            qname= self._list[self.current_idx]
            queue= self.pool[qname]
            self.current_idx = (self.current_idx + 1) % self.capapcity
            
            try:
                await asyncio.wait_for(queue.put(item), timeout= self.timeout)
                #print(f"\n[QUEUE MANAGER]: An item {item} is added to queue {qname}. Qsize= {queue.qsize()}")
                return
            except asyncio.TimeoutError:
                continue

        raise QueueAddError(f"\n[QUEUE MANAGER]: All queues are currently full")

            


    async def pull_items(self, qname: str) -> Any:
        if qname not in self._list:
            raise QueueNameError(f"\n[QUEUE MANAGER]: {qname} is invalid")
        
        queue= self.pool[qname]

        try:
            item= await asyncio.wait_for(queue.get(), timeout= self.timeout)
            return item 
        except asyncio.TimeoutError:
            raise QueueEmptyError(f"\n[QUEUE MANAGER]: No items available")



'''
async def main():
    qm= QueueManager()
    qm.initiate_queues()
    items= [f"task-{i}" for i in range(42)]
    try:
        for item in items:
            await qm.add_items(item)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass 
'''
        