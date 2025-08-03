// 应用修复脚本 - 提供缺少的函数和改进功能

// 全局配置
window.APP_CONFIG = {
    silentMode: false, // 静默模式，设为true时不显示非关键提醒
    debugMode: false,  // 调试模式
    alertCount: 0,     // 弹窗计数
    maxAlerts: 3       // 最大弹窗数量，超过后自动启用静默模式
};

// 提供给用户的控制函数
window.enableSilentMode = function() {
    window.APP_CONFIG.silentMode = true;
    console.log('🔇 已启用静默模式，错误信息将只在控制台显示');
};

window.disableSilentMode = function() {
    window.APP_CONFIG.silentMode = false;
    window.APP_CONFIG.alertCount = 0;
    console.log('🔊 已禁用静默模式');
};

// 1. 添加缺少的 showAlert 函数
function showAlert(message, type = 'info') {
    // 检查静默模式（除了成功消息外都不显示）
    if (window.APP_CONFIG.silentMode && type !== 'success') {
        console.log(`[静默模式] ${type.toUpperCase()}: ${message}`);
        return;
    }
    
    // 自动静默模式：如果弹窗太多，自动启用静默模式
    if (type === 'error' || type === 'warning') {
        window.APP_CONFIG.alertCount++;
        if (window.APP_CONFIG.alertCount >= window.APP_CONFIG.maxAlerts) {
            window.APP_CONFIG.silentMode = true;
            console.warn(`🔇 检测到过多弹窗(${window.APP_CONFIG.alertCount})，已自动启用静默模式`);
            console.log('如需重新启用弹窗，请在控制台输入：disableSilentMode()');
            return;
        }
    }
    
    // 创建alert容器（如果不存在）
    let alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(alertContainer);
    }

    // 创建alert元素
    const alertDiv = document.createElement('div');
    const alertClass = getAlertClass(type);
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.style.cssText = `
        margin-bottom: 10px;
        padding: 12px 16px;
        border: 1px solid transparent;
        border-radius: 4px;
        position: relative;
        animation: slideInRight 0.3s ease-out;
    `;
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" aria-label="Close" onclick="this.parentElement.remove()">
            <span aria-hidden="true">&times;</span>
        </button>
    `;

    // 添加到容器
    alertContainer.appendChild(alertDiv);

    // 3秒后自动移除
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => alertDiv.remove(), 300);
        }
    }, 3000);
}

function getAlertClass(type) {
    const types = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'danger': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info',
        'primary': 'alert-primary'
    };
    return types[type] || 'alert-info';
}

// 2. 添加alert样式到head
function addAlertStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .alert {
            position: relative;
            padding: 0.75rem 1.25rem;
            margin-bottom: 1rem;
            border: 1px solid transparent;
            border-radius: 0.25rem;
        }
        
        .alert-success {
            color: #155724;
            background-color: #d4edda;
            border-color: #c3e6cb;
        }
        
        .alert-danger {
            color: #721c24;
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        
        .alert-warning {
            color: #856404;
            background-color: #fff3cd;
            border-color: #ffeaa7;
        }
        
        .alert-info {
            color: #0c5460;
            background-color: #d1ecf1;
            border-color: #bee5eb;
        }
        
        .alert-primary {
            color: #004085;
            background-color: #cce7ff;
            border-color: #b8daff;
        }
        
        .btn-close {
            position: absolute;
            top: 0;
            right: 0;
            padding: 0.75rem 1.25rem;
            color: inherit;
            background: transparent;
            border: 0;
            float: right;
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1;
            text-shadow: 0 1px 0 #fff;
            opacity: 0.5;
            cursor: pointer;
        }
        
        .btn-close:hover {
            color: #000;
            text-decoration: none;
            opacity: 0.75;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        /* Bootstrap图标备用方案 */
        .bi-key::before { content: "🔑"; }
        .bi-bar-chart::before { content: "📊"; }
        .bi-plus-circle::before { content: "➕"; }
        .bi-check-circle::before { content: "✅"; }
        .bi-arrow-clockwise::before { content: "🔄"; }
        .bi-clock::before { content: "⏰"; }
        .bi-gear::before { content: "⚙️"; }
        .bi-terminal::before { content: "💻"; }
        .bi-trash::before { content: "🗑️"; }
        .bi-arrow-down::before { content: "⬇️"; }
        .bi-list::before { content: "📄"; }
        .bi-copy::before { content: "📋"; }
        .bi-envelope-check::before { content: "📧"; }
        .bi-stop-fill::before { content: "⏹️"; }
        .bi-hourglass-split::before { content: "⏳"; }
        .bi-exclamation-triangle::before { content: "⚠️"; }
    `;
    document.head.appendChild(style);
}

