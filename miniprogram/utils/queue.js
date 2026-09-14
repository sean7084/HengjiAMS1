// Persistent offline mutation queue.
//
// Every onsite change (device reading, photo, issue, store-level field, signoff)
// is enqueued with a stable dedupeKey so re-submits collapse into one entry and
// the server's client_device_uid / client_photo_uid idempotency prevents
// duplicates. The queue survives app restarts (wx storage).
const QUEUE_KEY = 'sync_queue';

function readQueue() {
  return wx.getStorageSync(QUEUE_KEY) || [];
}
function writeQueue(items) {
  wx.setStorageSync(QUEUE_KEY, items);
}
function uid() {
  return `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
}

// item: { type, inspectionId, dedupeKey, ...payload }
function enqueue(item) {
  const items = readQueue();
  const entry = { uid: item.uid || uid(), createdAt: Date.now(), attempts: 0, status: 'pending', ...item };
  const key = item.dedupeKey;
  const existingIndex = key
    ? items.findIndex((i) => i.dedupeKey === key && i.status !== 'done')
    : -1;
  if (existingIndex >= 0) {
    entry.uid = items[existingIndex].uid; // keep identity stable across edits
    items[existingIndex] = entry;
  } else {
    items.push(entry);
  }
  writeQueue(items);
  return entry;
}

function pending() {
  return readQueue().filter((i) => i.status !== 'done');
}

function markDone(itemUid) {
  const items = readQueue();
  const item = items.find((i) => i.uid === itemUid);
  if (item) item.status = 'done';
  writeQueue(items);
}

function markFailed(itemUid, error) {
  const items = readQueue();
  const item = items.find((i) => i.uid === itemUid);
  if (item) {
    item.attempts = (item.attempts || 0) + 1;
    item.status = 'failed';
    item.lastError = String((error && error.message) || error || '');
  }
  writeQueue(items);
}

// Drop completed items; keep failed/pending for retry.
function prune() {
  writeQueue(readQueue().filter((i) => i.status !== 'done'));
}

function clear() {
  writeQueue([]);
}

module.exports = { enqueue, pending, markDone, markFailed, prune, clear, readQueue, uid };
