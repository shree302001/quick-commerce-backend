const API_BASE_URL = 'http://localhost:8000/api/v1';

// State Management
let currentState = {
    currentView: 'overview',
    stores: [], // We might need to fetch stores first
    selectedStoreId: 1,
    refreshInterval: null,
    isAutoRefresh: false
};

// DOM Elements
const contentArea = document.getElementById('content-area');
const pageTitle = document.getElementById('page-title');
const pageSubtitle = document.getElementById('page-subtitle');
const navItems = document.querySelectorAll('.nav-item');
const mainLoader = document.getElementById('main-loader');
const autoRefreshCheck = document.getElementById('auto-refresh-check');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupAutoRefresh();
    loadView('overview');
});

function setupNavigation() {
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.getAttribute('data-view');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            loadView(view);
        });
    });
}

function setupAutoRefresh() {
    autoRefreshCheck.addEventListener('change', (e) => {
        currentState.isAutoRefresh = e.target.checked;
        if (currentState.isAutoRefresh) {
            startRefreshTimer();
        } else {
            stopRefreshTimer();
        }
    });
}

function startRefreshTimer() {
    stopRefreshTimer(); // Clear any existing
    currentState.refreshInterval = setInterval(() => {
        console.log(`Auto-refreshing view: ${currentState.currentView}`);
        loadView(currentState.currentView, true);
    }, 5000); // Refresh every 5 seconds
}

function stopRefreshTimer() {
    if (currentState.refreshInterval) {
        clearInterval(currentState.refreshInterval);
        currentState.refreshInterval = null;
    }
}

async function loadView(view, isSilent = false) {
    currentState.currentView = view;
    if (!isSilent) showLoader();
    
    try {
        switch(view) {
            case 'overview':
                await renderOverview();
                break;
            case 'products':
                await renderProducts();
                break;
            case 'inventory':
                await renderInventory();
                break;
            case 'timeline':
                await renderTimeline();
                break;
            case 'orders':
                await renderOrders();
                break;
            case 'dlq':
                await renderDLQ();
                break;
            case 'store-load':
                await renderStoreLoad();
                break;
            case 'store-map':
                await renderStoreMap();
                break;
        }
    } catch (error) {
        console.error('Error loading view:', error);
        if (!isSilent) {
            contentArea.innerHTML = `<div class="error-msg" style="text-align:center; padding: 100px;">
                <i data-lucide="alert-circle" style="width: 48px; height: 48px; color: var(--accent-danger); margin-bottom: 20px;"></i>
                <h3 style="color: var(--text-bright)">Backend Connection Error</h3>
                <p style="color: var(--text-dim); margin-top: 10px;">Failed to load data from ${API_BASE_URL}.</p>
                <button class="btn btn-outline" style="margin-top: 20px;" onclick="loadView('${view}')">Retry Connection</button>
            </div>`;
        }
    } finally {
        lucide.createIcons();
    }
}

function showLoader() {
    contentArea.innerHTML = '<div class="loader-container"><div class="loader"></div></div>';
}

// --- Render Functions ---

