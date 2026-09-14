// Device verification: category-driven capture fields + photos, saved to the
// offline queue (idempotent per client_device_uid) for later sync.
const db = require('../../utils/db');
const queue = require('../../utils/queue');

const FIELD_LABELS = {
  ip_address: 'IP 地址',
  cpu: 'CPU',
  memory: '内存',
  hdd: '硬盘',
  windows_version: '系统版本 (Windows)',
  ios_version: '系统版本 (iOS)',
  drive_c_free_space: 'C盘可用空间',
  intact_asset_tag: '完整标签 (Y/N)',
  comment: '备注 Comment',
};

Page({
  data: {
    id: '',
    uid: '',
    isNew: false,
    device: {},
    fields: {},
    captureFields: [],
    fieldLabels: FIELD_LABELS,
    overallPhoto: '',
    serialPhoto: '',
    status: 'in_store',
  },

  onLoad(query) {
    const id = query.id;
    const cached = db.getInspection(id);
    const checklist = db.getChecklist() || {};
    const captureMap = checklist.capture_fields || {};
    let device = {};
    let uid = query.uid || '';
    const isNew = query.new === '1';

    if (isNew) {
      uid = uid || `new-${queue.uid()}`;
      device = {
        client_device_uid: uid,
        sn: query.sn ? decodeURIComponent(query.sn) : '',
        is_new_device: true,
        category: '',
        brand_model: '',
        status: 'in_store',
      };
    } else if (cached) {
      device = (cached.devices || []).find((d) => d.client_device_uid === query.uid) || {};
      uid = device.client_device_uid || uid;
    }

    const captureFields =
      captureMap[device.category] ||
      checklist.default_capture_fields || ['intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'];

    const fields = {};
    captureFields.forEach((f) => {
      if (FIELD_LABELS[f]) fields[f] = device[f] || '';
    });

    this.setData({ id, uid, isNew, device, fields, captureFields, status: device.status || 'in_store' });
  },

  onField(e) {
    const key = e.currentTarget.dataset.field;
    this.setData({ [`fields.${key}`]: e.detail.value });
  },

  onIdentity(e) {
    const key = e.currentTarget.dataset.field;
    this.setData({ [`device.${key}`]: e.detail.value });
  },

  onStatus(e) {
    this.setData({ status: e.currentTarget.dataset.status });
  },

  choosePhoto(e) {
    const part = e.currentTarget.dataset.part; // overall_photo | serial_photo
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempPath = res.tempFiles[0].tempFilePath;
        // Persist the file so it survives until sync (offline safety).
        const fsm = wx.getFileSystemManager();
        fsm.saveFile({
          tempFilePath: tempPath,
          success: (s) => this.setData({ [part]: s.savedFilePath }),
          fail: () => this.setData({ [part]: tempPath }),
        });
      },
    });
  },

  onSave() {
    const photos = [];
    if (this.data.overallPhoto) {
      photos.push({ part: 'overall_photo', kind: 'overall', filePath: this.data.overallPhoto, uid: queue.uid(), index: 1 });
    }
    if (this.data.serialPhoto) {
      photos.push({ part: 'serial_photo', kind: 'serial', filePath: this.data.serialPhoto, uid: queue.uid(), index: 2 });
    }

    const fields = { ...this.data.fields, status: this.data.status };
    if (this.data.isNew) {
      fields.category = this.data.device.category || '';
      fields.brand_model = this.data.device.brand_model || '';
      fields.sn = this.data.device.sn || '';
      fields.asset_id_text = this.data.device.asset_id_text || '';
      fields.usage = this.data.device.usage || '';
      fields.is_new_device = true;
    }

    queue.enqueue({
      type: 'device',
      inspectionId: this.data.id,
      client_device_uid: this.data.uid,
      dedupeKey: `device:${this.data.id}:${this.data.uid}`,
      fields,
      photos,
    });

    wx.showToast({ title: '已保存，待同步', icon: 'success' });
    setTimeout(() => wx.navigateBack(), 600);
  },
});
