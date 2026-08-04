/* ==========================================================================
   LOCAL LEAD RESCUE DASHBOARD - CLIENT CONTROLLER
   ========================================================================== */

let currentFilter = 'ALL';
let activeLeadsData = [];
let selectedLeadForSMS = null;
let pollInterval = null;

// Audio Effects
function playBeep(type) {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        const now = ctx.currentTime;
        if (type === 'lead') {
            osc.frequency.setValueAtTime(587.33, now); // D5
            osc.frequency.setValueAtTime(880, now + 0.1); // A5
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
            osc.start(now);
            osc.stop(now + 0.3);
        } else if (type === 'sent') {
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.setValueAtTime(659.25, now + 0.08);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
            osc.start(now);
            osc.stop(now + 0.25);
        }
    } catch(e) {}
}

// Fetch Leads & Update Dashboard
async function fetchLeads() {
    try {
        const res = await fetch('/api/leads');
        const data = await res.json();
        
        const previousLength = activeLeadsData.length;
        activeLeadsData = data.leads || [];

        if (previousLength > 0 && activeLeadsData.length > previousLength) {
            playBeep('lead');
        }

        renderStats(data.stats);
        renderLeadsList();
    } catch (e) {
        console.error("Failed to fetch leads:", e);
    }
}

// Render KPI Stats Header
function renderStats(stats) {
    if (!stats) return;
    document.getElementById('kpi-new-leads').textContent = stats.new_leads || 0;
    document.getElementById('kpi-followed-up').textContent = stats.followed_up || 0;
    document.getElementById('kpi-closed-jobs').textContent = stats.closed_jobs || 0;
    document.getElementById('kpi-conversion-rate').textContent = `${stats.conversion_rate || 0}%`;

    document.getElementById('count-all').textContent = stats.total_leads || 0;
    document.getElementById('count-new').textContent = stats.new_leads || 0;
    document.getElementById('count-followed').textContent = stats.followed_up || 0;
    document.getElementById('count-closed').textContent = stats.closed_jobs || 0;
}

// Render Lead Pipeline Cards
function renderLeadsList() {
    const container = document.getElementById('leads-container');

    const filtered = activeLeadsData.filter(lead => {
        if (currentFilter === 'ALL') return true;
        return lead.status === currentFilter;
    });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 bg-slate-900/40 border border-slate-800 rounded-2xl">
                <i class="fa-solid fa-inbox text-4xl text-slate-700 mb-3"></i>
                <h4 class="text-base font-semibold text-slate-300">No leads found under "${currentFilter}"</h4>
                <p class="text-xs text-slate-500 mt-1">Use the "Simulate Lead Webhook" button above to test incoming leads.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(lead => {
        let statusBadge = '';
        if (lead.status === 'New') {
            statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><i class="fa-solid fa-circle text-[8px] mr-1"></i> NEW LEAD</span>`;
        } else if (lead.status === 'Followed Up') {
            statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20"><i class="fa-solid fa-check-double mr-1"></i> SMS FOLLOWED UP</span>`;
        } else {
            statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20"><i class="fa-solid fa-award mr-1"></i> CLOSED JOB</span>`;
        }

        return `
            <div class="bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-4 sm:p-5 transition shadow-lg space-y-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-full bg-slate-800 text-slate-300 font-bold flex items-center justify-center text-sm border border-slate-700">
                            ${lead.name.charAt(0)}
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="font-bold text-base text-white">${lead.name}</h3>
                                ${statusBadge}
                            </div>
                            <p class="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                                <span><i class="fa-solid fa-phone text-slate-500 mr-1"></i>${lead.phone}</span>
                                <span>&bull;</span>
                                <span><i class="fa-solid fa-globe text-slate-500 mr-1"></i>${lead.source}</span>
                            </p>
                        </div>
                    </div>
                    <span class="text-xs text-slate-500 font-mono">${lead.created_at || 'Just now'}</span>
                </div>

                <div class="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800/60 space-y-1.5">
                    <div class="text-xs font-bold text-brand-400 flex items-center gap-1.5">
                        <i class="fa-solid fa-screwdriver-wrench"></i> ${lead.service}
                    </div>
                    ${lead.notes ? `<p class="text-xs text-slate-300 italic">"${lead.notes}"</p>` : ''}
                </div>

                ${lead.ai_sms_draft ? `
                    <div class="bg-blue-950/20 border border-blue-500/20 rounded-xl p-3.5 space-y-1">
                        <div class="text-[11px] font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                            <i class="fa-solid fa-robot"></i> Automated AI Follow-up Draft
                        </div>
                        <p class="text-xs text-slate-200 font-mono">${lead.ai_sms_draft}</p>
                    </div>
                ` : ''}

                <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
                    <div class="flex items-center gap-2">
                        <button class="open-sms-modal-btn px-3.5 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition" data-id="${lead.id}">
                            <i class="fa-solid fa-paper-plane"></i> Preview / Send SMS
                        </button>
                    </div>

                    <div class="flex items-center gap-2">
                        ${lead.status !== 'Closed' ? `
                            <button class="update-status-btn px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-semibold border border-slate-700 transition" data-id="${lead.id}" data-status="Closed">
                                <i class="fa-solid fa-circle-check text-purple-400 mr-1"></i> Mark Closed Job
                            </button>
                        ` : `
                            <button class="update-status-btn px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-semibold border border-slate-700 transition" data-id="${lead.id}" data-status="New">
                                <i class="fa-solid fa-rotate-left mr-1"></i> Re-open Lead
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Attach Event Listeners to dynamic buttons
    document.querySelectorAll('.open-sms-modal-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = parseInt(btn.dataset.id);
            const lead = activeLeadsData.find(l => l.id === id);
            if (lead) {
                selectedLeadForSMS = lead;
                document.getElementById('sms-modal-lead-name').textContent = `To: ${lead.name} (${lead.phone})`;
                document.getElementById('sms-message-text').value = lead.ai_sms_draft || '';
                document.getElementById('sms-modal').classList.remove('hidden');
            }
        });
    });

    document.querySelectorAll('.update-status-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = parseInt(btn.dataset.id);
            const newStatus = btn.dataset.status;
            await updateLeadStatus(id, newStatus);
        });
    });
}

