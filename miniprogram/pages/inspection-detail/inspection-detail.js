// Inspection detail: progress, expected device list, barcode scan, offline cache.
const request = require('../../utils/request');
const db = require('../../utils/db');
const sync = require('../../utils/sync');

// Detail readings shown on each recorded device. They are visible by default;
// the engineer can hide any of them and the choice persists across inspections.
const DETAIL_COLUMNS = [
  { key: 'status', label: '状态 Status' },
  { key: 'windows_version', label: 'Windows 版本' },
  { key: 'ios_version', label: 'iOS 版本' },
  { key: 'ip_address', label: 'IP 地址' },
  { key: 'cpu', label: 'CPU' },
  { key: 'memory', label: '内存' },
  { key: 'hdd', label: '硬盘' },
  { key: 'drive_c_free_space', label: 'C盘可用空间' },
  { key: 'comment', label: '备注' },
];
const COLUMN_PREF_KEY = 'device_detail_columns';

function loadColumnPrefs() {
  const stored = wx.getStorageSync(COLUMN_PREF_KEY) || {};
  const prefs = {};
  DETAIL_COLUMNS.forEach((col) => {
    prefs[col.key] = stored[col.key] !== false;
  });
  return prefs;
}

Page({
  data: {
    id: '', inspection: null, devices: [], recorded: [], recordedCount: 0, expectedTotal: 0,
    loading: false, offline: false,
    colToggles: DETAIL_COLUMNS, colPrefs: {}, showCols: false,
  },

  onLoad(query) {
    this.setData({ id: query.id, colPrefs: loadColumnPrefs() });
  },

  onShow() {
    this.load();
  },

  async load() {
    this.setData({ loading: true });
    try {
      const detail = await request.request(`/inspections/${this.data.id}/`);
      db.setInspection(this.data.id, detail);
      this.setData({ inspection: detail, devices: detail.devices || [], offline: false });
      // Auto-record the arriving time when the FE first opens a planned inspection.
      if (detail && detail.status === 'planned') {
        try { await request.request(`/inspections/${this.data.id}/start/`, { method: 'POST' }); } catch (e) { /* ignore */ }
      }
    } catch (err) {
      const cached = db.getInspection(this.data.id);
      if (cached) {
        this.setData({ inspection: cached, devices: cached.devices || [], offline: true });
      }
    } finally {
      this.setData({ loading: false });
      this.computeCounts();
    }
  },

  // Blind count (盲盘): the master/expected asset list is hidden. Show only the
  // recorded/expected progress plus the engineer's own recorded entries so they
  // can review/correct them without seeing what is still outstanding.
  computeCounts() {
    const all = this.data.devices || [];
    const recorded = all.filter((d) => d.collected_at);
    const expectedTotal = all.filter((d) => !d.is_new_device).length;
    this.setData({ recorded, recordedCount: recorded.length, expectedTotal });
  },

  // Cache checklist + this inspection so the engineer can work without signal.
  async downloadOffline() {
    try {
      const checklist = await request.request('/inspections/checklist/');
      db.setChecklist(checklist);
      const detail = await request.request(`/inspections/${this.data.id}/`);
      db.setInspection(this.data.id, detail);
      this.setData({ inspection: detail, devices: detail.devices || [] });
      this.computeCounts();
      wx.showToast({ title: '已缓存，可离线巡检', icon: 'success' });
    } catch (err) {
      wx.showToast({ title: '下载失败（离线）', icon: 'none' });
    }
  },

  scan() {
    wx.scanCode({
      success: (res) => {
        const code = (res.result || '').trim();
        const match = this.data.devices.find(
          (d) => (d.sn && d.sn === code) || (d.asset_id_text && d.asset_id_text === code)
        );
        if (match) {
          this.openDeviceByUid(match.client_device_uid);
        } else {
          wx.showModal({
            title: '未找到设备',
            content: `条码 ${code} 不在预期清单中，作为新设备登记？`,
            success: (r) => {
              if (r.confirm) this.addDevice(code);
            },
          });
        }
      },
    });
  },

  openDevice(e) {
    this.openDeviceByUid(e.currentTarget.dataset.uid);
  },

  openDeviceByUid(uid) {
    wx.navigateTo({ url: `/pages/device-verify/device-verify?id=${this.data.id}&uid=${uid}` });
  },

  addDevice(code) {
    const query = code ? `&sn=${encodeURIComponent(code)}` : '';
    wx.navigateTo({ url: `/pages/device-verify/device-verify?id=${this.data.id}&new=1${query}` });
  },

  // Show/hide the detail-column chooser panel.
  toggleCols() {
    this.setData({ showCols: !this.data.showCols });
  },

  onToggleCol(e) {
    const key = e.currentTarget.dataset.key;
    const stored = wx.getStorageSync(COLUMN_PREF_KEY) || {};
    stored[key] = !!e.detail.value;
    wx.setStorageSync(COLUMN_PREF_KEY, stored);
    this.setData({ colPrefs: loadColumnPrefs() });
  },

  // 完成并提交: flush the offline queue (incl. enqueued signoff) then return home.
  async finishAndSubmit() {
    wx.showLoading({ title: '提交中…' });
    try {
      await sync.flush();
      wx.hideLoading();
      wx.showToast({ title: '已提交', icon: 'success' });
      setTimeout(() => wx.reLaunch({ url: '/pages/inspections/inspections' }), 800);
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: '提交失败，请重试', icon: 'none' });
    }
  },

  goPage(e) {
    const page = e.currentTarget.dataset.page;
    wx.navigateTo({ url: `/pages/${page}/${page}?id=${this.data.id}` });
  },
});
