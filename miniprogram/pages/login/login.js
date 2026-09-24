// First-launch binding, by Chinese name / phone / WeChat id / invite code:
//   1) engineer types an identifier -> lookup returns the English name(s)
//   2) engineer confirms the resolved English identity
//   3) engineer enters their password -> bind this WeChat openid to the account
//   4) invite-code accounts complete their contact details once (stage 'profile')
const auth = require('../../utils/auth');

Page({
  data: {
    stage: 'loading', // loading | name | pick | confirm | profile
    lookupMode: 'name', // name | phone | wechat | invite
    lookupLabel: '中文名',
    lookupPlaceholder: '请输入您的中文名',
    chineseName: '',
    matches: [],
    englishName: '',
    username: '',
    password: '',
    profileChineseName: '',
    profilePhone: '',
    profileWechat: '',
    loading: false,
    error: '',
  },

  onLoad() {
    // Try a silent login; if the openid is already bound, skip straight to the list.
    auth
      .seamlessLogin()
      .then((user) => (user ? this.afterAuth(user) : this.setData({ stage: 'name' })))
      .catch(() => this.setData({ stage: 'name', error: '无法连接服务器，请稍后重试' }));
  },

  onSetMode(e) {
    const mode = e.currentTarget.dataset.mode;
    const meta = {
      name: { lookupLabel: '中文名', lookupPlaceholder: '请输入您的中文名' },
      phone: { lookupLabel: '手机号', lookupPlaceholder: '请输入您的手机号' },
      wechat: { lookupLabel: '微信号', lookupPlaceholder: '请输入您的微信号' },
      invite: { lookupLabel: '邀请码', lookupPlaceholder: '请输入管理员提供的邀请码' },
    }[mode] || {};
    this.setData({ lookupMode: mode, ...meta, error: '' });
  },

  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value, error: '' });
  },

  // Resolve the identifier (name/phone/wechat/invite) to the engineer's English name.
  async onLookup() {
    const value = (this.data.chineseName || '').trim();
    if (!value) {
      this.setData({ error: `请输入${this.data.lookupLabel}` });
      return;
    }
    const payload = {
      name: { chinese_name: value },
      phone: { phone: value },
      wechat: { wechat_id: value },
      invite: { invite_code: value },
    }[this.data.lookupMode] || { chinese_name: value };
    this.setData({ loading: true, error: '' });
    try {
      const res = await auth.lookup(payload);
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
      const user = await auth.bind(this.data.username, this.data.password);
      this.afterAuth(user);
    } catch (err) {
      this.setData({ error: (err && err.data && err.data.error) || '绑定失败，请重试' });
    } finally {
      this.setData({ loading: false });
    }
  },

  // Invite-code accounts are created with no contact details, so collect them
  // once before entering the task list.
  afterAuth(user) {
    if (auth.needsProfile(user)) {
      this.setData({
        stage: 'profile',
        profileChineseName: user.chinese_name || '',
        profilePhone: user.phone_number || '',
        profileWechat: user.wechat_id || '',
        error: '',
      });
      return;
    }
    this.goList();
  },

  async onCompleteProfile() {
    const chineseName = (this.data.profileChineseName || '').trim();
    const phone = (this.data.profilePhone || '').trim();
    if (!chineseName || !phone) {
      this.setData({ error: '请填写中文名和手机号' });
      return;
    }
    this.setData({ loading: true, error: '' });
    try {
      await auth.completeProfile({
        chinese_name: chineseName,
        phone_number: phone,
        wechat_id: (this.data.profileWechat || '').trim(),
      });
      this.goList();
    } catch (err) {
      this.setData({ error: (err && err.data && err.data.error) || '保存失败，请重试' });
    } finally {
      this.setData({ loading: false });
    }
  },

  goList() {
    wx.reLaunch({ url: '/pages/inspections/inspections' });
  },
});
