import type { AgentMode, Citation, ModelProvider } from "./chat";

export interface AskEvent {
  action: "ask";
  request_id: string;
  query: string;
  model_provider?: ModelProvider;
  agent_mode?: AgentMode;
}

export interface AgentStateEvent {
  type: "agent_state";
  request_id: string;
  trace_id: string;
  node: string;
  status: string;
  summary: string;
  extra: Record<string, unknown>;
  timestamp: string;
}

export interface ChunkEvent {
  type: "chunk";
  request_id: string;
  trace_id: string;
  content: string;
}

export interface DoneEvent {
  type: "done";
  request_id: string;
  trace_id: string;
  answer: string;
  citations: Citation[];
  latency_ms: number;
}

export interface ErrorEvent {
  type: "error";
  request_id?: string;
  trace_id?: string;
  message: string;
  code: string;
}

export type WsServerEvent = AgentStateEvent | ChunkEvent | DoneEvent | ErrorEvent;
