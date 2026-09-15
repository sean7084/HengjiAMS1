// Confirmation page: engineer-confirmed device counts, WiFi coverage, IT-support
// rating. Saved to the offline queue as a store-level PATCH.
const db = require('../../utils/db');
const queue = require('../../utils/queue');

const RATINGS = [
  { value: 'satisfied', label: '满意' },
  { value: 'normal', label: '一般' },
  { value: 'unsatisfied', label: '不满意' },
];

Page({
  data: { id: '', countsList: [], wifiCovers: '', ratings: RATINGS, rating: '', comment: '' },

  onLoad(query) {
    const id = query.id;
    const checklist = db.getChecklist() || {};
    const inspection = db.getInspection(id) || {};
    const labels = checklist.confirmation_count_labels || [];
    const counts = inspection.device_counts || {};
    const countsList = labels.map((label) => ({
      label,
      value: counts[label] != null ? String(counts[label]) : '',
    }));
    let wifiCovers = '';
    if (inspection.wifi_covers_store === true) wifiCovers = 'yes';
    else if (inspection.wifi_covers_store === false) wifiCovers = 'no';
    this.setData({ id, countsList, wifiCovers, rating: inspection.it_support_rating || '', comment: inspection.it_support_comment || '' });
  },

  onCount(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({ [`countsList[${index}].value`]: e.detail.value });
  },
  onWifi(e) {
    this.setData({ wifiCovers: e.currentTarget.dataset.value });
  },
  onRating(e) {
    this.setData({ rating: e.currentTarget.dataset.value });
  },
  onComment(e) {
    this.setData({ comment: e.detail.value });
  },

  onSave() {
    const deviceCounts = {};
    this.data.countsList.forEach((row) => {
      if (row.value !== '') deviceCounts[row.label] = row.value;
    });
    const fields = {
      device_counts: deviceCounts,
      it_support_rating: this.data.rating,
      it_support_comment: this.data.comment,
    };
    if (this.data.wifiCovers === 'yes') fields.wifi_covers_store = true;
    else if (this.data.wifiCovers === 'no') fields.wifi_covers_store = false;

    queue.enqueue({
      type: 'inspection',
      inspectionId: this.data.id,
      dedupeKey: `inspection:${this.data.id}:confirmation`,
      fields,
    });
    wx.showToast({ title: '已保存，待同步', icon: 'success' });
    setTimeout(() => wx.navigateBack(), 600);
  },
});
