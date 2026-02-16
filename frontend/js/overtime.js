/* ==========================================
   Overtime Module
   ========================================== */
import { api } from './api.js';
import { t } from './i18n.js';
import { formatDuration, formatDate, escapeHtml, showToast, openModal, closeModal } from './utils.js';

export async function renderOvertimeTab() {
    await Promise.all([renderOvertimeBalance(), renderOvertimeHistory()]);
}

async function renderOvertimeBalance() {
    const balanceEl = document.getElementById('overtimeBalanceValue');
    if (!balanceEl) return;

    try {
        const data = await api.getOvertimeBalance();
        const minutes = data?.balance_minutes ?? 0;
        balanceEl.textContent = formatDuration(minutes);
        balanceEl.className = `overtime-balance-value ${minutes >= 0 ? 'positive' : 'negative'}`;

        // Disable use-overtime button when balance <= 0
        const useBtn = document.getElementById('useOvertimeBtn');
        if (useBtn) {
            useBtn.disabled = minutes <= 0;
            useBtn.title = minutes <= 0 ? (t('noOvertimeAvailable') || 'Kein Überstundenguthaben vorhanden') : '';
        }
    } catch (err) {
        balanceEl.textContent = '--:--';
    }
}

async function renderOvertimeHistory() {
    const container = document.getElementById('overtimeHistoryList');
    if (!container) return;

    try {
        const history = await api.getOvertimeHistory({ limit: 50 });
        if (!history || history.length === 0) {
            container.innerHTML = `<p class="no-entries">${t('noData')}</p>`;
            return;
        }
        container.innerHTML = history.map(item => {
            const isPositive = item.minutes > 0;
            const icon = item.reason === 'earned' ? '📈' : item.reason === 'used' ? '📉' : '🔧';
            const reasonLabel = t(`overtime${item.reason.charAt(0).toUpperCase() + item.reason.slice(1)}`);
            return `
                <div class="overtime-item ${isPositive ? 'positive' : 'negative'}">
                    <div class="overtime-item-left">
                        <span class="overtime-icon">${icon}</span>
                        <div>
                            <div class="overtime-reason">${escapeHtml(reasonLabel)}</div>
                            <div class="overtime-date">${escapeHtml(item.date)}</div>
                            ${item.note ? `<div class="overtime-note">${escapeHtml(item.note)}</div>` : ''}
                        </div>
                    </div>
                    <div class="overtime-item-right">
                        <div class="overtime-minutes ${isPositive ? 'text-success' : 'text-danger'}">
                            ${isPositive ? '+' : ''}${formatDuration(item.minutes)}
                        </div>
                        <button class="delete-overtime-btn icon-btn-sm" data-id="${item.id}" title="${t('delete') || 'Löschen'}">🗑️</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = `<p class="no-entries">${t('error')}</p>`;
    }
}

export function openUseOvertimeModal() {
    const form = document.getElementById('useOvertimeForm');
    if (form) form.reset();
    openModal('useOvertimeModal');
}

export async function submitUseOvertime() {
    const dateEl = document.getElementById('otUseDate');
    const minEl = document.getElementById('otUseMinutes');
    const noteEl = document.getElementById('otUseNote');

    const date = dateEl?.value;
    const minutes = parseInt(minEl?.value) || 0;
    const note = noteEl?.value || '';

    if (!date || minutes <= 0) {
        showToast(t('errorFillAllFields'), 'error');
        return;
    }

    try {
        await api.useOvertime({ date, minutes, note });
        closeModal('useOvertimeModal');
        showToast(t('success'), 'success');
        renderOvertimeTab();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ===== Absences Section =====
export async function renderAbsencesSection() {
    await Promise.all([renderVacationBudget(), renderAbsencesList()]);
}

async function renderVacationBudget() {
    const container = document.getElementById('vacationBudgetDisplay');
    if (!container) return;

    try {
        const year = new Date().getFullYear();
        const budget = await api.getVacationBudget(year);
        container.innerHTML = `
            <div class="budget-cards">
                <div class="budget-card">
                    <span class="budget-value">${budget.total_days ?? 30}</span>
                    <span class="budget-label">${t('totalDays')}</span>
                </div>
                <div class="budget-card">
                    <span class="budget-value">${budget.used_days ?? 0}</span>
                    <span class="budget-label">${t('usedDays')}</span>
                </div>
                <div class="budget-card accent">
                    <span class="budget-value">${(budget.total_days ?? 30) - (budget.used_days ?? 0)}</span>
                    <span class="budget-label">${t('remainingDays')}</span>
                </div>
            </div>
        `;
    } catch (_) {
        container.innerHTML = `<p class="no-entries">${t('noData')}</p>`;
    }
}

async function renderAbsencesList() {
    const container = document.getElementById('absencesList');
    if (!container) return;

    try {
        const year = new Date().getFullYear();
        const absences = await api.getAbsences({ year });
        if (!absences || absences.length === 0) {
            container.innerHTML = `<p class="no-entries">${t('noData')}</p>`;
            return;
        }
        container.innerHTML = absences.map(a => {
            const typeEmoji = a.type === 'urlaub' ? '🏖️' : a.type === 'krank' ? '🤒' : '📋';
            const typeLabel = a.type === 'urlaub' ? t('vacation') : a.type === 'krank' ? t('sick') : t('specialLeave');
            return `
                <div class="absence-item">
                    <span class="absence-emoji">${typeEmoji}</span>
                    <div class="absence-info">
                        <span class="absence-type">${escapeHtml(typeLabel)}</span>
                        <span class="absence-date">${escapeHtml(a.date)}</span>
                    </div>
                    <button class="delete-absence-btn icon-btn-sm" data-id="${a.id}" title="${t('delete')}">🗑️</button>
                </div>
            `;
        }).join('');
    } catch (_) {
        container.innerHTML = `<p class="no-entries">${t('error')}</p>`;
    }
}

export function openAddAbsenceModal() {
    const form = document.getElementById('addAbsenceForm');
    if (form) form.reset();
    openModal('addAbsenceModal');
}

export async function submitAddAbsence() {
    const dateEl = document.getElementById('absDate');
    const typeEl = document.getElementById('absType');

    const date = dateEl?.value;
    const absenceType = typeEl?.value;

    if (!date || !absenceType) {
        showToast(t('errorFillAllFields'), 'error');
        return;
    }

    try {
        await api.createAbsence({ date, type: absenceType });
        closeModal('addAbsenceModal');
        showToast(t('success'), 'success');
        renderAbsencesSection();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

export async function deleteAbsence(id) {
    try {
        await api.deleteAbsence(id);
        showToast(t('entryDeleted'), 'success');
        renderAbsencesSection();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

export async function deleteOvertimeEntry(id) {
    try {
        await api.deleteOvertimeEntry(id);
        showToast(t('entryDeleted') || 'Gelöscht', 'success');
        await renderOvertimeTab();
    } catch (err) {
        showToast(err.message, 'error');
    }
}
