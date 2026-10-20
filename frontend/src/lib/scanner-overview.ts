function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "The request failed.";
}

export async function settleScannerOverview<History, Tools>(
  historyRequest: Promise<History>,
  toolsRequest: Promise<Tools>,
) {
  const [historyResult, toolsResult] = await Promise.allSettled([historyRequest, toolsRequest]);
  return {
    history: historyResult.status === "fulfilled" ? historyResult.value : null,
    tools: toolsResult.status === "fulfilled" ? toolsResult.value : null,
    historyError: historyResult.status === "rejected" ? errorMessage(historyResult.reason) : "",
    toolsError: toolsResult.status === "rejected" ? errorMessage(toolsResult.reason) : "",
  };
}