async function renderOverview() {
    pageTitle.innerText = 'Dashboard Overview';
    pageSubtitle.innerText = 'Real-time performance metrics and quick stats.';

    // Fetch some summary data (we'll fetch orders and products count for now)
    const [ordersRes, productsRes, dlqRes] = await Promise.all([
        fetch(`${API_BASE_URL}/orders?limit=1`),
        fetch(`${API_BASE_URL}/products?limit=1`),
        fetch(`${API_BASE_URL}/dlq?limit=1`)
    ]);
    
    const ordersData = await ordersRes.json();
    const productsData = await productsRes.json();
    const dlqData = await dlqRes.json();

    contentArea.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-header"><i data-lucide="shopping-bag"></i></div>
                <div class="stat-label">Total Orders</div>
                <div class="stat-value">${ordersData.total || 0}</div>
                <div class="stat-footer"><span class="trend-up">↑ 12%</span> vs last week</div>
            </div>
            <div class="stat-card">
                <div class="stat-header"><i data-lucide="package"></i></div>
                <div class="stat-label">Unique Products</div>
                <div class="stat-value">${productsData.total || 0}</div>
                <div class="stat-footer">Across all categories</div>
            </div>
            <div class="stat-card">
                <div class="stat-header"><i data-lucide="alert-circle"></i></div>
                <div class="stat-label">DLQ Issues</div>
                <div class="stat-value">${dlqData.total || 0}</div>
                <div class="stat-footer ${dlqData.total > 0 ? 'trend-down' : 'trend-up'}">${dlqData.total > 0 ? 'Needs attention' : 'All clear'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-header"><i data-lucide="zap"></i></div>
                <div class="stat-label">Avg. Latency</div>
                <div class="stat-value">42ms</div>
                <div class="stat-footer"><span class="trend-up">Stable</span></div>
            </div>
        </div>

        <div class="data-table-container">
            <div class="table-header">
                <h3>Recent Orders</h3>
                <button class="btn btn-outline" onclick="loadView('orders')">View All</button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>User</th>
                        <th>Store</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody id="recent-orders-body">
                    <!-- Fetched orders will go here -->
                </tbody>
            </table>
        </div>
    `;

    // Fetch and render actual recent orders
    const recentOrdersRes = await fetch(`${API_BASE_URL}/orders?limit=5`);
    const recentOrdersData = await recentOrdersRes.json();
    const tbody = document.getElementById('recent-orders-body');
    
    if (recentOrdersData.items && recentOrdersData.items.length > 0) {
        tbody.innerHTML = recentOrdersData.items.map(order => `
            <tr>
                <td>#${order.id}</td>
                <td>User ${order.user_id}</td>
                <td>Store ${order.store_id}</td>
                <td>$${order.total_amount?.toFixed(2) || '0.00'}</td>
                <td><span class="status-badge status-${order.status.toLowerCase()}">${order.status}</span></td>
                <td>${new Date(order.created_at).toLocaleString()}</td>
            </tr>
        `).join('');
    } else {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 40px;">No recent orders found.</td></tr>';
    }
}

async function renderProducts() {
    pageTitle.innerText = 'Product Catalog';
    pageSubtitle.innerText = 'Manage and inspect available products.';
    
    const res = await fetch(`${API_BASE_URL}/products?limit=20`);
    const data = await res.json();

    contentArea.innerHTML = `
        <div class="data-table-container">
            <div class="table-header">
                <div class="search-bar" style="margin: 0">
                    <i data-lucide="search"></i>
                    <input type="text" placeholder="Filter products..." style="width: 300px">
                </div>
                <button class="btn btn-primary"><i data-lucide="plus"></i> Add Product</button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>SKU</th>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Price</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(p => `
                        <tr>
                            <td>${p.id}</td>
                            <td><code>${p.sku}</code></td>
                            <td>${p.name}</td>
                            <td>${p.category?.name || 'Uncategorized'}</td>
                            <td>$${p.price.toFixed(2)}</td>
                            <td>
                                <button class="icon-btn" onclick="viewProductDetail(${p.id})"><i data-lucide="eye"></i></button>
                                <button class="icon-btn"><i data-lucide="edit-2"></i></button>
                            </td>
                        </tr>
                    `).join('')}
                    ${data.items.length === 0 ? '<tr><td colspan="6" style="text-align:center; padding: 40px;">No products found.</td></tr>' : ''}
                </tbody>
            </table>
        </div>
    `;
}

async function renderInventory() {
    pageTitle.innerText = 'Inventory Levels';
    pageSubtitle.innerText = 'Real-time stock tracking per store.';
    
    // Default to store 1
    const res = await fetch(`${API_BASE_URL}/inventory/store/${currentState.selectedStoreId}`);
    const data = await res.json();

    contentArea.innerHTML = `
        <div class="filter-header" style="margin-bottom: 24px; display: flex; gap: 16px; align-items: center;">
            <label style="font-size: 0.9rem; color: var(--text-dim)">Store Hub:</label>
            <select onchange="updateStoreInventory(this.value)" style="background: var(--sidebar-bg); color: white; border: 1px solid var(--sidebar-border); padding: 8px 12px; border-radius: 8px; outline: none; cursor: pointer;">
                <option value="1" ${currentState.selectedStoreId == 1 ? 'selected' : ''}>Store #1 - Downtown</option>
                <option value="2" ${currentState.selectedStoreId == 2 ? 'selected' : ''}>Store #2 - Uptown</option>
                <option value="3" ${currentState.selectedStoreId == 3 ? 'selected' : ''}>Store #3 - Suburbs</option>
            </select>
        </div>
        <div class="data-table-container">
            <table>
                <thead>
                    <tr>
                        <th>Product ID</th>
                        <th>Total Quantity</th>
                        <th>Reserved</th>
                        <th>Available</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(i => {
                        const lowStock = i.available_quantity < 10;
                        return `
                        <tr>
                            <td><b>Product #${i.product_id}</b></td>
                            <td>${i.quantity}</td>
                            <td>${i.reserved_quantity}</td>
                            <td><span style="font-weight: 700; color: ${lowStock ? 'var(--accent-danger)' : 'var(--accent-success)'}">${i.available_quantity}</span></td>
                            <td>
                                <span class="status-badge ${lowStock ? 'status-failed' : 'status-completed'}">
                                    ${lowStock ? 'Low Stock' : 'Healthy'}
                                </span>
                            </td>
                        </tr>
                    `}).join('')}
                    ${data.items.length === 0 ? '<tr><td colspan="5" style="text-align:center; padding: 40px;">No inventory data for this store.</td></tr>' : ''}
                </tbody>
            </table>
        </div>
    `;
}

async function renderTimeline() {
    pageTitle.innerText = 'Inventory Timeline';
    pageSubtitle.innerText = 'Track stock movement and adjustment history.';

    try {
        const res = await fetch(`${API_BASE_URL}/inventory/snapshots?limit=20`);
        const data = await res.json();
        const timelineData = data.items || [];

        if (timelineData.length === 0) {
            contentArea.innerHTML = `<div style="text-align:center; padding: 100px; color: var(--text-dim)">
                <i data-lucide="clock" style="width: 48px; height: 48px; margin-bottom: 20px; opacity: 0.5;"></i>
                <p>No inventory history recorded yet.</p>
            </div>`;
            lucide.createIcons();
            return;
        }

        contentArea.innerHTML = `
            <div class="timeline">
                ${timelineData.map(item => {
                    const type = item.reason?.toUpperCase() || 'UPDATE';
                    const isPositive = ['RESTOCK', 'RETURN'].includes(type) || item.reason?.includes('added');
                    
                    return `
                    <div class="timeline-item">
                        <div class="timeline-content">
                            <span class="timeline-time">${new Date(item.timestamp).toLocaleString()}</span>
                            <div class="timeline-header">
                                <span class="timeline-title">${item.product_name}</span>
                                <span style="font-weight: 700;">
                                    ${item.quantity} units
                                </span>
                            </div>
                            <p class="timeline-desc">Stock level update recorded.</p>
                            <div style="margin-top: 10px; font-size: 0.7rem; color: var(--text-dim); display:flex; align-items:center; gap:5px;">
                                <i data-lucide="tag" style="width:12px;height:12px;"></i> ${type.replace(/_/g, ' ')}
                            </div>
                        </div>
                    </div>
                `}).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Timeline fetch error:', error);
        contentArea.innerHTML = '<p style="text-align:center; color: var(--accent-danger)">Failed to load timeline data.</p>';
    }
}

