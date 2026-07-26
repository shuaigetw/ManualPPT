/**
 * ManualPPT Content Script - Semantic DOM & UI Event Capture with Source Masking
 */

const SENSITIVE_TYPES = ['password', 'card', 'cvv', 'ssn'];
const SENSITIVE_PATTERNS = [/password/i, /secret/i, /salary/i, /token/i, /mfa/i];

function isElementSensitive(el) {
  if (!el) return false;
  if (el.type && SENSITIVE_TYPES.includes(el.type.toLowerCase())) return true;
  const nameOrId = (el.name || '') + ' ' + (el.id || '') + ' ' + (el.getAttribute('aria-label') || '');
  return SENSITIVE_PATTERNS.some(pat => pat.test(nameOrId));
}

function extractSemanticTarget(el) {
  if (!el) return null;
  const role = el.getAttribute('role') || el.tagName.toLowerCase();
  const name = el.getAttribute('aria-label') || el.innerText || el.value || el.name || '';
  const testId = el.getAttribute('data-testid') || el.getAttribute('data-test');
  
  const locators = [];
  if (el.id) locators.push(`#${el.id}`);
  if (testId) locators.push(`[data-testid="${testId}"]`);
  if (el.className) locators.push(`.${el.className.split(' ').join('.')}`);

  const rect = el.getBoundingClientRect();

  return {
    role: role,
    name: isElementSensitive(el) ? '***MASKED***' : name.substring(0, 100),
    test_id: testId || null,
    candidate_locators: locators,
    bounding_box: {
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height
    }
  };
}

// 監聽有語意之 click 事件
document.addEventListener('click', (event) => {
  const target = event.target;
  const semanticTarget = extractSemanticTarget(target);
  
  const eventPayload = {
    action_type: 'CLICK',
    target: semanticTarget,
    value: isElementSensitive(target) ? '***MASKED***' : (target.value || null),
    timestamp: new Date().toISOString()
  };

  chrome.runtime.sendMessage({ type: 'MANUALPPT_UI_EVENT', payload: eventPayload });
}, true);

// 監聽 input 事件 (具遮罩)
document.addEventListener('input', (event) => {
  const target = event.target;
  const semanticTarget = extractSemanticTarget(target);
  
  const eventPayload = {
    action_type: 'INPUT_TEXT',
    target: semanticTarget,
    value: isElementSensitive(target) ? '***MASKED***' : target.value,
    timestamp: new Date().toISOString()
  };

  chrome.runtime.sendMessage({ type: 'MANUALPPT_UI_EVENT', payload: eventPayload });
}, true);
