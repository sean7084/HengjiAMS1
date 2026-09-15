// JWT-aware network layer.
//
// - Injects `Authorization: Bearer <access>` on every authenticated call.
// - On 401, attempts a token refresh once and retries; clears the session if the
//   refresh fails so the page can route to bind/login.
// - Network failures throw an error flagged `networkError` so the offline queue
//   can keep the item pending instead of dropping it.
const env = require('../config/env');

const TOKEN_KEY = 'mp_access_token';
const REFRESH_KEY = 'mp_refresh_token';

function getAccess() {
  return wx.getStorageSync(TOKEN_KEY) || '';
}
function getRefresh() {
  return wx.getStorageSync(REFRESH_KEY) || '';
}
function setTokens(access, refresh) {
  if (access) wx.setStorageSync(TOKEN_KEY, access);
  if (refresh) wx.setStorageSync(REFRESH_KEY, refresh);
}
function clearTokens() {
  wx.removeStorageSync(TOKEN_KEY);
  wx.removeStorageSync(REFRESH_KEY);
}

function rawRequest(options) {
  return new Promise((resolve, reject) => {
    wx.request({
      ...options,
      success: resolve,
      fail: reject,
    });
  });
}

async function refreshAccessToken() {
  const refresh = getRefresh();
  if (!refresh) return false;
  try {
    const res = await rawRequest({
      url: `${env.API_BASE}/auth/token/refresh/`,
      method: 'POST',
      data: { refresh },
      header: { 'Content-Type': 'application/json' },
    });
    if (res.statusCode === 200 && res.data && res.data.access) {
      setTokens(res.data.access);
      return true;
    }
  } catch (e) {
    // fall through to failure
  }
  return false;
}

async function request(path, options = {}) {
  const { method = 'GET', data = {}, header = {}, auth = true, retry = true } = options;
  const url = path.startsWith('http') ? path : `${env.API_BASE}${path}`;
  const headers = { 'Content-Type': 'application/json', ...header };
  if (auth) {
    const token = getAccess();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let res;
  try {
    res = await rawRequest({ url, method, data, header: headers });
  } catch (err) {
    throw Object.assign(new Error('NETWORK_ERROR'), { networkError: true, cause: err });
  }

  if (res.statusCode === 401 && auth && retry) {
    const ok = await refreshAccessToken();
    if (ok) return request(path, { method, data, header, auth, retry: false });
    clearTokens();
    throw Object.assign(new Error('UNAUTHORIZED'), { statusCode: 401, data: res.data });
  }
  if (res.statusCode >= 200 && res.statusCode < 300) return res.data;
  throw Object.assign(new Error(`HTTP_${res.statusCode}`), { statusCode: res.statusCode, data: res.data });
}

// Multipart upload (photos/signatures). wx.uploadFile attaches a single file per
// call, so multi-file submissions are performed as sequential calls by the caller.
function uploadFile(path, filePath, name, formData = {}, auth = true) {
  return new Promise((resolve, reject) => {
    const header = {};
    const token = getAccess();
    if (auth && token) header.Authorization = `Bearer ${token}`;
    wx.uploadFile({
      url: `${env.API_BASE}${path}`,
      filePath,
      name,
      formData,
      header,
      success: (res) => {
        let data = res.data;
        try {
          data = JSON.parse(res.data);
        } catch (e) {
          // keep raw text
        }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(data);
        else reject(Object.assign(new Error(`HTTP_${res.statusCode}`), { statusCode: res.statusCode, data }));
      },
      fail: (err) => reject(Object.assign(new Error('NETWORK_ERROR'), { networkError: true, cause: err })),
    });
  });
}

module.exports = {
  request,
  uploadFile,
  getAccess,
  getRefresh,
  setTokens,
  clearTokens,
  refreshAccessToken,
};
