import test from "node:test";
import assert from "node:assert/strict";

import { scanAnnouncement } from "../src/lib/scan-state.ts";
import { routeTitle, focusPageHeading } from "../src/lib/route-state.ts";
import { settleScannerOverview } from "../src/lib/scanner-overview.ts";
import { getTranslation } from "../src/lib/translations.ts";
import { ApiError } from "../src/lib/api.ts";
import { friendlyError } from "../src/lib/errors.ts";

test("scan announcements ignore elapsed-time-only polling updates", () => {
  const base = {
    status: "running",
    current_tool: "nmap",
    completed_tools: 1,
    total_tools: 4,
  };

  const labels = { status: "Running", tool: "Nmap", completedTools: "Tools completed" };
  assert.equal(
    scanAnnouncement({ ...base, elapsed: 2 }, labels),
    "Running · Nmap. Tools completed: 1/4",
  );
  assert.equal(
    scanAnnouncement({ ...base, elapsed: 2 }, labels),
    scanAnnouncement({ ...base, elapsed: 20 }, labels),
  );
  assert.notEqual(
    scanAnnouncement({ ...base, elapsed: 2 }, labels),
    scanAnnouncement({ ...base, current_tool: "zap", completed_tools: 2, elapsed: 22 }, { ...labels, tool: "ZAP" }),
  );
});

test("route metadata names each application surface", () => {
  const en = getTranslation("en");
  const ar = getTranslation("ar");
  for (const route of ["/", "/login", "/scanner", "/auth-system.html"]) {
    assert.equal(routeTitle(route, en.pageTitles), "Scanner · SecScan");
  }
  assert.equal(routeTitle("/missing", ar.pageTitles), "الصفحة غير موجودة · SecScan");
});

test("route focus targets the page heading without scrolling", () => {
  const calls = [];
  const heading = {
    hasAttribute: () => false,
    setAttribute: (...args) => calls.push(["setAttribute", ...args]),
    focus: options => calls.push(["focus", options]),
  };

  assert.equal(focusPageHeading({ querySelector: selector => selector === "main h1" ? heading : null }), true);
  assert.deepEqual(calls, [["setAttribute", "tabindex", "-1"], ["focus", { preventScroll: true }]]);
  assert.equal(focusPageHeading({ querySelector: () => null }), false);
});

test("scanner overview preserves each successful request independently", async () => {
  const history = { scans: [{ scan_id: "scan-1" }] };
  const tools = { tools: { nmap: { available: true } }, allowed_hosts: ["localhost"] };

  assert.deepEqual(
    await settleScannerOverview(Promise.resolve(history), Promise.reject(new Error("tools offline"))),
    { history, tools: null, historyError: "", toolsError: "tools offline" },
  );
  assert.deepEqual(
    await settleScannerOverview(Promise.reject(new Error("history offline")), Promise.resolve(tools)),
    { history: null, tools, historyError: "history offline", toolsError: "" },
  );
});

test("Arabic errors replace unmarked English server text with actionable localized copy", () => {
  const ar = getTranslation("ar");
  const serverError = new ApiError("This browser origin is not allowed.", 403);
  assert.equal(friendlyError(serverError, "ar", ar), ar.errors.forbidden);
  assert.notEqual(friendlyError(serverError, "ar", ar), serverError.message);
  assert.equal(friendlyError(new Error("Network unavailable"), "ar", ar), ar.errors.connection);
});

test("English errors preserve useful backend detail", () => {
  const en = getTranslation("en");
  assert.equal(friendlyError(new ApiError("A scan is already running.", 409), "en", en), "A scan is already running.");
});
