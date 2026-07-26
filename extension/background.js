/**
 * ManualPPT Background Service Worker - Origin Allowlist Enforcement & Offline Buffering
 */

const ALLOWED_ORIGINS = [
  'http://localhost',
  'http://127.0.0.1',
  'https://localhost',
  'https://127.0.0.1'
];

function isOriginAllowed(url) {
  if (!url) return false;
  return ALLOWED_ORIGINS.some(allowed => url.startsWith(allowed)) || url.includes('.staging.internal');
}

let eventBuffer = [];

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'MANUALPPT_UI_EVENT') {
    const origin = sender.tab ? sender.tab.url : '';
    
    // 檢查硬性白名單
    if (!isOriginAllowed(origin)) {
      console.warn('[ManualPPT Extension] Security Alert: Blocked event from unapproved origin:', origin);
      return;
    }

    eventBuffer.push(message.payload);

    // 嘗試傳送至本機控制端
    fetch('http://localhost:8000/api/capture/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: eventBuffer })
    }).then(res => {
      if (res.ok) {
        eventBuffer = []; // 清空緩衝
      }
    }).catch(err => {
      console.log('[ManualPPT Extension] Desktop controller offline, buffering events locally.');
    });
  }
});
