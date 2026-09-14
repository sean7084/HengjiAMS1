// Signoff: capture store + engineer signatures on canvas, persist locally, and
// queue a 'signoff' item. Sync uploads each signature to /inspections/{id}/signoff/,
// which marks the inspection submitted on the server.
const queue = require('../../utils/queue');

Page({
  data: { id: '', storeSigned: false, engineerSigned: false },

  onLoad(query) {
    this.setData({ id: query.id });
    this.storeCtx = wx.createCanvasContext('storePad', this);
    this.engCtx = wx.createCanvasContext('engineerPad', this);
    this.lastStore = null;
    this.lastEng = null;
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
      dedupeKey: `signoff:${this.data.id}`,
    });
    wx.showToast({ title: '已保存，待同步', icon: 'success' });
    setTimeout(() => wx.navigateBack(), 700);
  },
});
