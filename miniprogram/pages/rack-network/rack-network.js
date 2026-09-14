// Rack / network / speedtest / issue photos. Each captured photo is persisted
// locally and queued (type 'photo') for offline sync to /inspections/{id}/photos/.
const queue = require('../../utils/queue');

const KINDS = [
  { kind: 'rack1', label: '机柜 Rack 1' },
  { kind: 'rack2', label: '机柜 Rack 2' },
  { kind: 'rack3', label: '机柜 Rack 3' },
  { kind: 'router', label: '路由器 Router' },
  { kind: 'switch', label: '交换机 Switch' },
  { kind: 'patchpanel', label: '配线架 Patch Panel' },
  { kind: 'speedtest_ethernet', label: '有线网速 Speedtest (Ethernet)' },
  { kind: 'speedtest_wifi', label: '无线网速 Speedtest (WiFi)' },
  { kind: 'issue', label: '问题照片 Issue' },
];

Page({
  data: { id: '', kinds: KINDS, shots: {} },

  onLoad(query) {
    this.setData({ id: query.id, shots: {} });
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

  async choose(e) {
    const kind = e.currentTarget.dataset.kind;
    try {
      const res = await new Promise((resolve, reject) =>
        wx.chooseMedia({ count: 9, mediaType: ['image'], sourceType: ['album', 'camera'], success: resolve, fail: reject })
      );
      const saved = await Promise.all(res.tempFiles.map((f) => this.saveLocal(f.tempFilePath)));
      const shots = { ...this.data.shots };
      const existing = shots[kind] || [];
      shots[kind] = existing.concat(saved.map((path) => ({ path, uid: queue.uid() })));
      this.setData({ shots });
    } catch (err) {
      // user cancelled
    }
  },

  removeShot(e) {
    const { kind, index } = e.currentTarget.dataset;
    const shots = { ...this.data.shots };
    shots[kind] = (shots[kind] || []).filter((_, i) => i !== index);
    this.setData({ shots });
  },

  save() {
    let count = 0;
    Object.keys(this.data.shots).forEach((kind) => {
      (this.data.shots[kind] || []).forEach((shot, index) => {
        queue.enqueue({
          type: 'photo',
          inspectionId: this.data.id,
          kind,
          filePath: shot.path,
          client_photo_uid: shot.uid,
          sort_index: index + 1,
          dedupeKey: `photo:${this.data.id}:${shot.uid}`,
        });
        count += 1;
      });
    });
    if (!count) {
      wx.showToast({ title: '没有待保存的照片', icon: 'none' });
      return;
    }
    this.setData({ shots: {} });
    wx.showToast({ title: `已加入 ${count} 张，待同步`, icon: 'success' });
    setTimeout(() => wx.navigateBack(), 700);
  },
});
