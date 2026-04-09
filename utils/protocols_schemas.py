import struct
from dataclasses import dataclass
import numpy as np 

@dataclass(slots=True)
class FinancialProtocol:
    msg_type: int # 0 for price, 1 for trade
    symbol_id: int
    price: float # For price: mid-price for trade: execution price
    volume: int # for price: Liquidity for trade: Quantity
    side: int # 0 for None, 1 for client buy, 2 for client sell


    FORMAT= '!BIdQq'
    def pack(self):
        return struct.pack(
            self.FORMAT,
            self.msg_type,
            self.symbol_id,
            self.price,
            self.volume,
            self.side,
        )
    


class RiskEngine:
    def __init__(self, max_symbols= 5):
        self.book= np.zeros(max_symbols, dtype=[
            ('symbol_id', 'i4'),
            ('last_price', 'f8'),
            ('position', 'i8'),
            ('avg_entry', 'f8'),
            ('realised_pnl', 'f8'),
        ])

        self.id_to_idx= {}
        self.next_idx= 0


    def get_idx(self, symbol_id):
        if symbol_id not in self.id_to_idx:
            idx= self.next_idx
            self.book[idx]['symbol_id']= symbol_id
            self.id_to_idx[symbol_id]= idx
            self.next_idx +=1
            return idx
        
        return self.id_to_idx[symbol_id]
    
    def update_market_price(self, symbol_id, price):
        idx= self.get_idx(symbol_id)
        self.book[idx]['last_price'] = price 


    def process_trade(self, symbol_id, exec_price, volume, side):
        idx= self.get_idx(symbol_id)
        row= self.book[idx]

        our_side= -1 if side == 1 else 1 
        quantity= our_side * volume

        current_position= row['position']
        # Check my current position. If I'm flat or same (long or short)
        if current_position == 0 or np.sign(current_position) == np.sign(quantity):
            new_total_quantity= current_position + quantity
            row['avg_entry']= ((current_position * row['avg_entry']) + (quantity * exec_price)) / new_total_quantity
            row['position']= new_total_quantity
        else:
            row['position'] += quantity
            realised_pnl= (exec_price - row['avg_entry']) * volume
            row['realised_pnl']= realised_pnl

    def calculate_metrics(self):
        active_rows= self.book[: self.next_idx].copy()
        #print(f"ACTIVE ROWS= {active_rows}")

        unrealised_pnl= (active_rows['last_price'] - active_rows['avg_entry']) * active_rows['position'] 
        total_pnl= np.sum(unrealised_pnl) + np.sum(active_rows['realised_pnl'])
        total_exposure= np.sum(np.abs(active_rows['position']) * active_rows['last_price'])

        return {
            'total_pnl': float(total_pnl),
            'total_exposure': float(total_exposure),
            'symbol_data': active_rows.tolist(),
        }
    





class CircularBuffer:
    def __init__(self, size: int):
        self.buffer= bytearray(size)
        self.mv= memoryview(self.buffer)
        self.size= size
        self.tail= 0
        self.head= 0
        self.count= 0
        self.packet_format= "!BIdQq"
        self.packet_size= struct.calcsize(self.packet_format)

    
    def write_to(self):
        return self.mv[self.tail: ]
    
    def did_write(self, nbytes: int):
        self.tail= (self.tail + nbytes) % self.size
        #print(f"Tail= {self.tail}")
        self.count += nbytes
        #print(f"Count= {self.count}")

    def peek(self):
        if (self.head + self.packet_size) > self.size:
            left_chunk= self.size - self.head
            #print(f"Left-chunk={left_chunk}")
            #self.mv[: left_chunk]= self.buffer[self.head: ]
            self.head= (self.head + left_chunk) % self.size
            
            return struct.unpack_from(self.packet_format, self.mv, self.head)

        else:
            return struct.unpack_from(self.packet_format, self.mv, self.head)
        
        
    def advance(self):
        self.head= (self.head + self.packet_size) % self.size
        #print(f"Head= {self.head}")
        self.count -= self.packet_size
        #print(f"fin-Count: {self.count}")

        if (self.tail + self.packet_size) > self.size:
            left_chunk= self.size - self.tail
            self.tail = (self.tail + left_chunk) % self.size
            #print(f"fin-tail= {self.tail}")



