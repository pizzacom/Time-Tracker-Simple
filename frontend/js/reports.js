/* ==========================================
   Reports Module
   ========================================== */
import { api } from './api.js';
import { t, getMonthName } from './i18n.js';
import { formatDate, formatDuration, escapeHtml, showToast } from './utils.js';

let reportMonth = new Date();

export function getReportMonth() { return reportMonth; }

export async function renderReport() {
    const year = reportMonth.getFullYear();
    const month = reportMonth.getMonth() + 1;

    const monthTitle = document.getElementById('reportMonth');
    if (monthTitle) monthTitle.textContent = `${getMonthName(reportMonth)} ${reportMonth.getFullYear()}`;

    try {
        const report = await api.getMonthlyReport(year, month);
        if (!report) return;

        document.getElementById('totalDays').textContent = report.work_days ?? 0;
        document.getElementById('totalHours').textContent = formatDuration(report.ist_total ?? 0);

        // Calculate total breaks from day entries
        let totalBreakMin = 0;
        if (report.days) {
            report.days.forEach(day => {
                (day.entries || []).forEach(e => { totalBreakMin += e.break_minutes || 0; });
            });
        }
        document.getElementById('totalBreaks').textContent = formatDuration(totalBreakMin);

        const avgMin = report.work_days ? Math.round((report.ist_total ?? 0) / report.work_days) : 0;
        document.getElementById('avgHours').textContent = formatDuration(avgMin);

        // Overtime summary
        const otEl = document.getElementById('reportOvertimeSummary');
        if (otEl) {
            const sollTotal = report.soll_total ?? 0;
            const istTotal = report.ist_total ?? 0;
            const delta = report.delta_total ?? (istTotal - sollTotal);
            const otEarned = report.overtime_earned ?? 0;
            const otUsed = report.overtime_used ?? 0;
            const otBalance = report.overtime_balance ?? 0;
            otEl.innerHTML = `
                <div class="summary-card">
                    <span class="summary-icon">🎯</span>
                    <div class="summary-content">
                        <span class="summary-value">${formatDuration(sollTotal)}</span>
                        <span class="summary-label">${t('sollMinutes')}</span>
                    </div>
                </div>
                <div class="summary-card">
                    <span class="summary-icon">${delta >= 0 ? '📈' : '📉'}</span>
                    <div class="summary-content">
                        <span class="summary-value ${delta >= 0 ? 'text-success' : 'text-danger'}">${formatDuration(delta)}</span>
                        <span class="summary-label">${t('delta')}</span>
                    </div>
                </div>
                <div class="summary-card">
                    <span class="summary-icon">⏰</span>
                    <div class="summary-content">
                        <span class="summary-value ${otBalance >= 0 ? 'text-success' : 'text-danger'}">${formatDuration(otBalance)}</span>
                        <span class="summary-label">${t('overtimeBalance')}</span>
                    </div>
                </div>
            `;
        }

        // Render table
        const tbody = document.getElementById('reportTableBody');
        if (tbody && report.days) {
            if (report.days.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">${t('noEntries')}</td></tr>`;
            } else {
                tbody.innerHTML = report.days.map(day => {
                    const entries = day.entries || [];
                    if (entries.length === 0) {
                        const typeLabel = day.absence_type || (day.is_holiday ? '🎄' : '');
                        return `<tr class="day-no-entries">
                            <td>${escapeHtml(day.date)}</td>
                            <td colspan="3" style="text-align:center;color:var(--text-muted)">${typeLabel || '-'}</td>
                            <td>${formatDuration(day.soll_minutes || 0)}</td>
                            <td>0:00</td>
                            <td>${formatDuration(day.delta_minutes || 0)}</td>
                        </tr>`;
                    }
                    return entries.map((e, i) => `
                        <tr>
                            ${i === 0 ? `<td rowspan="${entries.length}">${escapeHtml(day.date)}</td>` : ''}
                            <td>${escapeHtml((e.start_time || '').slice(0, 5))}</td>
                            <td>${escapeHtml((e.end_time || '').slice(0, 5))}</td>
                            <td>${e.break_minutes} min</td>
                            ${i === 0 ? `
                                <td rowspan="${entries.length}">${formatDuration(day.soll_minutes || 0)}</td>
                                <td rowspan="${entries.length}">${formatDuration(day.ist_minutes || 0)}</td>
                                <td rowspan="${entries.length}" class="${(day.delta_minutes || 0) >= 0 ? 'text-success' : 'text-danger'}">${formatDuration(day.delta_minutes || 0)}</td>
                            ` : ''}
                        </tr>
                    `).join('');
                }).join('');
            }
        }
    } catch (err) {
        console.error('Report error:', err);
        const tbody = document.getElementById('reportTableBody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="7">${t('error')}</td></tr>`;
    }
}

export function changeReportMonth(delta) {
    reportMonth.setMonth(reportMonth.getMonth() + delta);
    renderReport();
}

export async function exportPdf() {
    try {
        const year = reportMonth.getFullYear();
        const month = reportMonth.getMonth() + 1;
        await api.downloadPdf(year, month);
        showToast(t('dataExported'), 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

export async function exportExcel() {
    try {
        const year = reportMonth.getFullYear();
        const month = reportMonth.getMonth() + 1;
        await api.downloadExcel(year, month);
        showToast(t('dataExported'), 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

export async function exportCsv() {
    try {
        const year = reportMonth.getFullYear();
        const month = reportMonth.getMonth() + 1;
        await api.downloadCsv(year, month);
        showToast(t('dataExported'), 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}
