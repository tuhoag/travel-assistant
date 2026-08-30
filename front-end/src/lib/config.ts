export const config = {
  backendUrl: process.env.AGENT_URL ?? "http://127.0.0.1:8000",
  assistantId: process.env.AGENT_ID ?? "agent",
};
