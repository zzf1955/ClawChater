// Recall Web UI

let currentPage = 1;
let searchQuery = '';

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    loadRecentScreenshots();
    loadConfig();
    setupEventListeners();

    // 定时刷新状态
    setInterval(loadStatus, 5000);
});

// 加载状态
async function loadStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        const badge = document.getElementById('status-badge');
        badge.textContent = data.running ? '运行中' : '已停止';
        badge.className = 'badge ' + (data.running ? 'running' : 'stopped');

        document.getElementById('stat-total').textContent = data.total_screenshots;
        document.getElementById('stat-pending').textContent = data.pending_ocr;
        document.getElementById('stat-done').textContent = data.done_ocr;
    } catch (e) {
        console.error('加载状态失败:', e);
    }
}

// 加载最近截图
async function loadRecentScreenshots() {
    try {
        const res = await fetch('/api/screenshots?per_page=8');
        const data = await res.json();
        renderScreenshots(data, 'recent-screenshots');
    } catch (e) {
        console.error('加载截图失败:', e);
    }
}

// 加载截图列表
async function loadScreenshots() {
    try {
        const url = `/api/screenshots?page=${currentPage}&search=${encodeURIComponent(searchQuery)}`;
        const res = await fetch(url);
        const data = await res.json();
        renderScreenshots(data, 'screenshot-list');
        document.getElementById('page-info').textContent = `第 ${currentPage} 页`;
    } catch (e) {
        console.error('加载截图失败:', e);
    }
}

// 渲染截图
function renderScreenshots(screenshots, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = screenshots.map(s => {
        const imgPath = s.path.replace(/\\/g, '/').replace(/^.*screenshots/, '/screenshots');
        const time = new Date(s.timestamp).toLocaleString('zh-CN');
        const title = s.window_title || s.process_name || '';
        return `
            <div class="screenshot-card" data-id="${s.id}">
                <img src="${imgPath}" alt="" loading="lazy">
                <div class="info">
                    <div>${time}</div>
                    <div>${title.substring(0, 30)}</div>
                </div>
            </div>
        `;
    }).join('');
}

// 加载配置
async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();

        const form = document.getElementById('config-form');
        for (const [key, value] of Object.entries(data)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) input.value = value;
        }
    } catch (e) {
        console.error('加载配置失败:', e);
    }
}

// 保存配置
async function saveConfig(e) {
    e.preventDefault();
    const form = e.target;
    const data = {};

    form.querySelectorAll('input').forEach(input => {
        const value = input.type === 'number' ? parseFloat(input.value) : input.value;
        data[input.name] = value;
    });

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        alert(result.message);
    } catch (e) {
        alert('保存失败: ' + e.message);
    }
}

// 显示截图详情
async function showScreenshotDetail(id) {
    try {
        const res = await fetch(`/api/screenshot/${id}`);
        const data = await res.json();

        const imgPath = data.path.replace(/\\/g, '/').replace(/^.*screenshots/, '/screenshots');
        document.getElementById('modal-img').src = imgPath;
        document.getElementById('modal-info').innerHTML = `
            <p><strong>时间:</strong> ${new Date(data.timestamp).toLocaleString('zh-CN')}</p>
            <p><strong>窗口:</strong> ${data.window_title || '-'}</p>
            <p><strong>进程:</strong> ${data.process_name || '-'}</p>
        `;
        document.getElementById('modal-ocr').textContent = data.ocr_text || '(无OCR文本)';
        document.getElementById('modal').style.display = 'block';
    } catch (e) {
        console.error('加载详情失败:', e);
    }
}

// 设置事件监听
function setupEventListeners() {
    // Tab切换
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');

            if (btn.dataset.tab === 'screenshots') loadScreenshots();
        });
    });

    // 搜索
    document.getElementById('search-btn').addEventListener('click', () => {
        searchQuery = document.getElementById('search-input').value;
        currentPage = 1;
        loadScreenshots();
    });

    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchQuery = e.target.value;
            currentPage = 1;
            loadScreenshots();
        }
    });

    // 分页
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; loadScreenshots(); }
    });
    document.getElementById('next-page').addEventListener('click', () => {
        currentPage++; loadScreenshots();
    });

    // 配置表单
    document.getElementById('config-form').addEventListener('submit', saveConfig);

    // 截图点击
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.screenshot-card');
        if (card) showScreenshotDetail(card.dataset.id);
    });

    // 关闭弹窗
    document.querySelector('.modal .close').addEventListener('click', () => {
        document.getElementById('modal').style.display = 'none';
    });
    document.getElementById('modal').addEventListener('click', (e) => {
        if (e.target.id === 'modal') e.target.style.display = 'none';
    });
}
