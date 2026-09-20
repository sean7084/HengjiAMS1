// Authentication: WeChat seamless login + first-launch binding to a staff account.
const request = require('./request');

const USER_KEY = 'mp_user';

function getUser() {
  return wx.getStorageSync(USER_KEY) || null;
}
function setUser(user) {
  if (user) wx.setStorageSync(USER_KEY, user);
}
function clearSession() {
  request.clearTokens();
  wx.removeStorageSync(USER_KEY);
}

function wxLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => (res.code ? resolve(res.code) : reject(new Error('NO_CODE'))),
      fail: reject,
    });
  });
}

// Returns the user when the openid is already bound, or null when the client
// should show the bind screen.
async function seamlessLogin() {
  const code = await wxLoginCode();
  const data = await request.request('/auth/wechat/login/', {
    method: 'POST',
    data: { code },
    auth: false,
  });
  if (data && data.bound) {
    request.setTokens(data.access, data.refresh);
    setUser(data.user);
    return data.user;
  }
  return null;
}

// Resolve a Chinese name to matching engineer(s) for the login confirmation step.
// Returns {found, matches:[{username, english_name, chinese_name}]}.
async function lookupByName(chineseName) {
  return request.request('/auth/wechat/lookup/', {
    method: 'POST',
    data: { chinese_name: chineseName },
    auth: false,
  });
}

// First launch: authenticate with staff username/password + wx.login code, bind
// the openid, and store the issued tokens.
async function bind(username, password) {
  const code = await wxLoginCode();
  const data = await request.request('/auth/wechat/bind/', {
    method: 'POST',
    data: { code, username, password },
    auth: false,
  });
  request.setTokens(data.access, data.refresh);
  setUser(data.user);
  return data.user;
}

// Reuse a cached session when present, otherwise try a silent WeChat login.
async function ensureSession() {
  if (request.getAccess() && getUser()) return getUser();
  return seamlessLogin();
}

module.exports = { getUser, setUser, clearSession, seamlessLogin, lookupByName, bind, ensureSession };
