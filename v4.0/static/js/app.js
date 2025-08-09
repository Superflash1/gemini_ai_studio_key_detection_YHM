// 轻量提示（生产版）：透明背景的右上角提醒
(function initInlineAlert(){
  function ensureContainer(){
    let c = document.getElementById('alert-container');
    if (!c){
      c = document.createElement('div');
      c.id = 'alert-container';
      c.style.cssText = 'position:fixed;top:70px;right:20px;z-index:1050;max-width:420px;';
      document.body.appendChild(c);
    }
    return c;
  }
  function cls(type){
    const map={ success:'alert-success', danger:'alert-danger', error:'alert-danger', warning:'alert-warning', info:'alert-info', primary:'alert-primary'};
    return map[type]||'alert-info';
  }
  window.showAlert = function(message, type='info'){
    const container = ensureContainer();
    const div = document.createElement('div');
    div.className = `alert ${cls(type)} alert-dismissible fade show`;
    div.style.cssText = 'margin-bottom:10px;padding:12px 16px;border-radius:10px;border:1px solid rgba(0,0,0,.06);box-shadow:0 6px 14px rgba(17,24,39,.08)';
    div.innerHTML = `${message}<button type="button" class="btn-close" aria-label="Close"></button>`;
    div.querySelector('.btn-close').onclick = ()=> div.remove();
    container.appendChild(div);
    setTimeout(()=>{ if(div.parentNode) div.remove(); }, 3000);
  }
})();

