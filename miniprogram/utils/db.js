// Local cache for offline-first operation.
//
// Stores the checklist and each inspection (header + expected devices + issues)
// so an engineer can download a store, work without connectivity, and sync later.
const PREFIX = 'cache:';
const IDS_KEY = `${PREFIX}inspection_ids`;

function setInspection(id, data) {
  wx.setStorageSync(`${PREFIX}inspection:${id}`, data);
  const ids = listCachedInspectionIds();
  if (!ids.includes(id)) {
    ids.push(id);
    wx.setStorageSync(IDS_KEY, ids);
  }
}

function getInspection(id) {
  return wx.getStorageSync(`${PREFIX}inspection:${id}`) || null;
}

function removeInspection(id) {
  wx.removeStorageSync(`${PREFIX}inspection:${id}`);
  wx.setStorageSync(IDS_KEY, listCachedInspectionIds().filter((x) => x !== id));
}

function listCachedInspectionIds() {
  return wx.getStorageSync(IDS_KEY) || [];
}

function setChecklist(data) {
  wx.setStorageSync(`${PREFIX}checklist`, data);
}

function getChecklist() {
  return wx.getStorageSync(`${PREFIX}checklist`) || null;
}

module.exports = {
  setInspection,
  getInspection,
  removeInspection,
  listCachedInspectionIds,
  setChecklist,
  getChecklist,
};