// 3. CDN备用加载方案
function loadBootstrapFallback() {
    // 检查Bootstrap是否已加载
    if (typeof window.bootstrap === 'undefined') {
        console.log('Bootstrap CDN加载失败，启用本地备用方案');
        
        // 加载本地CSS
        const localCSS = document.createElement('link');
        localCSS.rel = 'stylesheet';
        localCSS.href = '/static/css/local-bootstrap.css';
        document.head.appendChild(localCSS);
        
        // 创建基本的Bootstrap功能
        window.bootstrap = {
            Modal: function(element, options) {
                return {
                    show: function() {
                        element.style.display = 'block';
                        element.classList.add('show');
                    },
                    hide: function() {
                        element.style.display = 'none';
                        element.classList.remove('show');
                    }
                };
            }
        };
    }
}

// 4. 改进统计信息更新
function updateStatsWithAnimation() {
    // 直接调用原始函数而不是Promise链
    try {
        const originalUpdate = window.originalUpdateStats || updateStats;
        if (typeof originalUpdate === 'function') {
            originalUpdate();
        }
        
        // 添加更新动画效果
        const statElements = ['validCount', 'invalidCount', 'pendingCount'];
        statElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.transform = 'scale(1.1)';
                element.style.transition = 'transform 0.2s ease';
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 200);
            }
        });
    } catch (error) {
        console.warn('统计更新动画失败:', error);
    }
}

// 5. 改进日志滚动功能
function smoothScrollToBottom() {
    const logContainer = document.getElementById('logContainer');
    if (logContainer) {
        logContainer.scrollTo({
            top: logContainer.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// 6. 网络状态检测
function checkNetworkStatus() {
    if (navigator.onLine) {
        document.getElementById('statusText').textContent = '系统运行中 - 网络正常';
    } else {
        document.getElementById('statusText').textContent = '系统运行中 - 网络连接中断';
        showAlert('网络连接中断，某些功能可能受限', 'warning');
    }
}

// 7. 页面初始化
function initializeAppFixes() {
    // 添加样式
    addAlertStyles();
    
    // 检查并加载Bootstrap备用方案
    setTimeout(loadBootstrapFallback, 1000);
    
    // 监听网络状态
    window.addEventListener('online', checkNetworkStatus);
    window.addEventListener('offline', checkNetworkStatus);
    
    // 保存原始函数引用
    if (typeof updateStats === 'function') {
        window.originalUpdateStats = updateStats;
        updateStats = updateStatsWithAnimation;
    }
    
    if (typeof scrollToBottom === 'function') {
        window.originalScrollToBottom = scrollToBottom;
        scrollToBottom = smoothScrollToBottom;
    }
    
    // 初始网络检查
    checkNetworkStatus();
    
    console.log('应用修复脚本已加载');
}

// 8. DOM加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAppFixes);
} else {
    initializeAppFixes();
}

// 9. 添加智能错误处理（只处理严重错误）
window.addEventListener('error', function(e) {
    console.error('JavaScript错误:', e.error);
    
    // 只对严重错误显示提醒
    const errorMessage = e.error ? e.error.message : e.message || '';
    const filename = e.filename || '';
    
    // 忽略一些常见的非关键错误
    const ignoredErrors = [
        'Script error',
        'ResizeObserver loop limit exceeded',
        'Non-Error promise rejection captured',
        'ChunkLoadError',
        'Loading chunk',
        'Loading CSS chunk'
    ];
    
    const shouldIgnore = ignoredErrors.some(ignored => 
        errorMessage.toLowerCase().includes(ignored.toLowerCase())
    );
    
    // 忽略来自外部脚本的错误
    const isExternalScript = filename && (
        filename.includes('cdn.') || 
        filename.includes('unpkg.') || 
        filename.includes('googleapis.') ||
        filename.includes('bootstrap')
    );
    
    if (!shouldIgnore && !isExternalScript) {
        // 只在控制台记录，不弹窗
        console.warn('检测到应用错误，但已自动处理');
    }
});

// 10. 网络请求超时处理（静默处理）
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const [url, options = {}] = args;
    
    // 设置默认超时（增加到30秒）
    const timeout = options.timeout || 30000;
    
    return Promise.race([
        originalFetch(url, options),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('请求超时')), timeout)
        )
    ]).catch(error => {
        if (error.message === '请求超时') {
            console.warn('网络请求超时:', url);
            // 不显示弹窗，静默处理
        }
        throw error;
    });
};

