// Signoff: capture store + engineer signatures on canvas, persist locally, and
// queue a 'signoff' item. Sync uploads each signature to /inspections/{id}/signoff/,
// which marks the inspection submitted on the server.
const queue = require('../../utils/queue');
const db = require('../../utils/db');
const request = require('../../utils/request');

Page({
  data: {
    id: '', storeSigned: false, engineerSigned: false,
    categoryCounts: [], itRating: '', wifiBadge: '',
  },

  onLoad(query) {
    this.setData({ id: query.id });
    this.storeCtx = wx.createCanvasContext('storePad', this);
    this.engCtx = wx.createCanvasContext('engineerPad', this);
    this.lastStore = null;
    this.lastEng = null;
    this.loadSummary();
  },

  // Merged confirmation summary: device counts per category, IT rating, and an
  // auto-derived WiFi good/bad badge (from recorded weak points).
  async loadSummary() {
    let inspection = db.getInspection(this.data.id);
    if (!inspection) {
      try { inspection = await request.request(`/inspections/${this.data.id}/`); } catch (e) { inspection = null; }
    }
    if (!inspection) return;
    const devices = (inspection.devices || []).filter((d) => d.collected_at);
    const byCat = {};
    devices.forEach((d) => { byCat[d.category || '其他'] = (byCat[d.category || '其他'] || 0) + 1; });
    const categoryCounts = Object.keys(byCat).map((k) => ({ category: k, count: byCat[k] }));
    const weak = (inspection.wifi_weak_points || []).length;
    const wifiBadge = inspection.wifi_coverage === 'weak' || weak > 0 ? 'bad' : 'good';
    this.setData({ categoryCounts, itRating: inspection.it_support_rating || '', wifiBadge });
  },

  setItRating(e) {
    this.setData({ itRating: e.currentTarget.dataset.value });
  },

  saveLocal(tempPath) {
    return new Promise((resolve) => {
      wx.getFileSystemManager().saveFile({
        tempFilePath: tempPath,
        success: (s) => resolve(s.savedFilePath),
        fail: () => resolve(tempPath),
      });
    });
  },

  exportPad(canvasId) {
    return new Promise((resolve) => {
      wx.canvasToTempFilePath({ canvasId, fileType: 'png', success: (r) => resolve(r.tempFilePath), fail: () => resolve('') }, this);
    });
  },

  storeStart(e) {
    const t = e.touches[0];
    this.lastStore = { x: t.x, y: t.y };
  },
  storeMove(e) {
    const t = e.touches[0];
    if (!this.lastStore) return;
    this.storeCtx.setStrokeStyle('#111111');
    this.storeCtx.setLineWidth(3);
    this.storeCtx.beginPath();
    this.storeCtx.moveTo(this.lastStore.x, this.lastStore.y);
    this.storeCtx.lineTo(t.x, t.y);
    this.storeCtx.stroke();
    this.storeCtx.draw(true);
    this.lastStore = { x: t.x, y: t.y };
    if (!this.data.storeSigned) this.setData({ storeSigned: true });
  },

  engStart(e) {
    const t = e.touches[0];
    this.lastEng = { x: t.x, y: t.y };
  },
  engMove(e) {
    const t = e.touches[0];
    if (!this.lastEng) return;
    this.engCtx.setStrokeStyle('#111111');
    this.engCtx.setLineWidth(3);
    this.engCtx.beginPath();
    this.engCtx.moveTo(this.lastEng.x, this.lastEng.y);
    this.engCtx.lineTo(t.x, t.y);
    this.engCtx.stroke();
    this.engCtx.draw(true);
    this.lastEng = { x: t.x, y: t.y };
    if (!this.data.engineerSigned) this.setData({ engineerSigned: true });
  },

  clearStore() {
    this.storeCtx.clearRect(0, 0, 1000, 400);
    this.storeCtx.draw();
    this.setData({ storeSigned: false });
  },
  clearEng() {
    this.engCtx.clearRect(0, 0, 1000, 400);
    this.engCtx.draw();
    this.setData({ engineerSigned: false });
  },

  async save() {
    const signatures = [];
    if (this.data.storeSigned) {
      const path = await this.exportPad('storePad');
      if (path) signatures.push({ part: 'store_signature', filePath: await this.saveLocal(path) });
    }
    if (this.data.engineerSigned) {
      const path = await this.exportPad('engineerPad');
      if (path) signatures.push({ part: 'engineer_signature', filePath: await this.saveLocal(path) });
    }
    if (!signatures.length) {
      wx.showToast({ title: '请至少完成一项签名', icon: 'none' });
      return;
    }
    queue.enqueue({
      type: 'signoff',
      inspectionId: this.data.id,
      signatures,
      fields: {
        it_support_rating: this.data.itRating || undefined,
        device_counts: this.data.categoryCounts.reduce((acc, c) => { acc[c.category] = c.count; return acc; }, {}),
        wifi_coverage: this.data.wifiBadge === 'bad' ? 'weak' : 'good',
      },
      dedupeKey: `signoff:${this.data.id}`,
    });
    wx.showToast({ title: '已保存，待同步', icon: 'success' });
    setTimeout(() => wx.navigateBack(), 700);
  },
});
