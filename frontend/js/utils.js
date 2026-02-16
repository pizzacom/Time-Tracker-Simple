/* ==========================================
   Utils Module - Shared Utility Functions
   ========================================== */

export function generateId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}

export function formatTime(date) {
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}

export function formatDate(date) {
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function formatDateISO(date) {
    const y = date.getFullYear();
    const m = (date.getMonth() + 1).toString().padStart(2, '0');
    const d = date.getDate().toString().padStart(2, '0');
    return `${y}-${m}-${d}`;
}

export function formatDuration(minutes) {
    const h = Math.floor(Math.abs(minutes) / 60);
    const m = Math.round(Math.abs(minutes) % 60);
    const sign = minutes < 0 ? '-' : '';
    return `${sign}${h}:${m.toString().padStart(2, '0')}`;
}

export function formatTimerDisplay(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

export function parseTimeToMinutes(timeStr) {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
}

export function calculateWorkMinutes(startTime, endTime, breakMinutes) {
    return Math.max(0, parseTimeToMinutes(endTime) - parseTimeToMinutes(startTime) - breakMinutes);
}

export function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

export function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-message">${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

export function openModal(modalId) {
    document.getElementById(modalId)?.classList.add('active');
}

export function closeModal(modalId) {
    document.getElementById(modalId)?.classList.remove('active');
}

export function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
}

// LocalStorage helpers (for non-auth state: theme, language, etc.)
export function saveLocal(key, data) {
    try { localStorage.setItem(`zeittracker_${key}`, JSON.stringify(data)); } catch (_) {}
}

export function loadLocal(key, defaultValue = null) {
    try {
        const d = localStorage.getItem(`zeittracker_${key}`);
        return d ? JSON.parse(d) : defaultValue;
    } catch (_) { return defaultValue; }
}

export function getWeekdayShort(dateStr, lang = 'de') {
    const days = lang === 'de'
        ? ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.']
        : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const [y, m, d] = dateStr.split('-').map(Number);
    return days[new Date(y, m - 1, d).getDay()];
}