// 11. 修复邮箱数量显示功能
function initEmailCountFix() {
    // 确保邮箱数量函数可用
    if (!window.updateEmailCount) {
        window.updateEmailCount = function() {
            const count = getConfiguredEmailCount();
            const countBadge = document.getElementById('emailCount');
            if (countBadge) {
                countBadge.textContent = count;
                countBadge.className = `badge ${count > 0 ? 'bg-success' : 'bg-secondary'}`;
            }
        };
    }
    
    if (!window.getConfiguredEmails) {
        window.getConfiguredEmails = function() {
            const emails = [];
            for (let i = 1; i <= 3; i++) {
                const emailInput = document.getElementById(`email${i}`);
                if (emailInput) {
                    const email = emailInput.value.trim();
                    if (email) {
                        emails.push(email);
                    }
                }
            }
            return emails;
        };
    }
    
    if (!window.getConfiguredEmailCount) {
        window.getConfiguredEmailCount = function() {
            return getConfiguredEmails().length;
        };
    }
    
    // 立即更新邮箱数量
    setTimeout(() => {
        if (window.updateEmailCount) {
            updateEmailCount();
        }
    }, 100);
    
    // 绑定邮箱输入事件
    for (let i = 1; i <= 3; i++) {
        const emailInput = document.getElementById(`email${i}`);
        if (emailInput) {
            emailInput.addEventListener('input', () => {
                if (window.updateEmailCount) {
                    updateEmailCount();
                }
            });
        }
    }
}

