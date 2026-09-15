// Assigned store inspections list, with offline fallback to the local cache.
const request = require('../../utils/request');
const db = require('../../utils/db');
const queue = require('../../utils/queue');

Page({
  data: { inspections: [], loading: false, offline: false, pendingCount: 0 },

  onShow() {
    this.refreshPending();
    this.loadList();
  },

  onPullDownRefresh() {
    this.loadList().then(() => wx.stopPullDownRefresh());
  },

  refreshPending() {
    this.setData({ pendingCount: queue.pending().length });
  },

  async loadList() {
    this.setData({ loading: true });
    try {
      const data = await request.request('/inspections/');
      const list = (data && data.results) || data || [];
      list.forEach((item) => db.setInspection(item.id, item));
      this.setData({ inspections: list, offline: false });
    } catch (err) {
      // Offline (or error): show cached headers so the engineer can still work.
      const cached = db
        .listCachedInspectionIds()
        .map((id) => db.getInspection(id))
        .filter(Boolean);
      this.setData({ inspections: cached, offline: true });
    } finally {
      this.setData({ loading: false });
    }
  },

  openDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/inspection-detail/inspection-detail?id=${id}` });
  },

  goSync() {
    wx.navigateTo({ url: '/pages/sync/sync' });
  },
});
