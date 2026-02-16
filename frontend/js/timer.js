/* ==========================================
   Timer Module  – server-synced (cross-device)
   ========================================== */
import { api } from './api.js';
import { t } from './i18n.js';
import { formatTime, formatTimerDisplay, formatDateISO, formatDuration,
         calculateWorkMinutes, showToast, escapeHtml } from './utils.js';

let timerInterval = null;
let timerState = { isRunning: false, startTime: null, description: '' };

/* ---------- init: load from server, fallback to localStorage ---------- */
export async function initTimer() {
    try {
        const remote = await api.getTimerState();
        if (remote && remote.is_running) {
            timerState.isRunning = true;
            timerState.startTime = new Date(remote.start_time);
            timerState.description = remote.description || '';
        } else {
            timerState = { isRunning: false, startTime: null, description: '' };
        }
    } catch (_) {
        // Offline / error – fall back to localStorage
        const saved = localStorage.getItem('zeittracker_timer');
        if (saved) {
            try {
                timerState = JSON.parse(saved);
                if (timerState.startTime) timerState.startTime = new Date(timerState.startTime);
            } catch (_e) { /* ignore */ }
        }
    }
    // Populate description field if timer was running
    if (timerState.isRunning && timerState.description) {
        const desc = document.getElementById('taskDescription');
        if (desc) desc.value = timerState.description;
    }
    saveTimerLocal();
    updateTimerUI();
}

/* ---------- localStorage helper (offline fallback) ---------- */
function saveTimerLocal() {
    localStorage.setItem('zeittracker_timer', JSON.stringify(timerState));
}

/* ---------- start ---------- */
export async function startTimer() {
    timerState.isRunning = true;
    timerState.startTime = new Date();
    timerState.description = document.getElementById('taskDescription')?.value || '';
    saveTimerLocal();
    updateTimerUI();
    timerInterval = setInterval(updateTimerDisplay, 1000);

    // Persist to server (fire-and-forget; ignore errors)
    try { await api.saveTimerState(timerState.startTime.toISOString(), timerState.description); } catch (_) {}
}

/* ---------- stop ---------- */
export async function stopTimer(onRefresh) {
    if (!timerState.isRunning) return;
    clearInterval(timerInterval);
    timerInterval = null;

    const endTime = new Date();
    const startTime = new Date(timerState.startTime);

    const startStr = formatTime(startTime);
    const endStr = formatTime(endTime);
    const dateStr = formatDateISO(startTime);

    try {
        await api.createEntry({
            date: dateStr,
            start_time: startStr,
            end_time: endStr,
            break_minutes: 0,
            description: timerState.description,
        });
        showToast(t('timerSaved'), 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }

    timerState.isRunning = false;
    timerState.startTime = null;
    timerState.description = '';
    saveTimerLocal();
    updateTimerUI();

    // Clear server timer state
    try { await api.clearTimerState(); } catch (_) {}

    if (onRefresh) onRefresh();
}

/* ---------- reset ---------- */
export async function resetTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    timerState.isRunning = false;
    timerState.startTime = null;
    timerState.description = '';
    const desc = document.getElementById('taskDescription');
    if (desc) desc.value = '';
    saveTimerLocal();
    updateTimerUI();

    // Clear server timer state
    try { await api.clearTimerState(); } catch (_) {}
}

function updateTimerDisplay() {
    if (!timerState.isRunning || !timerState.startTime) return;
    const elapsed = Date.now() - new Date(timerState.startTime).getTime();
    const el = document.getElementById('timerTime');
    if (el) el.textContent = formatTimerDisplay(elapsed);
}

function updateTimerUI() {
    const startStopBtn = document.getElementById('startStopBtn');
    const startStopIcon = document.getElementById('startStopIcon');
    const startStopText = document.getElementById('startStopText');
    const resetBtn = document.getElementById('resetBtn');
    const timerStatus = document.getElementById('timerStatus');
    const timerInfo = document.getElementById('timerInfo');
    const startTimeDisplay = document.getElementById('startTimeDisplay');

    if (!startStopBtn) return;

    if (timerState.isRunning) {
        startStopIcon.textContent = '⏹️';
        startStopText.textContent = t('stop');
        startStopBtn.classList.remove('btn-primary');
        startStopBtn.classList.add('btn-danger');
        resetBtn.disabled = false;
        timerStatus.textContent = t('timerRunning');
        timerInfo.classList.remove('hidden');
        startTimeDisplay.textContent = formatTime(new Date(timerState.startTime));
        if (!timerInterval) {
            timerInterval = setInterval(updateTimerDisplay, 1000);
            updateTimerDisplay();
        }
    } else {
        startStopIcon.textContent = '▶️';
        startStopText.textContent = t('start');
        startStopBtn.classList.add('btn-primary');
        startStopBtn.classList.remove('btn-danger');
        resetBtn.disabled = true;
        timerStatus.textContent = t('timerStopped');
        timerInfo.classList.add('hidden');
        const timerTime = document.getElementById('timerTime');
        if (timerTime) timerTime.textContent = '00:00:00';
    }
}

export async function renderTodayEntries() {
    const container = document.getElementById('todayEntriesList');
    if (!container) return;

    try {
        const today = formatDateISO(new Date());
        const entries = await api.getEntries({ date_from: today, date_to: today });
        if (!entries || entries.length === 0) {
            container.innerHTML = `<p class="no-entries">${t('noEntries')}</p>`;
            return;
        }
        container.innerHTML = entries.map(entry => createEntryCard(entry)).join('');
    } catch (err) {
        container.innerHTML = `<p class="no-entries">${t('error')}: ${escapeHtml(err.message)}</p>`;
    }
}

export function createEntryCard(entry) {
    const workTime = formatDuration(entry.work_minutes || 0);
    const desc = escapeHtml(entry.description || '');
    return `
        <div class="entry-card" data-id="${entry.id}">
            <div class="entry-info">
                <div class="entry-time">
                    ${escapeHtml((entry.start_time || '').slice(0, 5))} - ${escapeHtml((entry.end_time || '').slice(0, 5))}
                    <span class="entry-duration">(${workTime})</span>
                </div>
                ${desc ? `<div class="entry-description">${desc}</div>` : ''}
                ${entry.break_minutes > 0 ? `<div class="entry-break">☕ ${entry.break_minutes} min</div>` : ''}
            </div>
            <div class="entry-actions">
                <button class="edit-entry-btn" data-id="${entry.id}" title="${t('editTitle')}">✏️</button>
                <button class="delete-entry-btn" data-id="${entry.id}" title="${t('deleteTitle')}">🗑️</button>
            </div>
        </div>
    `;
}
