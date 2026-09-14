// First-launch binding: authenticate a staff account, then bind this WeChat openid.
const auth = require('../../utils/auth');

Page({
  data: { username: '', password: '', loading: false, needBind: false, error: '' },

  onLoad() {
    // Try a silent login; if the openid is already bound, skip straight to the list.
    auth
      .seamlessLogin()
      .then((user) => (user ? this.goList() : this.setData({ needBind: true })))
      .catch(() => this.setData({ needBind: true, error: '无法连接服务器，请稍后重试' }));
  },

  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value });
  },

  async onBind() {
    if (!this.data.username || !this.data.password) {
      this.setData({ error: '请输入用户名和密码' });
      return;
    }
    this.setData({ loading: true, error: '' });
    try {
      await auth.bind(this.data.username, this.data.password);
      this.goList();
    } catch (err) {
      const message = (err && err.data && err.data.error) || '绑定失败，请重试';
      this.setData({ error: message });
    } finally {
      this.setData({ loading: false });
    }
  },

  goList() {
    wx.reLaunch({ url: '/pages/inspections/inspections' });
  },
});
