'use strict';
const includeFinance = document.getElementById('include-finance');
const modeStatus = document.getElementById('mode-status');
function updateMode() {
  document.body.classList.toggle('no-finance', !includeFinance.checked);
  modeStatus.replaceChildren(document.createTextNode(includeFinance.checked ? '기업소개 · 사업 실적 포함' : '영업용 보기 · 매출 제외 (이 화면과 인쇄에만 적용)'));
  const date = document.createElement('span');
  date.textContent = '2026.09.16 기준';
  modeStatus.append(date);
  if (!includeFinance.checked && location.hash === '#performance') {
    document.getElementById('contact').scrollIntoView();
  }
}
includeFinance.addEventListener('change', updateMode);
document.getElementById('print').addEventListener('click', () => window.print());
updateMode();
