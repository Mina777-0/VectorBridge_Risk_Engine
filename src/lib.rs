use pyo3::prelude::*;
use std::collections::HashMap;
use serde::Serialize;
use pyo3::exceptions::PyValueError;


#[derive(Clone, Default, Serialize)]
#[pyclass(get_all)]
pub struct BookRow {
    pub symbol_id: u32,
    pub last_price: f64,
    pub position: i64,
    pub avg_entry: f64,
    pub realised_pnl: f64,
}


#[pyclass]
struct RiskEngine {
    #[pyo3(get)]
    book: Vec<BookRow>,
    #[pyo3(get)]
    id_to_idx: HashMap<u32, usize>,
}

#[pyclass(get_all)]
#[derive(Serialize)]
struct Metrics {
    pub total_pnl: f64,
    pub total_exposure: f64, 
    pub symbol_data: Vec<BookRow>,
}


#[pymethods]
impl Metrics {
    pub fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self).map_err(|err| PyErr::new::<PyValueError, _>(err.to_string()))
    }
}


#[pymethods]
impl RiskEngine {
    #[new]
    pub fn new(max_size: usize) -> Self {
        RiskEngine {
            book: Vec::with_capacity(max_size),
            id_to_idx: HashMap::with_capacity(max_size),
        }
    }


    pub fn get_idx(&mut self, symbol_id: u32) -> usize {
        if let Some(&idx)= self.id_to_idx.get(&symbol_id) {
            return idx;
        }

        let new_idx= self.book.len();
        let mut new_row= BookRow::default();
        new_row.symbol_id= symbol_id;
        
        self.book.push(new_row);
        self.id_to_idx.insert(symbol_id, new_idx);

        new_idx
    }

    pub fn update_price(&mut self, symbol_id: u32, last_price: f64) {
        let idx: usize= self.get_idx(symbol_id);
        if let Some(row) = self.book.get_mut(idx) {
            row.last_price= last_price;
        }
    }

    pub fn process_trade(&mut self, symbol_id: u32, volume: u64, side: i64, exec_price: f64) {
        let idx:usize= self.get_idx(symbol_id);
        let our_side= if side == 1 { -1 } else { 1 };
        let qty= (volume as i64) * our_side;

        if let Some(row)= self.book.get_mut(idx) {
            let current_position= row.position;
            let total_qty = row.position + qty;

            if current_position == 0 || current_position.signum() == qty.signum() {
                row.avg_entry= ((current_position as f64 * row.avg_entry) + (qty as f64 * exec_price)) / total_qty as f64;
                row.position = total_qty;

            } else {
                row.position = total_qty;
                row.realised_pnl= (exec_price - row.avg_entry) * volume as f64;
            }
        }
    }

    pub fn calculate_metrics(&self) -> Metrics {
        let active_index= self.book.len();
        let active_rows= &self.book[0..active_index];
        
        let total_unrealised_pnl: f64= active_rows.iter()
        .map(|row| (row.last_price - row.avg_entry) * row.position as f64).sum();
        
        let total_realised_pnl: f64= active_rows.iter()
        .map(|row| row.realised_pnl).sum();

        let total_exposure: f64= active_rows.iter()
        .map(|row| (row.position.abs() as f64) * row.last_price).sum();

        
        Metrics {
            total_pnl: total_realised_pnl + total_unrealised_pnl,
            total_exposure,
            symbol_data: active_rows.to_vec(),
        }
    }
}


/// A Python module implemented in Rust.
#[pymodule]
fn risk_manager(m:&Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<BookRow>()?;
    m.add_class::<RiskEngine>()?;
    m.add_class::<Metrics>()?;

    Ok(())
}
