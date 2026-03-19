export interface EvalRunDTO {
  id: string;
  name: string;
  dataset_name: string;
  status: string;
  question_count: number;
  created_at: string;
  finished_at?: string | null;
}

export interface EvalRecordDTO {
  id: string;
  question: string;
  reference_answer?: string | null;
  baseline_answer?: string | null;
  agent_answer?: string | null;
  baseline_latency_ms?: number | null;
  agent_latency_ms?: number | null;
  baseline_score?: number | null;
  agent_score?: number | null;
  route_expected?: string | null;
  route_actual?: string | null;
  route_correct: boolean;
}

export interface StartEvalRequest {
  name: string;
  dataset_name: string;
  question_count?: number;
  model_provider?: "zhipuai" | "openai";
}
