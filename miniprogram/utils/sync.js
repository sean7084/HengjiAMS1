// Sync engine: flushes the offline queue to the server.
//
// Ordering matters - a device must exist before its extra photos, so device
// upserts carry their first photo (multipart) and remaining photos follow.
// On a network error the flush stops and leaves the rest pending; permanent
// (4xx) errors are marked failed so they surface on the sync page for review.
const request = require('./request');
const queue = require('./queue');

async function flushOne(item) {
  const { type, inspectionId } = item;

  if (type === 'device') {
    const fields = item.fields || {};
    const photos = item.photos || [];
    if (photos.length) {
      const [first, ...rest] = photos;
      const formData = {
        client_device_uid: item.client_device_uid,
        ...fields,
        [`${first.part}_uid`]: first.uid,
        [`${first.part}_index`]: first.index || 0,
      };
      await request.uploadFile(`/inspections/${inspectionId}/devices/`, first.filePath, first.part, formData);
      for (const photo of rest) {
        await request.uploadFile(`/inspections/${inspectionId}/photos/`, photo.filePath, 'image', {
          kind: photo.kind,
          client_device_uid: item.client_device_uid,
          client_photo_uid: photo.uid,
          sort_index: photo.index || 0,
        });
      }
    } else {
      await request.request(`/inspections/${inspectionId}/devices/`, {
        method: 'POST',
        data: { client_device_uid: item.client_device_uid, ...fields },
      });
    }
    return;
  }

  if (type === 'photo') {
    await request.uploadFile(`/inspections/${inspectionId}/photos/`, item.filePath, 'image', {
      kind: item.kind,
      client_photo_uid: item.client_photo_uid,
      client_device_uid: item.client_device_uid || '',
      sort_index: item.sort_index || 0,
    });
    return;
  }

  if (type === 'issue') {
    await request.request(`/inspections/${inspectionId}/issues/`, { method: 'POST', data: item.fields });
    return;
  }

  if (type === 'inspection') {
    await request.request(`/inspections/${inspectionId}/`, { method: 'PATCH', data: item.fields });
    return;
  }

  if (type === 'signoff') {
    // Merged confirmation fields (device counts / IT rating / wifi coverage) go
    // through a PATCH first; signatures then upload and mark submitted.
    if (item.fields && Object.keys(item.fields).length) {
      await request.request(`/inspections/${inspectionId}/`, { method: 'PATCH', data: item.fields });
    }
    // wx.uploadFile sends one file per call; the endpoint accepts each signature
    // independently and marks the inspection submitted.
    for (const sig of item.signatures || []) {
      await request.uploadFile(`/inspections/${inspectionId}/signoff/`, sig.filePath, sig.part, {});
    }
    return;
  }

  if (type === 'wifi_weak_points') {
    await request.request(`/inspections/${inspectionId}/wifi-weak-points/`, {
      method: 'POST',
      data: { weak_points: item.weak_points || [] },
    });
    return;
  }

  throw new Error(`UNKNOWN_QUEUE_TYPE:${type}`);
}

async function flush(options = {}) {
  const { onProgress } = options;
  const items = queue.pending();
  let synced = 0;
  let failed = 0;

  for (const item of items) {
    try {
      await flushOne(item);
      queue.markDone(item.uid);
      synced += 1;
    } catch (err) {
      queue.markFailed(item.uid, err);
      failed += 1;
      if (err && err.networkError) {
        // Offline: stop now, keep the remainder pending for the next attempt.
        break;
      }
    }
    if (onProgress) onProgress({ synced, failed, total: items.length });
  }

  queue.prune();
  return { synced, failed, remaining: queue.pending().length };
}

module.exports = { flush, flushOne };