async function renderOrders() {
    pageTitle.innerText = 'Orders Management';
    pageSubtitle.innerText = 'Track and process all customer orders.';
    
    const res = await fetch(`${API_BASE_URL}/orders?limit=20`);
    const data = await res.json();

    contentArea.innerHTML = `
        <div class="data-table-container">
            <table>
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>User</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Latency</th>
                        <th>Date</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(o => `
                        <tr>
                            <td>#${o.id}</td>
                            <td>User ${o.user_id}</td>
                            <td>$${o.total_amount.toFixed(2)}</td>
                            <td><span class="status-badge status-${o.status.toLowerCase()}">${o.status}</span></td>
                            <td><span style="color: var(--text-dim)">${o.checkout_latency_ms ? o.checkout_latency_ms.toFixed(1) + 'ms' : '-'}</span></td>
                            <td>${new Date(o.created_at).toLocaleString()}</td>
                            <td><button class="icon-btn"><i data-lucide="chevron-right"></i></button></td>
                        </tr>
                    `).join('')}
                    ${data.items.length === 0 ? '<tr><td colspan="7" style="text-align:center; padding: 40px;">No orders found.</td></tr>' : ''}
                </tbody>
            </table>
        </div>
    `;
}

async function renderDLQ() {
    pageTitle.innerText = 'Dead Letter Queue (DLQ)';
    pageSubtitle.innerText = 'Inspect and retry failed order processing.';
    
    const res = await fetch(`${API_BASE_URL}/dlq`);
    const data = await res.json();

    contentArea.innerHTML = `
        <div class="data-table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Store Context</th>
                        <th>Error Specification</th>
                        <th>Retries</th>
                        <th>Time</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(f => `
                        <tr>
                            <td>#${f.id}</td>
                            <td>U:${f.user_id} | S:${f.store_id}</td>
                            <td style="color: var(--accent-danger); font-family: monospace; font-size: 0.8rem; max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${f.error_message}">
                                ${f.error_message}
                            </td>
                            <td><span class="status-badge status-pending">${f.retry_count}</span></td>
                            <td>${new Date(f.created_at).toLocaleString()}</td>
                            <td>
                                <button class="btn btn-outline" style="padding: 4px 12px" onclick="replayOrder(${f.id})">Retry</button>
                            </td>
                        </tr>
                    `).join('')}
                    ${data.items.length === 0 ? `<tr><td colspan="6" style="text-align:center; padding: 60px;">
                        <i data-lucide="check-circle" style="width: 48px; height: 48px; color: var(--accent-success); margin-bottom: 20px;"></i>
                        <p>All queues are clear. No failed orders detected.</p>
                    </td></tr>` : ''}
                </tbody>
            </table>
        </div>
    `;
}

