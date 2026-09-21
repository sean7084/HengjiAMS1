// First-launch binding, by Chinese name:
//   1) engineer types their Chinese name -> lookup returns the English name(s)
//   2) engineer confirms the resolved English identity
//   3) engineer enters their password -> bind this WeChat openid to the account
const auth = require('../../utils/auth');

Page({
  data: {
    stage: 'loading', // loading | name | pick | confirm
    chineseName: '',
    matches: [],
    englishName: '',
    username: '',
    password: '',
    loading: false,
    error: '',
  },

  onLoad() {
    // Try a silent login; if the openid is already bound, skip straight to the list.
    auth
      .seamlessLogin()
      .then((user) => (user ? this.goList() : this.setData({ stage: 'name' })))
      .catch(() => this.setData({ stage: 'name', error: '无法连接服务器，请稍后重试' }));
  },

  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value, error: '' });
  },

  // Resolve the Chinese name to the engineer's English name for confirmation.
  async onLookup() {
    const name = (this.data.chineseName || '').trim();
    if (!name) {
      this.setData({ error: '请输入中文名' });
      return;
    }
    this.setData({ loading: true, error: '' });
    try {
      const res = await auth.lookupByName(name);
      const matches = (res && res.matches) || [];
      if (!matches.length) {
        this.setData({ error: '未找到该中文名，请联系管理员录入' });
        return;
      }
      if (matches.length === 1) {
        this.setData({
          englishName: matches[0].english_name,
          username: matches[0].username,
          stage: 'confirm',
        });
      } else {
        this.setData({ matches, stage: 'pick' });
      }
    } catch (err) {
      this.setData({ error: (err && err.data && err.data.error) || '查询失败，请重试' });
    } finally {
      this.setData({ loading: false });
    }
  },

  onPickMatch(e) {
    const m = this.data.matches[e.currentTarget.dataset.index];
    if (m) {
      this.setData({ englishName: m.english_name, username: m.username, stage: 'confirm', error: '' });
    }
  },

  onBackToName() {
    this.setData({ stage: 'name', password: '', error: '' });
  },

  async onBind() {
    if (!this.data.password) {
      this.setData({ error: '请输入密码' });
      return;
    }
    this.setData({ loading: true, error: '' });
    try {
      await auth.bind(this.data.username, this.data.password);
      this.goList();
    } catch (err) {
      this.setData({ error: (err && err.data && err.data.error) || '绑定失败，请重试' });
    } finally {
      this.setData({ loading: false });
    }
  },

  goList() {
    wx.reLaunch({ url: '/pages/inspections/inspections' });
  },
});
