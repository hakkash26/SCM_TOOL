/**
 * AI-Based Medicine Reminder & Prescription Management System
 * Unified Frontend Application Logic
 */

let allUsers = [];
let activeUser = null;
let currentTab = 'patient';

// --- Sound Synthesizer for Medicine Reminders (Web Audio API) ---
function playReminderSound() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        
        // Medical chime chord: C5 -> E5 -> G5
        const notes = [523.25, 659.25, 783.99];
        notes.forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = freq;
            
            const start = ctx.currentTime + (idx * 0.12);
            gain.gain.setValueAtTime(0, start);
            gain.gain.linearRampToValueAtTime(0.3, start + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, start + 0.6);
            
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(start);
            osc.stop(start + 0.65);
        });
    } catch (e) {
        console.log("Audio alert playback error:", e);
    }
}

// --- Toast Notification Helper ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '🔔';
    if (type === 'success') icon = '✅';
    if (type === 'warning') icon = '⚠️';
    if (type === 'danger') icon = '🚨';

    toast.innerHTML = `<span>${icon}</span><div>${message}</div>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// --- App Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    await fetchUsers();
    await fetchSession();
    setupEventListeners();
    refreshActiveView();
});

// --- Fetch Users and Populate Header Switcher ---
async function fetchUsers() {
    try {
        const res = await fetch('/api/v1/users');
        const data = await res.json();
        if (data.success) {
            allUsers = data.users;
            const select = document.getElementById('role-select');
            select.innerHTML = '';
            allUsers.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                opt.textContent = `${u.full_name} (${u.role.toUpperCase()})`;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Error fetching users:", err);
    }
}

// --- Fetch Active Session ---
async function fetchSession() {
    try {
        const res = await fetch('/api/v1/session');
        const data = await res.json();
        if (data.success) {
            activeUser = data.active_user;
            document.getElementById('role-select').value = activeUser.id;
            updateProfileBanner();
            // Automatically switch tab matching role
            switchTab(activeUser.role);
        }
    } catch (err) {
        console.error("Error fetching session:", err);
    }
}

function updateProfileBanner() {
    if (!activeUser) return;
    document.getElementById('banner-user-name').textContent = activeUser.full_name;
    document.getElementById('banner-user-role').textContent = activeUser.role;
    
    let icon = '👤';
    if (activeUser.role === 'doctor') icon = '🩺';
    if (activeUser.role === 'caregiver') icon = '🛡️';
    if (activeUser.role === 'pharmacy') icon = '💊';
    document.getElementById('banner-avatar-icon').textContent = icon;

    let meta = activeUser.conditions || activeUser.email || '';
    if (activeUser.age) meta = `Age: ${activeUser.age} | ` + meta;
    document.getElementById('banner-user-meta').textContent = meta;
}

// --- Event Listeners ---
function setupEventListeners() {
    // Role Select Change
    document.getElementById('role-select').addEventListener('change', async (e) => {
        const userId = e.target.value;
        const res = await fetch('/api/v1/session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await res.json();
        if (data.success) {
            activeUser = data.active_user;
            updateProfileBanner();
            switchTab(activeUser.role);
            showToast(`Switched active view to: ${activeUser.full_name}`);
        }
    });

    // Navigation Tab Buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });

    // SCM Traceability Modal
    document.getElementById('scm-modal-btn').addEventListener('click', () => {
        document.getElementById('scm-modal').classList.add('open');
    });
    document.getElementById('scm-modal-close').addEventListener('click', () => {
        document.getElementById('scm-modal').classList.remove('open');
    });

    // Doctor: Add Medicine Row
    const addMedBtn = document.getElementById('btn-add-rx-row');
    if (addMedBtn) {
        addMedBtn.addEventListener('click', addPrescriptionItemRow);
    }

    // Doctor: AI Check Button
    const aiCheckBtn = document.getElementById('btn-run-ai-check');
    if (aiCheckBtn) {
        aiCheckBtn.addEventListener('click', runDoctorInteractionCheck);
    }

    // Doctor: Prescription Form Submit
    const rxForm = document.getElementById('prescription-form');
    if (rxForm) {
        rxForm.addEventListener('submit', handlePrescriptionSubmit);
    }

    // Live Reminder Sound Demo Button
    const demoSoundBtn = document.getElementById('btn-demo-reminder');
    if (demoSoundBtn) {
        demoSoundBtn.addEventListener('click', () => {
            playReminderSound();
            showReminderAlertModal("Lisinopril 10 mg", "08:30 AM", "After Breakfast");
        });
    }
}

// --- Switch Tabs ---
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === tab);
    });
    document.querySelectorAll('.view-panel').forEach(p => {
        p.classList.toggle('active', p.id === `view-${tab}`);
    });
    refreshActiveView();
}

function refreshActiveView() {
    if (currentTab === 'patient') {
        loadPatientDashboard();
    } else if (currentTab === 'doctor') {
        loadDoctorDashboard();
    } else if (currentTab === 'caregiver') {
        loadCaregiverDashboard();
    } else if (currentTab === 'pharmacy') {
        loadPharmacyDashboard();
    }
}

// ==========================================
// 1. PATIENT DASHBOARD LOGIC
// ==========================================
async function loadPatientDashboard() {
    const patientId = (activeUser && activeUser.role === 'patient') ? activeUser.id : 3;
    
    // 1. Fetch Today's Reminders
    try {
        const res = await fetch(`/api/v1/reminders?patient_id=${patientId}`);
        const data = await res.json();
        renderPatientReminders(data.reminders || []);
    } catch (e) {
        console.error("Failed loading reminders:", e);
    }

    // 2. Fetch AI Adherence Prediction
    try {
        const res = await fetch(`/api/v1/ai/adherence-prediction?patient_id=${patientId}`);
        const data = await res.json();
        if (data.success) {
            renderAIPrediction(data.prediction);
        }
    } catch (e) {
        console.error("Failed loading AI prediction:", e);
    }

    // 3. Fetch Adherence Analytics
    try {
        const res = await fetch(`/api/v1/analytics?patient_id=${patientId}`);
        const data = await res.json();
        if (data.success) {
            renderAdherenceMetrics(data.metrics);
        }
    } catch (e) {
        console.error("Failed loading analytics:", e);
    }

    // 4. Fetch Active Prescriptions
    try {
        const res = await fetch(`/api/v1/prescriptions?patient_id=${patientId}`);
        const data = await res.json();
        renderPatientPrescriptions(data.prescriptions || []);
    } catch (e) {
        console.error("Failed loading prescriptions:", e);
    }
}

function renderPatientReminders(reminders) {
    const container = document.getElementById('reminders-container');
    if (!reminders.length) {
        container.innerHTML = `<div class="card" style="text-align:center; padding:2rem; color:var(--text-muted)">
            <p>🎉 No pending reminders for today! All medications are up to date.</p>
        </div>`;
        return;
    }

    let html = '';
    reminders.forEach(r => {
        const isTaken = r.status === 'taken';
        const isSnoozed = r.status === 'snoozed';
        const isSkipped = r.status === 'skipped';
        const isLowSupply = r.remaining_quantity <= 10;

        html += `
        <div class="reminder-card status-${r.status}">
            <div class="reminder-main">
                <div class="time-badge">${r.reminder_time}</div>
                <div class="med-info">
                    <h3>${r.medicine_name} <span style="font-size:0.85rem; font-weight:normal; color:var(--text-muted)">${r.dosage}</span></h3>
                    <p>Instructions: <strong>${r.timing_instruction}</strong></p>
                    <div class="med-meta">
                        <span class="pill-badge food">${r.timing_instruction}</span>
                        <span class="pill-badge ${isLowSupply ? 'stock-low' : ''}">Stock: ${r.remaining_quantity} left</span>
                        <span class="pill-badge" style="text-transform: capitalize;">Status: <strong>${r.status}</strong></span>
                    </div>
                </div>
            </div>
            <div class="reminder-actions">
                ${!isTaken ? `
                    <button class="btn btn-success" onclick="markReminderStatus(${r.id}, 'taken')">
                        ✓ Take
                    </button>
                    <button class="btn btn-warning" onclick="markReminderStatus(${r.id}, 'snoozed')">
                        ⏰ Snooze
                    </button>
                    <button class="btn btn-outline" style="color:var(--danger)" onclick="markReminderStatus(${r.id}, 'skipped')">
                        ✕ Skip
                    </button>
                ` : `
                    <span style="color:var(--success); font-weight:700; font-size:0.9rem;">✓ Taken Today</span>
                `}
                ${isLowSupply ? `
                    <button class="btn btn-outline" style="border-color:#f87171; color:#dc2626;" onclick="requestRefillForPill(${r.prescription_item_id}, '${r.medicine_name}')">
                        💊 Request Refill
                    </button>
                ` : ''}
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

