import test from 'node:test';
import assert from 'node:assert/strict';
import { scanProgress, isActiveScan } from '../src/lib/scan-state.ts';

test('progress reflects completed tools and never fabricates running progress', () => {
  assert.equal(scanProgress({ completed_tools: 0, total_tools: 4 }), 0);
  assert.equal(scanProgress({ completed_tools: 2, total_tools: 4 }), 50);
  assert.equal(scanProgress({ completed_tools: 4, total_tools: 4 }), 100);
  assert.equal(scanProgress({ completed_tools: 0, total_tools: 0 }), 0);
});

test('only queued and running scans block a new scan', () => {
  assert.equal(isActiveScan({ status: 'queued' }), true);
  assert.equal(isActiveScan({ status: 'running' }), true);
  assert.equal(isActiveScan({ status: 'error' }), false);
  assert.equal(isActiveScan({ status: 'finished' }), false);
  assert.equal(isActiveScan(null), false);
});
