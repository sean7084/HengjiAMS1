// Simplified-Chinese labels for device capture fields (JS side).
// The .wxs module (utils/i18n.wxs) handles category/usage VALUE translation in
// WXML; this map provides the field LABELS used by form logic + rendering.
const FIELD_LABELS = {
  sn: '序列号 (SN)',
  asset_id_text: '资产编号 (Asset ID)',
  usage: '用途 (Usage)',
  category: '类别',
  brand_model: '型号',
  ip_address: 'IP 地址',
  cpu: 'CPU',
  memory: '内存',
  hdd: '硬盘',
  windows_version: 'Windows 版本',
  ios_version: 'iOS 版本',
  drive_c_free_space: 'C盘可用空间',
  intact_asset_tag: '完整标签 (Y/N)',
  comment: '备注',
  is_company_phone: '公司手机',
  user_email: '使用者邮箱 (User)',
};

module.exports = { FIELD_LABELS };