async function renderStoreLoad() {
    pageTitle.innerText = 'Store Load Monitoring';
    pageSubtitle.innerText = 'Real-time performance and load metrics by store hub.';
    
    // Fetch metrics for multiple stores
    const stores = [1, 2, 3];
    const metrics = await Promise.all(stores.map(id => 
        fetch(`${API_BASE_URL}/orders/store/${id}/load`).then(r => r.json()).catch(() => null)
    ));

    contentArea.innerHTML = `
        <div class="load-grid">
            ${metrics.map((m, idx) => {
                const storeId = stores[idx];
                if (!m) return `<div class="load-card"><h3>Store #${storeId}</h3><p style="color:var(--text-dim)">Connecting...</p></div>`;
                
                const loadColor = m.total_load_score > 0.8 ? 'var(--accent-danger)' : (m.total_load_score > 0.5 ? 'var(--accent-warning)' : 'var(--accent-success)');
                
                return `
                <div class="load-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
                        <div>
                            <h3 style="color: var(--text-bright); margin-bottom: 4px;">Store Hub #${storeId}</h3>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <div class="status-indicator" style="width:8px; height:8px; border-radius:50%; background:${loadColor}; box-shadow: 0 0 10px ${loadColor}"></div>
                                <span style="font-size: 0.8rem; font-weight: 600; color: ${loadColor}">${m.total_load_score > 0.8 ? 'CRITICAL' : (m.total_load_score > 0.5 ? 'MODERATE' : 'STABLE')}</span>
                            </div>
                        </div>
                        <i data-lucide="activity" style="color: ${loadColor}"></i>
                    </div>

                    <div class="progress-container">
                        <div class="progress-header">
                            <span style="color: var(--text-dim)">Resource Saturation</span>
                            <span style="font-weight: 700;">${(m.total_load_score * 100).toFixed(0)}%</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-bar" style="width: ${m.total_load_score * 100}%; background: ${loadColor}"></div>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 30px; text-align: center;">
                        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                            <p style="font-size: 0.65rem; color: var(--text-dim); text-transform:uppercase; letter-spacing:1px;">Pending</p>
                            <p style="font-size: 1.25rem; font-weight: 700; color: var(--text-bright);">${m.pending_orders_count}</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                            <p style="font-size: 0.65rem; color: var(--text-dim); text-transform:uppercase; letter-spacing:1px;">Active</p>
                            <p style="font-size: 1.25rem; font-weight: 700; color: var(--text-bright);">${m.active_orders_count}</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                            <p style="font-size: 0.65rem; color: var(--text-dim); text-transform:uppercase; letter-spacing:1px;">Velocity</p>
                            <p style="font-size: 1.25rem; font-weight: 700; color: var(--text-bright);">${m.recent_velocity_per_min.toFixed(1)}</p>
                        </div>
                    </div>
                </div>
                `;
            }).join('')}
        </div>
    `;
}

async function renderStoreMap() {
    pageTitle.innerText = 'Store Network Map';
    pageSubtitle.innerText = 'Geospatial distribution of fulfillment hubs.';

    contentArea.innerHTML = `
        <div class="map-container">
            <div class="map-grid"></div>
            <div class="map-glow"></div>
            
            <div class="map-marker" style="top: 25%; left: 35%;">
                <i data-lucide="map-pin" fill="var(--accent-primary)"></i>
                <span>Hub #1 - Central</span>
            </div>
            
            <div class="map-marker" style="top: 55%; left: 65%;">
                <i data-lucide="map-pin" fill="var(--accent-primary)"></i>
                <span>Hub #2 - East End</span>
            </div>
            
            <div class="map-marker" style="top: 70%; left: 20%;">
                <i data-lucide="map-pin" fill="var(--accent-primary)"></i>
                <span>Hub #3 - South Park</span>
            </div>
            
            <div style="position: absolute; bottom: 30px; left: 30px; background: var(--sidebar-bg); border: 1px solid var(--sidebar-border); padding: 16px; border-radius: 12px; border-left: 4px solid var(--accent-primary);">
                <h4 style="color: var(--text-bright); margin-bottom: 4px;">Network Status</h4>
                <p style="font-size: 0.8rem; color: var(--text-dim)">3 Hubs Online | 100% Connectivity</p>
            </div>
            
            <div style="text-align: center; z-index: 10;">
                <p style="color: var(--text-dim); font-size: 0.9rem;">Map rendering module active.<br>High-fidelity GIS integration pending.</p>
            </div>
        </div>
    `;
}

// --- Interaction Handlers ---

async function updateStoreInventory(storeId) {
    currentState.selectedStoreId = storeId;
    renderInventory();
}

async function replayOrder(failedOrderId) {
    if (!confirm('Re-process this failed order instance?')) return;
    
    try {
        const res = await fetch(`${API_BASE_URL}/dlq/${failedOrderId}/replay`, { method: 'POST' });
        if (res.ok) {
            renderDLQ();
        } else {
            const err = await res.json();
            alert('Replay failed: ' + (err.detail || 'Service Error'));
        }
    } catch (e) {
        alert('Network error during replay.');
    }
}

async function viewProductDetail(productId) {
    const res = await fetch(`${API_BASE_URL}/products/${productId}`);
    const p = await res.json();
    
    const modalContainer = document.getElementById('modal-container');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.innerText = `Product Detail: ${p.name}`;
    modalBody.innerHTML = `
        <div style="display: flex; gap: 30px;">
            <div style="flex: 1;">
                <div style="width: 100%; aspect-ratio: 1; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px dashed var(--sidebar-border); display:flex; align-items:center; justify-content:center;">
                    <i data-lucide="image" style="width: 48px; height: 48px; color: var(--sidebar-border)"></i>
                </div>
            </div>
            <div style="flex: 1.5;">
                <div style="margin-bottom: 20px;">
                    <span style="font-size: 0.75rem; color: var(--accent-primary); font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">${p.category?.name || 'General'}</span>
                    <h2 style="font-size: 1.75rem; color: var(--text-bright); margin: 5px 0 10px 0;">$${p.price.toFixed(2)}</h2>
                    <p style="color: var(--text-dim); font-size: 0.9rem; line-height: 1.6;">${p.description || 'Detailed technical specifications for this product are currently being indexed by the system.'}</p>
                </div>
                <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: 10px; border-left: 3px solid var(--accent-secondary);">
                    <p style="font-size: 0.85rem;"><b>SKU:</b> <code style="color: var(--accent-secondary)">${p.sku}</code></p>
                    <p style="font-size: 0.85rem; margin-top: 8px;"><b>System ID:</b> #${p.id}</p>
                </div>
                <div style="margin-top: 24px;">
                    <button class="btn btn-primary" style="width: 100%">Edit Metadata</button>
                </div>
            </div>
        </div>
    `;
    
    modalContainer.classList.remove('hidden');
    lucide.createIcons();
    
    document.getElementById('close-modal').onclick = () => {
        modalContainer.classList.add('hidden');
    };
}