// Update Lead Status via API
async function updateLeadStatus(leadId, newStatus) {
    try {
        const res = await fetch('/api/lead/status', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_id: leadId, status: newStatus })
        });
        if (res.ok) {
            fetchLeads();
        }
    } catch (e) {
        console.error("Failed to update status:", e);
    }
}

// Setup Event Handlers
function setupEventListeners() {
    // Auth Form
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const user = document.getElementById('login-user').value;
        const pass = document.getElementById('login-pass').value;

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass })
            });
            const data = await res.json();
            if (data.success) {
                localStorage.setItem('lead_rescue_token', data.token);
                document.getElementById('login-modal').classList.add('hidden');
                document.getElementById('app-wrapper').classList.remove('hidden');
                fetchLeads();
                if (!pollInterval) pollInterval = setInterval(fetchLeads, 2500);
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (e) {
            // Offline/demo fallback
            document.getElementById('login-modal').classList.add('hidden');
            document.getElementById('app-wrapper').classList.remove('hidden');
            fetchLeads();
            if (!pollInterval) pollInterval = setInterval(fetchLeads, 2500);
        }
    });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('lead_rescue_token');
        document.getElementById('app-wrapper').classList.add('hidden');
        document.getElementById('login-modal').classList.remove('hidden');
        if (pollInterval) clearInterval(pollInterval);
    });

    // Filter Tabs
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.filter-tab').forEach(t => {
                t.classList.remove('active', 'bg-slate-800', 'text-white', 'border', 'border-slate-700');
                t.classList.add('text-slate-400');
            });
            tab.classList.add('active', 'bg-slate-800', 'text-white', 'border', 'border-slate-700');
            tab.classList.remove('text-slate-400');

            currentFilter = tab.dataset.status;
            renderLeadsList();
        });
    });

    // Simulator Modal
    document.getElementById('open-simulator-btn').addEventListener('click', () => {
        document.getElementById('simulator-modal').classList.remove('hidden');
    });
    document.querySelectorAll('.close-sim-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('simulator-modal').classList.add('hidden');
        });
    });

    // Simulator Form Submit
    document.getElementById('simulator-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('sim-name').value,
            phone: document.getElementById('sim-phone').value,
            service: document.getElementById('sim-service').value,
            notes: document.getElementById('sim-notes').value,
            source: 'Website Missed Call Form',
            auto_send_sms: document.getElementById('sim-autosend').checked
        };

        try {
            const res = await fetch('/api/webhook/lead', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                playBeep('sent');
                document.getElementById('simulator-modal').classList.add('hidden');
                fetchLeads();
            }
        } catch (e) {
            console.error("Webhook ingestion error:", e);
        }
    });

    // SMS Modal Close
    document.querySelectorAll('.close-sms-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('sms-modal').classList.add('hidden');
        });
    });

    // Confirm Send SMS
    document.getElementById('confirm-send-sms-btn').addEventListener('click', async () => {
        if (!selectedLeadForSMS) return;
        const msg = document.getElementById('sms-message-text').value;

        try {
            const res = await fetch('/api/sms/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lead_id: selectedLeadForSMS.id, message: msg })
            });
            const data = await res.json();
            if (data.success) {
                playBeep('sent');
                document.getElementById('sms-modal').classList.add('hidden');
                fetchLeads();
            }
        } catch (e) {
            console.error("SMS send error:", e);
        }
    });
}

// Auto-check local session token
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    const token = localStorage.getItem('lead_rescue_token');
    if (token) {
        document.getElementById('login-modal').classList.add('hidden');
        document.getElementById('app-wrapper').classList.remove('hidden');
        fetchLeads();
        pollInterval = setInterval(fetchLeads, 2500);
    }
});