function renderAIPrediction(pred) {
    const scoreElem = document.getElementById('ai-adherence-score');
    const badgeElem = document.getElementById('ai-risk-badge');
    const adviceElem = document.getElementById('ai-advice-content');

    if (scoreElem) scoreElem.textContent = `${pred.adherence_probability}%`;
    if (badgeElem) {
        badgeElem.textContent = pred.risk_category;
        badgeElem.className = `pill-badge ${pred.badge_color === 'danger' ? 'stock-low' : 'food'}`;
    }
    if (adviceElem) adviceElem.textContent = pred.ai_advice;
}

function renderAdherenceMetrics(metrics) {
    const totalElem = document.getElementById('stat-total-doses');
    const takenElem = document.getElementById('stat-taken-doses');
    const pctElem = document.getElementById('stat-compliance-pct');

    if (totalElem) totalElem.textContent = metrics.total_doses;
    if (takenElem) takenElem.textContent = metrics.taken;
    if (pctElem) pctElem.textContent = `${metrics.adherence_percentage}%`;
}

function renderPatientPrescriptions(rxList) {
    const container = document.getElementById('patient-rx-list');
    if (!container) return;
    if (!rxList.length) {
        container.innerHTML = `<p style="color:var(--text-muted)">No active prescriptions on file.</p>`;
        return;
    }

    let html = '';
    rxList.forEach(rx => {
        html += `
        <div style="border-bottom:1px solid #f1f5f9; padding-bottom:1rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <strong>${rx.diagnosis}</strong>
                <span class="pill-badge food">${rx.prescription_code}</span>
            </div>
            <p style="font-size:0.85rem; color:var(--text-muted)">Doctor: ${rx.doctor_name} | Notes: ${rx.notes || 'None'}</p>
            <div style="margin-top:0.5rem; display:flex; flex-wrap:wrap; gap:0.5rem;">
                ${rx.items.map(it => `
                    <span class="pill-badge" style="background:#f1f5f9;">
                        💊 ${it.medicine_name} (${it.dosage}) - ${it.frequency}
                    </span>
                `).join('')}
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

async function markReminderStatus(reminderId, status) {
    try {
        const res = await fetch(`/api/v1/reminders/${reminderId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, status === 'taken' ? 'success' : 'warning');
            loadPatientDashboard();
        }
    } catch (e) {
        console.error("Status update error:", e);
    }
}

