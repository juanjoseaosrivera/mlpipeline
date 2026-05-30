export interface PredictPayload {
  feature_1: number;
  feature_2: number;
  category: number;
}

export interface PredictResponse {
  prediction: number;
  probability: number;
  latency_ms: number;
  model_version: string;
}

export type PredictionError =
  | { kind: 'network'; message: string }
  | { kind: 'validation'; message: string }
  | { kind: 'server'; message: string; status: number }
  | { kind: 'unknown'; message: string; status: number };
