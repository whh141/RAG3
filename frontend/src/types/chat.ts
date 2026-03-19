export type ModelProvider = "zhipuai" | "openai";
export type AgentMode = "baseline_rag" | "agentic_rag";
export type MessageRole = "system" | "user" | "assistant";

export interface Citation {
  source_type: string;
  source_name: string;
  chunk_id?: string | null;
  score?: number | null;
  url?: string | null;
}

export interface SessionDTO {
  id: string;
  title: string;
  description?: string | null;
  model_provider: ModelProvider | string;
  agent_mode: AgentMode | string;
  created_at: string;
  updated_at: string;
  last_message_at?: string | null;
}

export interface MessageDTO {
  id: string;
  role: MessageRole;
  content: string;
  content_format: string;
  message_status: string;
  citations: Citation[];
  trace_id?: string | null;
  latency_ms?: number | null;
  created_at: string;
}

export interface CreateSessionRequest {
  title?: string;
  model_provider?: ModelProvider;
  agent_mode?: AgentMode;
}

export interface CreateSessionResponse {
  session_id: string;
  title: string;
  created_at: string;
}
