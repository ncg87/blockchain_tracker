use ethabi::{Contract, Token, Event, ParamType};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use hex;
use web3::types::H256;
use std::sync::Arc;
use lru_time_cache::LruCache;
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize)]
pub struct LogEntry {
    pub address: String,
    pub topics: Vec<String>,
    pub data: String,
    pub log_index: u64,
    pub transaction_hash: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EventSignature {
    pub signature_hash: String,
    pub event_name: String,
    pub decoded_signature: String,
    pub input_types: Vec<String>,
    pub indexed_inputs: Vec<bool>,
    pub input_names: Vec<String>,
    pub inputs: Vec<EventInput>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EventInput {
    pub name: String,
    pub r#type: String,
    pub indexed: bool,
    pub description: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DecodedParameter {
    pub value: Token,
    pub r#type: String,
    pub indexed: bool,
    pub description: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DecodedLog {
    pub event: String,
    pub parameters: Option<HashMap<String, DecodedParameter>>,
    pub signature: Option<String>,
    pub decode_error: Option<String>,
    pub log_index: u64,
}

pub struct LogDecoder {
    event_signature_cache: LruCache<String, Arc<EventSignature>>,
}

impl LogDecoder {
    pub fn new() -> Self {
        Self {
            event_signature_cache: LruCache::with_expiry_duration(Duration::from_secs(24 * 3600)),
        }
    }

    pub fn decode_log(&mut self, log: &LogEntry, event_sig: &EventSignature) -> DecodedLog {
        if log.topics.is_empty() {
            return DecodedLog {
                event: "Unknown".to_string(),
                parameters: None,
                signature: None,
                decode_error: Some("No topics found".to_string()),
                log_index: log.log_index,
            };
        }

        let mut decoded = DecodedLog {
            event: event_sig.event_name.clone(),
            parameters: Some(HashMap::new()),
            signature: Some(log.topics[0].clone()),
            decode_error: None,
            log_index: log.log_index,
        };

        // Skip if no parameters
        if event_sig.input_types.is_empty() {
            return decoded;
        }

        let params = decoded.parameters.as_mut().unwrap();
        
        // Process indexed parameters
        let mut topic_idx = 1;
        for (i, (input_type, is_indexed, input_name)) in event_sig.input_types.iter()
            .zip(&event_sig.indexed_inputs)
            .zip(&event_sig.input_names)
            .map(|((a, b), c)| (a, b, c))
            .enumerate() 
        {
            if !is_indexed {
                continue;
            }

            if topic_idx >= log.topics.len() {
                break;
            }

            let topic = &log.topics[topic_idx];
            topic_idx += 1;

            let value = self.decode_parameter(topic, input_type);
            
            params.insert(input_name.clone(), DecodedParameter {
                value,
                r#type: input_type.clone(),
                indexed: true,
                description: event_sig.inputs.get(i)
                    .and_then(|input| input.description.clone()),
            });
        }

        // Process non-indexed parameters
        if log.data != "0x" && !log.data.is_empty() {
            if let Ok(data) = hex::decode(&log.data[2..]) {
                let non_indexed: Vec<_> = event_sig.input_types.iter()
                    .zip(&event_sig.indexed_inputs)
                    .zip(&event_sig.input_names)
                    .filter(|((_, indexed), _)| !*indexed)
                    .collect();

                // Decode non-indexed parameters
                // Implementation details for non-indexed parameter decoding...
            }
        }

        decoded
    }

    fn decode_parameter(&self, hex_data: &str, param_type: &str) -> Token {
        // Implementation for parameter decoding
        // This would use ethabi's decoding functions
        Token::String("placeholder".to_string()) // Placeholder
    }
} 