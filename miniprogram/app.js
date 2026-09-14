// App entry. Attempts a silent WeChat login on launch; pages handle the
// "not yet bound" case by routing to the bind/login screen.
const auth = require('./utils/auth');

App({
  onLaunch() {
    auth.ensureSession().catch(() => {
      // Silent login failed (offline or unbound). Pages will prompt as needed.
    });
  },
  globalData: {
    userInfo: null,
  },
});