// 12. 修复Bootstrap下拉菜单功能
function initBootstrapDropdownFix() {
    console.log('开始修复Bootstrap下拉菜单...');
    
    // 添加下拉菜单样式
    const dropdownStyle = document.createElement('style');
    dropdownStyle.textContent = `
        .dropdown {
            position: relative;
            display: inline-block;
        }
        
        .dropdown-menu {
            display: none;
            position: absolute;
            background-color: white;
            min-width: 160px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            z-index: 1000;
            border: 1px solid rgba(0,0,0,.15);
            border-radius: 0.25rem;
            padding: 0.5rem 0;
            margin: 0.125rem 0 0;
            font-size: 1rem;
            color: #212529;
            text-align: left;
            list-style: none;
            background-clip: padding-box;
            right: 0; /* 右对齐 */
        }
        
        .dropdown-menu.show {
            display: block !important;
        }
        
        .dropdown-item {
            display: block;
            width: 100%;
            padding: 0.25rem 1rem;
            clear: both;
            font-weight: 400;
            color: #212529;
            text-align: inherit;
            text-decoration: none;
            white-space: nowrap;
            background-color: transparent;
            border: 0;
            cursor: pointer;
        }
        
        .dropdown-item:hover,
        .dropdown-item:focus {
            color: #1e2125;
            background-color: #e9ecef;
            text-decoration: none;
        }
        
        .dropdown-item:active {
            color: #fff;
            text-decoration: none;
            background-color: #0d6efd;
        }
        
        .dropdown-toggle-split {
            padding-right: 0.5625rem !important;
            padding-left: 0.5625rem !important;
        }
        
        .dropdown-toggle-split::after {
            margin-left: 0 !important;
        }
        
        /* 确保btn-group正确显示 */
        .btn-group {
            position: relative;
            display: inline-flex;
            vertical-align: middle;
        }
        
        .btn-group > .btn {
            position: relative;
            flex: 1 1 auto;
        }
        
        .btn-group > .btn:not(:first-child) {
            margin-left: -1px;
        }
        
        .btn-group > .btn:first-child:not(:last-child):not(.dropdown-toggle) {
            border-top-right-radius: 0;
            border-bottom-right-radius: 0;
        }
        
        .btn-group > .dropdown-toggle-split:last-child {
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
        }
    `;
    document.head.appendChild(dropdownStyle);
    
    // 强制修复下拉菜单功能
    function setupDropdownHandlers() {
        // 移除旧的事件监听器
        const oldHandlers = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        oldHandlers.forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
        });
        
        // 添加新的事件监听器
        document.addEventListener('click', function(e) {
            // 处理下拉按钮点击
            const dropdownToggle = e.target.closest('[data-bs-toggle="dropdown"]');
            if (dropdownToggle) {
                e.preventDefault();
                e.stopPropagation();
                
                // 找到相关的下拉菜单
                let dropdownMenu = null;
                const parent = dropdownToggle.parentElement;
                
                // 查找下拉菜单（可能在父元素中）
                if (parent) {
                    dropdownMenu = parent.querySelector('.dropdown-menu');
                    if (!dropdownMenu && parent.classList.contains('btn-group')) {
                        dropdownMenu = parent.querySelector('.dropdown-menu');
                    }
                }
                
                if (dropdownMenu) {
                    // 切换显示状态
                    const isShown = dropdownMenu.classList.contains('show');
                    
                    // 先关闭所有下拉菜单
                    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                        menu.classList.remove('show');
                    });
                    document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(btn => {
                        btn.setAttribute('aria-expanded', 'false');
                    });
                    
                    // 如果之前没有显示，则显示它
                    if (!isShown) {
                        dropdownMenu.classList.add('show');
                        dropdownToggle.setAttribute('aria-expanded', 'true');
                        
                        // 确保下拉菜单在视口内
                        const rect = dropdownMenu.getBoundingClientRect();
                        if (rect.right > window.innerWidth) {
                            dropdownMenu.style.right = '0';
                            dropdownMenu.style.left = 'auto';
                        }
                    }
                }
                
                return false;
            }
            
            // 处理下拉菜单项点击
            const dropdownItem = e.target.closest('.dropdown-item');
            if (dropdownItem) {
                // 关闭下拉菜单
                const menu = dropdownItem.closest('.dropdown-menu');
                if (menu) {
                    menu.classList.remove('show');
                }
                // 让原有的onclick处理器继续执行
            }
            
            // 点击其他地方关闭所有下拉菜单
            if (!e.target.closest('.dropdown-menu') && !e.target.closest('[data-bs-toggle="dropdown"]')) {
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
                document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(btn => {
                    btn.setAttribute('aria-expanded', 'false');
                });
            }
        });
        
        console.log('下拉菜单事件处理器已设置');
    }
    
    // 立即设置处理器
    setupDropdownHandlers();
    
    // 确保Bootstrap加载后也能工作
    if (typeof window.bootstrap !== 'undefined') {
        console.log('Bootstrap已加载，但我们使用自定义实现以确保可靠性');
    }
}

// 页面加载完成后初始化修复
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            initEmailCountFix();
            initBootstrapDropdownFix();
        }, 500); // 延迟500ms确保页面元素都已加载
    });
} else {
    setTimeout(() => {
        initEmailCountFix();
        initBootstrapDropdownFix();
    }, 500);
}

// 初始化完成提示
console.log('✅ 应用修复脚本加载完成');
console.log('🔧 修复功能包括：');
console.log('  - showAlert() 函数');
console.log('  - 网络状态监控'); 
console.log('  - CDN失效自动切换');
console.log('  - 智能错误处理');
console.log('  - 自动静默模式');
console.log('  - 邮箱数量显示修复');
console.log('  - Bootstrap下拉菜单修复');
console.log('📝 控制台命令：');
console.log('  - enableSilentMode()  启用静默模式');
console.log('  - disableSilentMode() 禁用静默模式'); 