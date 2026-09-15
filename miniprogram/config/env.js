// Environment configuration.
//
// API_BASE must be an HTTPS host that is added to the WeChat MP console legal
// domains (request / uploadFile / downloadFile) for production. During local
// development you can enable "不校验合法域名" in WeChat DevTools and point at
// the Django dev server.
const ENV = 'dev'; // 'dev' | 'prod'

const CONFIGS = {
  dev: {
    API_BASE: 'http://127.0.0.1:8000/api/v1',
  },
  prod: {
    // TODO: replace with your production HTTPS API host before release.
    API_BASE: 'https://your-domain.example.com/api/v1',
  },
};

module.exports = {
  ENV,
  API_BASE: CONFIGS[ENV].API_BASE,
};
