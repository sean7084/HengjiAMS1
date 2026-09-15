// Sync page: shows the offline queue and flushes it to the server.
const queue = require('../../utils/queue');
const sync = require('../../utils/sync');

Page({
  data: { items: [], syncing: false, result: null, progress: null },

  onShow() {
    this.refresh();
    // Auto-flush when the page opens and there is work pending.
    if (queue.pending().length) this.doSync();
  },

  refresh() {
    this.setData({ items: queue.readQueue() });
  },

  async doSync() {
    if (this.data.syncing) return;
    this.setData({ syncing: true, result: null, progress: null });
    try {
      const result = await sync.flush({
        onProgress: (progress) => this.setData({ progress }),
      });
      this.setData({ result });
      wx.showToast({
        title: result.remaining ? `剩余 ${result.remaining} 项` : '同步完成',
        icon: result.remaining ? 'none' : 'success',
      });
    } catch (err) {
      wx.showToast({ title: '同步失败', icon: 'none' });
    } finally {
      this.setData({ syncing: false });
      this.refresh();
    }
  },
});
