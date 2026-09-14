// Report generation + download. Requires connectivity (server-side rendering).
const request = require('../../utils/request');

Page({
  data: { id: '', generating: false, reportUrl: '', photoZipUrl: '', generatedAt: '' },

  onLoad(query) {
    this.setData({ id: query.id });
  },

  async generate() {
    if (this.data.generating) return;
    this.setData({ generating: true });
    wx.showLoading({ title: '生成中…' });
    try {
      const data = await request.request(`/inspections/${this.data.id}/report/`, { method: 'POST' });
      this.setData({
        reportUrl: data.report_file || '',
        photoZipUrl: data.photo_zip || '',
        generatedAt: data.report_generated_at || '',
      });
      wx.hideLoading();
      wx.showToast({ title: '报告已生成', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: '生成失败（需联网）', icon: 'none' });
    } finally {
      this.setData({ generating: false });
    }
  },

  openReport() {
    this.download(this.data.reportUrl, 'xlsx');
  },
  openZip() {
    this.download(this.data.photoZipUrl, 'zip');
  },

  download(url, fileType) {
    if (!url) {
      wx.showToast({ title: '请先生成报告', icon: 'none' });
      return;
    }
    wx.showLoading({ title: '下载中…' });
    wx.downloadFile({
      url,
      success: (res) => {
        wx.hideLoading();
        wx.openDocument({
          filePath: res.tempFilePath,
          fileType,
          showMenu: true,
          fail: () => wx.showToast({ title: '无法打开该文件类型', icon: 'none' }),
        });
      },
      fail: () => {
        wx.hideLoading();
        wx.showToast({ title: '下载失败', icon: 'none' });
      },
    });
  },

  // Share the generated workbook to a WeChat chat (download then shareFileMessage).
  shareReport() {
    if (!this.data.reportUrl) {
      wx.showToast({ title: '请先生成报告', icon: 'none' });
      return;
    }
    wx.showLoading({ title: '下载中…' });
    wx.downloadFile({
      url: this.data.reportUrl,
      success: (res) => {
        wx.hideLoading();
        wx.shareFileMessage({
          filePath: res.tempFilePath,
          fileName: '巡检报告.xlsx',
          fail: () => wx.showToast({ title: '分享已取消', icon: 'none' }),
        });
      },
      fail: () => {
        wx.hideLoading();
        wx.showToast({ title: '下载失败', icon: 'none' });
      },
    });
  },

  onShareAppMessage() {
    return { title: 'Kering 店铺巡检报告', path: `/pages/report/report?id=${this.data.id}` };
  },
});
