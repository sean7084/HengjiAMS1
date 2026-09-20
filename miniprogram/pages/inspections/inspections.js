// Assigned store inspections list, with offline fallback to the local cache.
const request = require('../../utils/request');
const db = require('../../utils/db');
const queue = require('../../utils/queue');
const auth = require('../../utils/auth');

Page({
  data: { inspections: [], loading: false, offline: false, pendingCount: 0, meName: '', meCities: '' },

  onShow() {
    this.loadIdentity();
    this.refreshPending();
    this.loadList();
  },

  // Show the signed-in field engineer's Chinese name + service cities so they can
  // flag corrections (both values are maintained on the backend account).
  loadIdentity() {
    const me = auth.getUser() || {};
    const cn = me.chinese_name || '';
    const en = me.english_name || '';
    let name = en;
    if (cn) name = en ? cn + ' (' + en + ')' : cn;
    this.setData({
      meName: name || me.username || '',
      meCities: (me.service_city_names || []).join('、'),
    });
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
