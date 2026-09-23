// Global floating home button: returns the engineer to the inspections list.
Component({
  methods: {
    goHome() {
      wx.reLaunch({ url: '/pages/inspections/inspections' });
    },
  },
});