async function requestRefillForPill(prescriptionItemId, medicineName) {
    const patientId = (activeUser && activeUser.role === 'patient') ? activeUser.id : 3;
    try {
        const res = await fetch('/api/v1/refills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                prescription_item_id: prescriptionItemId,
                pharmacy_id: 5,
                medicine_name: medicineName,
                quantity: 30
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Refill request for ${medicineName} sent to HealthPlus Pharmacy!`, 'success');
        }
    } catch (e) {
        console.error("Refill error:", e);
    }
}

// ==========================================
// 2. DOCTOR DASHBOARD LOGIC
// ==========================================
function loadDoctorDashboard() {
    // Populate patient dropdown in doctor prescription form
    const sel = document.getElementById('rx-patient-select');
    if (sel) {
        sel.innerHTML = '';
        allUsers.filter(u => u.role === 'patient').forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.full_name} (Age: ${p.age}, ${p.conditions})`;
            sel.appendChild(opt);
        });
    }
}

function addPrescriptionItemRow() {
    const container = document.getElementById('rx-items-container');
    const row = document.createElement('div');
    row.className = 'rx-item-row';
    row.style = 'display:grid; grid-template-columns: 2fr 1fr 1.5fr 1fr auto; gap:0.5rem; margin-bottom:0.75rem; align-items:center;';
    row.innerHTML = `
        <input type="text" class="form-control med-name-input" placeholder="e.g. Warfarin, Aspirin, Metformin" required>
        <input type="text" class="form-control med-dosage-input" placeholder="e.g. 5 mg" required>
        <select class="form-control med-freq-select">
            <option value="Once Daily (Morning)">Once Daily (Morning)</option>
            <option value="Twice Daily">Twice Daily</option>
            <option value="Three Times Daily">Three Times Daily</option>
            <option value="Once Daily (Night)">Once Daily (Night)</option>
        </select>
        <input type="number" class="form-control med-duration-input" value="30" min="1" max="90">
        <button type="button" class="btn btn-outline" style="color:var(--danger);" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(row);
}

function getDoctorMedList() {
    const meds = [];
    document.querySelectorAll('.med-name-input').forEach(input => {
        if (input.value.trim()) meds.push(input.value.trim());
    });
    return meds;
}

async function runDoctorInteractionCheck() {
    const meds = getDoctorMedList();
    if (meds.length < 2) {
        showToast("Enter at least 2 medications to check drug-drug interactions.", "warning");
        return;
    }

    try {
        const res = await fetch('/api/v1/ai/check-interactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ medicines: meds })
        });
        const data = await res.json();
        renderDoctorInteractionReport(data.data);
    } catch (e) {
        console.error("AI check error:", e);
    }
}

function renderDoctorInteractionReport(result) {
    const box = document.getElementById('doctor-ai-report-box');
    box.style.display = 'block';

    if (result.is_safe) {
        box.innerHTML = `
            <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-left:4px solid var(--success); padding:1rem; border-radius:var(--radius-md);">
                <strong style="color:#065f46;">✅ AI Analysis: Safe Combination</strong>
                <p style="font-size:0.85rem; color:#047857; margin-top:0.25rem;">No known severe drug-drug interactions detected among the specified medications.</p>
            </div>
        `;
    } else {
        box.innerHTML = `
            <div class="interaction-alert-box">
                <div class="interaction-alert-header">
                    <span>🚨</span>
                    <span>AI Alert: ${result.status} (${result.interactions_count} Conflict Found)</span>
                </div>
                ${result.interactions.map(it => `
                    <div class="interaction-item">
                        <strong style="color:#991b1b;">${it.drug_1} + ${it.drug_2} [${it.severity}]</strong>
                        <p style="font-size:0.85rem; margin-top:0.2rem; color:#374151;">${it.description}</p>
                        <p style="font-size:0.8rem; margin-top:0.3rem; color:#0369a1;"><strong>Clinical Recommendation:</strong> ${it.recommendation}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

async function handlePrescriptionSubmit(e) {
    e.preventDefault();
    const patientId = document.getElementById('rx-patient-select').value;
    const diagnosis = document.getElementById('rx-diagnosis-input').value;
    const notes = document.getElementById('rx-notes-input').value;

    const items = [];
    document.querySelectorAll('.rx-item-row').forEach(row => {
        const name = row.querySelector('.med-name-input').value;
        const dosage = row.querySelector('.med-dosage-input').value;
        const freq = row.querySelector('.med-freq-select').value;
        const duration = parseInt(row.querySelector('.med-duration-input').value) || 30;

        let schedTimes = ["08:30"];
        if (freq === 'Twice Daily') schedTimes = ["08:30", "20:00"];
        if (freq === 'Three Times Daily') schedTimes = ["08:30", "13:30", "20:30"];
        if (freq === 'Once Daily (Night)') schedTimes = ["21:30"];

        if (name && dosage) {
            items.push({
                medicine_name: name,
                dosage: dosage,
                frequency: freq,
                scheduled_times: schedTimes,
                timing_instruction: "After Food",
                duration_days: duration,
                total_quantity: duration * (schedTimes.length)
            });
        }
    });

    if (!items.length) {
        showToast("Please add at least one medication to prescribe.", "warning");
        return;
    }

    try {
        const res = await fetch('/api/v1/prescriptions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                doctor_id: (activeUser && activeUser.role === 'doctor') ? activeUser.id : 1,
                patient_id: parseInt(patientId),
                diagnosis: diagnosis,
                notes: notes,
                items: items
            })
        });

        const data = await res.json();
        if (res.status === 409 && data.requires_confirmation) {
            // High risk interaction warning modal
            renderDoctorInteractionReport(data.interaction_warning);
            if (confirm("⚠️ WARNING: High risk drug interaction detected! Do you want to proceed and override this prescription?")) {
                // Retry with force_override
                const overrideRes = await fetch('/api/v1/prescriptions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        doctor_id: 1,
                        patient_id: parseInt(patientId),
                        diagnosis: diagnosis,
                        notes: notes,
                        items: items,
                        force_override: true
                    })
                });
                const overrideData = await overrideRes.json();
                if (overrideData.success) {
                    showToast(overrideData.message, 'success');
                    document.getElementById('prescription-form').reset();
                }
            }
        } else if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('prescription-form').reset();
            document.getElementById('doctor-ai-report-box').style.display = 'none';
        }
    } catch (e) {
        console.error("Prescription error:", e);
    }
}

// ==========================================
// 3. CAREGIVER DASHBOARD LOGIC
// ==========================================
async function loadCaregiverDashboard() {
    const caregiverId = (activeUser && activeUser.role === 'caregiver') ? activeUser.id : 2;
    try {
        const res = await fetch(`/api/v1/caregiver/alerts?caregiver_id=${caregiverId}`);
        const data = await res.json();
        renderCaregiverAlerts(data.alerts || []);
    } catch (e) {
        console.error("Caregiver alerts error:", e);
    }
}

function renderCaregiverAlerts(alerts) {
    const container = document.getElementById('caregiver-alerts-container');
    if (!container) return;

    if (!alerts.length) {
        container.innerHTML = `<div class="card" style="text-align:center; padding:2rem; color:var(--text-muted)">
            <p>✅ All patients are adherent. No missed dose escalation alerts at this time.</p>
        </div>`;
        return;
    }

    let html = '';
    alerts.forEach(a => {
        const isCritical = a.severity === 'critical';
        html += `
        <div class="card" style="border-left:5px solid ${isCritical ? 'var(--danger)' : 'var(--warning)'}; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <span>${isCritical ? '🚨' : '⚠️'}</span>
                    <strong>${a.patient_name} - ${a.alert_type.toUpperCase().replace('_', ' ')}</strong>
                </div>
                <span style="font-size:0.75rem; color:var(--text-muted);">${a.created_at}</span>
            </div>
            <p style="font-size:0.9rem; color:#374151;">${a.message}</p>
            <div style="margin-top:0.75rem; display:flex; gap:0.5rem;">
                <a href="tel:+15550303" class="btn btn-outline" style="font-size:0.8rem;">📞 Call Patient (Robert)</a>
                <button class="btn btn-primary" style="font-size:0.8rem;" onclick="showToast('Acknowledge logged to SCM audit records.')">✓ Acknowledge</button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

// ==========================================
// 4. PHARMACY DASHBOARD LOGIC
// ==========================================
async function loadPharmacyDashboard() {
    const pharmacyId = (activeUser && activeUser.role === 'pharmacy') ? activeUser.id : 5;
    try {
        const res = await fetch(`/api/v1/refills?pharmacy_id=${pharmacyId}`);
        const data = await res.json();
        renderPharmacyRefills(data.refills || []);
    } catch (e) {
        console.error("Pharmacy refills error:", e);
    }
}

function renderPharmacyRefills(refills) {
    const container = document.getElementById('pharmacy-refills-container');
    if (!container) return;

    if (!refills.length) {
        container.innerHTML = `<p style="text-align:center; padding:2rem; color:var(--text-muted)">No pending refill requests.</p>`;
        return;
    }

    let html = '';
    refills.forEach(rf => {
        const isDispensed = rf.status === 'dispensed';
        const isApproved = rf.status === 'approved';

        html += `
        <div class="card" style="margin-bottom:1rem; border-left: 4px solid ${isDispensed ? 'var(--success)' : 'var(--primary)'}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="font-size:1.05rem;">💊 ${rf.medicine_name} (${rf.requested_quantity} units)</h3>
                    <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.2rem;">
                        Patient: <strong>${rf.patient_name}</strong> | Phone: ${rf.patient_phone} | Req Code: ${rf.request_code}
                    </p>
                </div>
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <span class="pill-badge" style="text-transform:uppercase;">${rf.status}</span>
                    ${!isDispensed ? `
                        <button class="btn btn-success" onclick="updateRefillStatus(${rf.id}, 'dispensed')">
                            ✓ Dispense Refill
                        </button>
                    ` : `
                        <span style="color:var(--success); font-weight:700; font-size:0.85rem;">✓ Fulfilled</span>
                    `}
                </div>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

async function updateRefillStatus(refillId, status) {
    try {
        const res = await fetch(`/api/v1/refills/${refillId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadPharmacyDashboard();
        }
    } catch (e) {
        console.error("Update refill status error:", e);
    }
}

// ==========================================
// REMINDER MODAL POPUP (LIVE DEMO)
// ==========================================
function showReminderAlertModal(medName, schedTime, instructions) {
    const modal = document.getElementById('reminder-alert-modal');
    document.getElementById('modal-med-title').textContent = medName;
    document.getElementById('modal-time-badge').textContent = schedTime;
    document.getElementById('modal-instructions').textContent = instructions;
    modal.classList.add('open');
}

function closeReminderAlertModal() {
    document.getElementById('reminder-alert-modal').classList.remove('open');
}
