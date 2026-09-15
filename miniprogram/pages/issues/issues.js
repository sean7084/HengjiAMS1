// Issue list (cover_page). New issues are queued offline; existing issues load
// from cache and refresh when online.
const db = require('../../utils/db');
const queue = require('../../utils/queue');
const request = require('../../utils/request');

const STATUSES = [
  { value: 'to_be_followed', label: '待跟进' },
  { value: 'fixed', label: '已修正' },
];

Page({
  data: { id: '', issues: [], description: '', status: 'to_be_followed', statuses: STATUSES },

  onLoad(query) {
    this.setData({ id: query.id });
    this.load();
  },

  async load() {
    const inspection = db.getInspection(this.data.id) || {};
    this.setData({ issues: inspection.issues || [] });
    try {
      const data = await request.request(`/inspections/${this.data.id}/issues/`);
      this.setData({ issues: data });
    } catch (err) {
      // offline: keep cached issues
    }
  },

  onDesc(e) {
    this.setData({ description: e.detail.value });
  },
  onStatus(e) {
    this.setData({ status: e.currentTarget.dataset.value });
  },

  addIssue() {
    const description = (this.data.description || '').trim();
    if (!description) {
      wx.showToast({ title: '请输入问题描述', icon: 'none' });
      return;
    }
    const seq = this.data.issues.length + 1;
    const fields = { seq, description, status: this.data.status };
    queue.enqueue({
      type: 'issue',
      inspectionId: this.data.id,
      dedupeKey: `issue:${this.data.id}:${queue.uid()}`,
      fields,
    });
    this.setData({ description: '', issues: this.data.issues.concat([{ ...fields, pending: true }]) });
    wx.showToast({ title: '已加入同步队列', icon: 'success' });
  },
});
