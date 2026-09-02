// No eager throw here: this module is evaluated during `next build`'s page-data
// collection pass for every route (including API routes), so throwing at
// import time would fail the build even though AGENT_URL is only genuinely
// needed once a real request comes in. See backendClient.ts for the actual
// runtime check.
export const config = {
  backendUrl: process.env.AGENT_URL,
  assistantId: process.env.AGENT_ID ?? "agent",
};