// 应用主脚本（重构）
(function() {
  let eventSource = null;
  let logContainer = null;
  let isCheckingGlobal = false;
  let settingsModal = null;

  function qs(id) { return document.getElementById(id); }

  function init() {
    logContainer = qs('logContainer');
    const modalEl = qs('settingsModal');
    if (modalEl && window.bootstrap) {
      settingsModal = new bootstrap.Modal(modalEl);
    }

    // 绑定按钮
    bindActions();

    // 初始化数据
    initEventSource();
    refreshKeyList();
    updateStats();
    checkStatus();

    // 定时器
    setInterval(refreshKeyList, 10000);
    setInterval(updateStats, 10000);
    setInterval(checkStatus, 2000);
  }

  function bindActions() {
    const addForm = qs('addKeyForm');
    if (addForm) addForm.addEventListener('submit', addKeys);

    const saveBtn = qs('action-save-settings');
    if (saveBtn) saveBtn.addEventListener('click', saveSettings);

    const openSettings = qs('action-open-settings');
    if (openSettings) openSettings.addEventListener('click', () => settingsModal && settingsModal.show());

    const btnCheckAll = qs('action-check-all');
    if (btnCheckAll) btnCheckAll.addEventListener('click', () => checkAllKeys(false));

    const btnCheckPending = qs('action-check-pending');
    if (btnCheckPending) btnCheckPending.addEventListener('click', checkPendingKeys);

    const btnForce = qs('action-force-check');
    if (btnForce) btnForce.addEventListener('click', () => checkAllKeys(true));

    const btnStop = qs('action-stop');
    if (btnStop) btnStop.addEventListener('click', stopChecking);

    const btnCopyLines = qs('action-copy-valid-lines');
    if (btnCopyLines) btnCopyLines.addEventListener('click', () => copyValidKeys('lines'));

    const btnCopyComma = qs('action-copy-valid-comma');
    if (btnCopyComma) btnCopyComma.addEventListener('click', () => copyValidKeys('comma'));

    const btnDeleteInvalid = qs('action-delete-invalid');
    if (btnDeleteInvalid) btnDeleteInvalid.addEventListener('click', deleteInvalidKeys);

    const btnClearLogs = qs('action-clear-logs');
    if (btnClearLogs) btnClearLogs.addEventListener('click', clearLogs);

    const btnScrollBottom = qs('action-scroll-bottom');
    if (btnScrollBottom) btnScrollBottom.addEventListener('click', scrollToBottom);

    // 设置表单内动态显示
    const useProxyCheckbox = qs('useProxy');
    const proxyUrlContainer = qs('proxyUrlContainer');
    if (useProxyCheckbox && proxyUrlContainer) {
      const updateProxyVisibility = () => {
        proxyUrlContainer.style.display = 'block';
        const input = qs('proxyUrl');
        if (!input) return;
        if (useProxyCheckbox.checked) {
          proxyUrlContainer.style.opacity = '1';
          input.disabled = false;
        } else {
          proxyUrlContainer.style.opacity = '0.5';
          input.disabled = true;
        }
      };
      useProxyCheckbox.addEventListener('change', updateProxyVisibility);
      updateProxyVisibility();
    }

    const emailEnabledCheckbox = qs('emailEnabled');
    const emailConfigContainer = qs('emailConfigContainer');
    if (emailEnabledCheckbox && emailConfigContainer) {
      const updateEmailVisibility = () => {
        const emailInputs = document.querySelectorAll('.email-input');
        emailConfigContainer.style.display = 'block';
        if (emailEnabledCheckbox.checked) {
          emailConfigContainer.style.opacity = '1';
          emailInputs.forEach(i => i.disabled = false);
          const pwd = qs('emailPassword'); if (pwd) pwd.disabled = false;
        } else {
          emailConfigContainer.style.opacity = '0.5';
          emailInputs.forEach(i => i.disabled = true);
          const pwd = qs('emailPassword'); if (pwd) pwd.disabled = true;
        }
      };
      emailEnabledCheckbox.addEventListener('change', updateEmailVisibility);
      updateEmailVisibility();

      // 邮箱数量徽章
      updateEmailCount();
      document.querySelectorAll('.email-input').forEach(input => {
        input.addEventListener('input', updateEmailCount);
      });
    }

    // 暴露部分函数到 window，供按钮内联调用
    window.refreshKeyList = refreshKeyList;
    window.updateStats = updateStats;
    window.checkAllKeys = checkAllKeys;
    window.stopChecking = stopChecking;
    window.copyValidKeys = copyValidKeys;
    window.sendTestEmail = sendTestEmail;
  }

  // SSE
  function initEventSource() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource('/logs');
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (!data.heartbeat) addLogEntry(data);
      } catch (e) {
        console.error('解析日志数据失败:', e, event.data);
      }
    };
    eventSource.onopen = () => {
      qs('statusText').textContent = '系统运行中 - 日志流已连接';
      const ls = qs('logStatus'); if (ls) { ls.textContent = '已连接'; ls.className = 'text-success'; }
    };
    eventSource.onerror = () => {
      qs('statusText').textContent = '系统运行中 - 日志流连接中断';
      const ls = qs('logStatus'); if (ls) { ls.textContent = '重连中...'; ls.className = 'text-warning'; }
      eventSource.close();
      setTimeout(initEventSource, 5000);
    };
  }

  function addLogEntry(logData) {
    if (!logContainer) return;
    if (logData.is_update && logData.update_id) {
      return updateLogEntry(logData);
    }
    const logDiv = document.createElement('div');
    logDiv.className = 'log-entry';
    let levelClass = 'log-info';
    if (logData.level === 'ERROR') levelClass = 'log-error';
    else if (logData.message.includes('✅')) levelClass = 'log-success';
    else if (logData.message.includes('📊 进度:')) levelClass = 'log-progress';
    logDiv.innerHTML = `<span class="text-muted">[${logData.timestamp}]</span> <span class="${levelClass}">${escapeHtml(logData.message)}</span>`;
    logContainer.appendChild(logDiv);
    logContainer.scrollTop = logContainer.scrollHeight;
    if (/(检测|📊 进度:|🎉)/.test(logData.message)) setTimeout(updateStats, 500);
    while (logContainer.children.length > 1000) logContainer.removeChild(logContainer.firstChild);
  }

  function updateLogEntry(logData) {
    const existing = document.querySelector(`[data-update-id="${logData.update_id}"]`);
    let levelClass = 'log-progress';
    const html = `<span class="text-muted">[${logData.timestamp}]</span> <span class="${levelClass}">${escapeHtml(logData.message)}</span>`;
    if (existing) {
      existing.innerHTML = html;
      setTimeout(updateStats, 500);
    } else if (logContainer) {
      const logDiv = document.createElement('div');
      logDiv.className = 'log-entry';
      logDiv.setAttribute('data-update-id', logData.update_id);
      logDiv.innerHTML = html;
      logContainer.appendChild(logDiv);
      logContainer.scrollTop = logContainer.scrollHeight;
      setTimeout(updateStats, 500);
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text; return div.innerHTML;
  }

  function clearLogs() { if (logContainer) logContainer.innerHTML = ''; }
  function scrollToBottom() { if (logContainer) logContainer.scrollTop = logContainer.scrollHeight; }

  // 业务操作
  async function addKeys(event) {
    event.preventDefault();
    const textarea = document.getElementById('newKeys');
    const keysText = (textarea.value || '').trim();
    if (!keysText) { showAlert('请输入至少一个密钥','warning'); return; }
    try {
      const res = await fetch('/api/keys', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ keys: keysText })});
      const result = await res.json();
      if (result.success) {
        textarea.value = '';
        setTimeout(() => { refreshKeyList(); updateStats(); }, 1000);
        addLogEntry({ timestamp: new Date().toLocaleString(), level: 'INFO', message: `✅ 已添加 ${result.added_count} 个密钥，${result.duplicate_count} 个重复，开始检测...` });
      } else { showAlert('添加失败: ' + result.message, 'danger'); }
    } catch (e) { showAlert('添加失败: ' + e.message, 'danger'); }
  }

  async function deleteInvalidKeys() {
    const invalidCount = parseInt(qs('invalidCount')?.textContent || '0');
    if (!invalidCount) { showAlert('没有无效密钥需要删除','info'); return; }
    if (!confirm(`确定要删除所有 ${invalidCount} 个无效密钥吗？此操作不可撤销。`)) return;
    try {
      const res = await fetch('/api/keys/delete-invalid', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      const result = await res.json();
      if (result.success) { refreshKeyList(); updateStats(); showAlert(result.message,'success'); }
      else { showAlert('删除失败: ' + result.message,'danger'); }
    } catch (e) { showAlert('删除失败: ' + e.message,'danger'); }
  }

  async function saveSettings() {
    const intervalMinutes = parseInt(qs('intervalMinutes').value);
    const apiUrl = qs('apiUrl').value.trim();
    const useProxy = qs('useProxy').checked;
    const proxyUrl = qs('proxyUrl').value;
    const concurrency = parseInt(qs('concurrency').value);
    const checkStrategy = qs('checkStrategy').value;
    const emailEnabled = qs('emailEnabled').checked;
    const email1 = qs('email1').value.trim();
    const email2 = qs('email2').value.trim();
    const email3 = qs('email3').value.trim();
    const emailPassword = qs('emailPassword').value;
    if (concurrency < 1) { showAlert('并发数必须 ≥ 1','warning'); return; }
    try {
      const res = await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ check_interval: intervalMinutes, api_url: apiUrl, use_proxy: useProxy ? 'true':'false', proxy_url: proxyUrl, concurrency, check_strategy: checkStrategy, email_enabled: emailEnabled ? 'true':'false', email1, email2, email3, email_password: emailPassword })});
      const result = await res.json();
      if (result.success) {
        showAlert('设置已保存','success');
        settingsModal && settingsModal.hide();
        addLogEntry({ timestamp: new Date().toLocaleString(), level: 'INFO', message: `⚙️ 设置已更新 - 间隔: ${intervalMinutes} 分钟, 并发: ${concurrency}, 策略: ${checkStrategy}, 代理: ${useProxy ? proxyUrl : '禁用'}` });
      } else { showAlert('保存失败: ' + result.message,'danger'); }
    } catch (e) { showAlert('保存失败: ' + e.message,'danger'); }
  }

  function checkAllKeys(forceAll=false) {
    if (isCheckingGlobal) { showAlert('检测被跳过：另一个检测进程正在运行中', 'warning'); return; }
    fetch('/api/check-all', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ force_all: forceAll })})
      .then(r => r.json()).then(data => {
        if (data.success) { showAlert(data.message, 'success'); setTimeout(checkStatus, 100); }
        else { showAlert(data.message, data.is_checking ? 'warning':'danger'); }
      }).catch(() => showAlert('检测请求失败', 'danger'));
  }

  function checkPendingKeys() {
    if (isCheckingGlobal) { showAlert('检测被跳过：另一个检测进程正在运行中', 'warning'); return; }
    fetch('/api/check-pending', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then(r => r.json()).then(data => {
        if (data.success) { showAlert(data.message, 'success'); setTimeout(checkStatus, 100); }
        else { showAlert(data.message, data.is_checking ? 'warning':'danger'); }
      }).catch(() => showAlert('检测请求失败', 'danger'));
  }

  function checkSingleKey(keyValue) {
    if (isCheckingGlobal) { showAlert('检测被跳过：另一个检测进程正在运行中', 'warning'); return; }
    fetch('/api/check-single', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: keyValue }) })
      .then(r => r.json()).then(data => {
        if (data.success) { showAlert(data.message, 'success'); setTimeout(checkStatus, 100); }
        else { showAlert(data.message, data.is_checking ? 'warning':'danger'); }
      }).catch(() => showAlert('检测请求失败', 'danger'));
  }

  async function refreshKeyList() {
    try {
      const res = await fetch('/api/keys');
      const keys = await res.json();
      const tbody = qs('keyTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';
      keys.forEach(key => {
        const tr = document.createElement('tr');
        let badge = '<span class="badge bg-secondary status-badge">未知</span>';
        if (key.status === 'valid') badge = '<span class="badge bg-success status-badge">有效</span>'; else if (key.status === 'invalid') badge = '<span class="badge bg-danger status-badge">无效</span>'; else if (key.status === 'pending') badge = '<span class="badge bg-warning status-badge">待检测</span>';
        const lastChecked = key.last_checked ? new Date(key.last_checked).toLocaleString() : '从未';
        const errorMessage = key.error_message || '';
        tr.innerHTML = `
          <td class="key-display">${key.key_value.substring(0, 10)}...${key.key_value.substring(key.key_value.length - 4)}</td>
          <td>${badge}</td>
          <td><small>${lastChecked}</small></td>
          <td><small class="text-danger">${escapeHtml(errorMessage)}</small></td>
          <td>
            <button class="btn btn-sm btn-primary" data-key="${key.key_value}"><i class="bi bi-check-circle"></i></button>
            <button class="btn btn-sm btn-danger" data-id="${key.id}"><i class="bi bi-trash"></i></button>
          </td>`;
        tbody.appendChild(tr);
      });
      // 绑定行内按钮
      tbody.querySelectorAll('button[data-key]').forEach(btn => btn.addEventListener('click', e => checkSingleKey(e.currentTarget.getAttribute('data-key'))));
      tbody.querySelectorAll('button[data-id]').forEach(btn => btn.addEventListener('click', async e => {
        const id = e.currentTarget.getAttribute('data-id');
        if (!confirm('确定要删除这个密钥吗？')) return;
        try {
          const res = await fetch(`/api/keys/${id}`, { method: 'DELETE' });
          const result = await res.json();
          if (result.success) refreshKeyList(); else showAlert('删除失败: ' + result.message,'danger');
        } catch (err) { showAlert('删除失败: ' + err.message,'danger'); }
      }));
    } catch (e) { console.error('刷新密钥列表失败:', e); }
  }

  async function updateStats() {
    try {
      const res = await fetch('/api/stats');
      const stats = await res.json();
      qs('validCount').textContent = stats.valid_count;
      qs('invalidCount').textContent = stats.invalid_count;
      qs('pendingCount').textContent = stats.pending_count;
      const total = (stats.valid_count||0)+(stats.invalid_count||0)+(stats.pending_count||0);
      const validPct = total>0 ? Math.round((stats.valid_count/total)*100) : 0;
      const invalidPct = total>0 ? Math.round((stats.invalid_count/total)*100) : 0;
      const processedPct = total>0 ? Math.round(((stats.valid_count+stats.invalid_count)/total)*100) : 0;
      const pf = qs('statProgressFill'); if (pf) pf.style.width = `${processedPct}%`;
      const vp = qs('validPercent'); if (vp) vp.textContent = `${validPct}%`;
      const ip = qs('invalidPercent'); if (ip) ip.textContent = `${invalidPct}%`;
    } catch (e) { console.error('更新统计信息失败:', e); }
  }

  function checkStatus() {
    fetch('/api/check-status').then(r => r.json()).then(data => { if (data.success) updateCheckStatus(data.status); }).catch(() => {});
  }

  function updateCheckStatus(status) {
    const isChecking = status.is_checking;
    const stopRequested = status.stop_requested;
    isCheckingGlobal = isChecking;
    const idleElement = qs('status-idle');
    const checkingElement = qs('status-checking');
    const stopStatusElement = qs('stop-status');
    const stopBtn = qs('stop-check-btn');
    if (isChecking) {
      idleElement.classList.add('d-none');
      checkingElement.classList.remove('d-none');
      qs('check-type').textContent = status.check_type || '正在检测...';
      qs('check-duration').textContent = `运行时间: ${status.duration}秒`;
      if (stopRequested) { stopStatusElement.classList.remove('d-none'); stopBtn.disabled = true; stopBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 停止中'; }
      else { stopStatusElement.classList.add('d-none'); stopBtn.disabled = false; stopBtn.innerHTML = '<i class="bi bi-stop-fill"></i> 停止'; }
    } else {
      idleElement.classList.remove('d-none');
      checkingElement.classList.add('d-none');
      stopStatusElement.classList.add('d-none');
    }
  }

  function stopChecking() {
    if (!isCheckingGlobal) { showAlert('当前没有正在进行的检测','info'); return; }
    if (!confirm('确定要停止当前检测吗？已完成的检测结果将会保存。')) return;
    fetch('/api/stop-check', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then(r=>r.json()).then(data => { if (data.success) { showAlert(data.message,'success'); setTimeout(checkStatus, 100);} else { showAlert('停止失败: ' + data.message,'danger'); } })
      .catch(()=> showAlert('停止请求失败','danger'));
  }

  async function copyValidKeys(format) {
    try {
      const res = await fetch(`/api/valid-keys?format=${format}`);
      const result = await res.json();
      if (!result.success) { showAlert('获取有效密钥失败: ' + result.message,'danger'); return; }
      if (result.count === 0) { showAlert('没有有效的密钥可复制','info'); return; }
      if (navigator.clipboard) { await navigator.clipboard.writeText(result.content); showAlert(`已复制 ${result.count} 个有效密钥（${format==='comma'?'逗号分隔':'换行分隔'}）`,'success'); }
      else { const ta=document.createElement('textarea'); ta.value=result.content; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); showAlert(`已复制 ${result.count} 个有效密钥（${format==='comma'?'逗号分隔':'换行分隔'}）`,'success'); }
    } catch (e) { showAlert('复制失败: ' + e.message,'danger'); }
  }

  async function sendTestEmail() {
    const emailPassword = qs('emailPassword').value;
    const emails = getConfiguredEmails();
    if (emails.length === 0 || !emailPassword) { showAlert('请至少设置一个邮箱地址并填写Gmail应用密码','warning'); return; }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const invalid = emails.filter(e => !emailRegex.test(e));
    if (invalid.length) { showAlert(`以下邮箱地址格式无效: ${invalid.join(', ')}`,'danger'); return; }
    try {
      const res = await fetch('/api/test-email', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ receiver_email: emails[0], app_password: emailPassword })});
      const result = await res.json();
      if (result.success) { showAlert(result.message,'success'); addLogEntry({ timestamp: new Date().toLocaleString(), level:'INFO', message:`📧 ${result.message}` }); }
      else { showAlert('测试邮件发送失败: ' + result.message,'danger'); }
    } catch (e) { showAlert('测试邮件发送失败: ' + e.message,'danger'); }
  }

  function getConfiguredEmails() {
    const emails=[]; for (let i=1;i<=3;i++){ const el=qs(`email${i}`); if(el){ const v=el.value.trim(); if(v) emails.push(v);} } return emails;
  }
  function updateEmailCount(){ const count = getConfiguredEmails().length; const badge=qs('emailCount'); if(badge){ badge.textContent = count; badge.className = `badge ${count>0?'bg-success':'bg-secondary'}`; } }

  // 暴露必要函数（给内联或修复脚本使用）
  window.refreshKeyList = refreshKeyList;
  window.updateStats = updateStats;
  window.checkAllKeys = checkAllKeys;
  window.stopChecking = stopChecking;
  window.copyValidKeys = copyValidKeys;
  window.sendTestEmail = sendTestEmail;

  document.addEventListener('DOMContentLoaded', init);
})(); 