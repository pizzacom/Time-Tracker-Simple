/* ==========================================
   Calendar Module
   ========================================== */
import { api } from './api.js';
import { t, getMonthName } from './i18n.js';
import { formatDateISO, formatDate, escapeHtml } from './utils.js';
import { createEntryCard } from './timer.js';

let calendarMonth = new Date();
let selectedDate = null;
let _renderInProgress = false;

export function getCalendarMonth() { return calendarMonth; }
export function getSelectedDate() { return selectedDate; }
export function setSelectedDate(d) { selectedDate = d; }

export async function renderCalendar() {
    // Guard against concurrent renders
    if (_renderInProgress) return;
    _renderInProgress = true;

    try {
        const year = calendarMonth.getFullYear();
        const month = calendarMonth.getMonth();

        const monthTitle = document.getElementById('currentMonth');
        if (monthTitle) monthTitle.textContent = `${getMonthName(calendarMonth)} ${year}`;

        const container = document.getElementById('calendarDays');
        if (!container) return;

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const totalDays = lastDay.getDate();

        let startWeekday = firstDay.getDay() - 1;
        if (startWeekday < 0) startWeekday = 6;

        // Fetch entries and holidays for the month
        let daysWithEntries = new Set();
        let holidayDates = new Map(); // date string -> {name, is_half_day}
        try {
            const from = `${year}-${String(month + 1).padStart(2, '0')}-01`;
            const to = `${year}-${String(month + 1).padStart(2, '0')}-${String(totalDays).padStart(2, '0')}`;
            const [entries, holidays] = await Promise.all([
                api.getEntries({ date_from: from, date_to: to }).catch(() => []),
                api.getHolidays(year).catch(() => []),
            ]);
            if (entries) {
                entries.forEach(e => {
                    const day = parseInt(e.date.split('-')[2]);
                    daysWithEntries.add(day);
                });
            }
            if (holidays) {
                holidays.forEach(h => {
                    holidayDates.set(h.date, { name: h.name, is_half_day: h.is_half_day });
                });
            }
        } catch (_) {}

        const todayStr = formatDateISO(new Date());

        // Build new content in a document fragment to avoid flicker
        const fragment = document.createDocumentFragment();

        // Empty cells before first of month
        const prevMonth = new Date(year, month, 0);
        for (let i = 0; i < startWeekday; i++) {
            const day = prevMonth.getDate() - startWeekday + i + 1;
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day other-month';
            dayEl.textContent = day;
            fragment.appendChild(dayEl);
        }

        // Days of current month
        for (let day = 1; day <= totalDays; day++) {
            const dateStr = formatDateISO(new Date(year, month, day));
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day';
            dayEl.dataset.date = dateStr;

            const dayNum = document.createElement('span');
            dayNum.className = 'calendar-day-num';
            dayNum.textContent = day;
            dayEl.appendChild(dayNum);

            if (dateStr === todayStr) dayEl.classList.add('today');
            if (dateStr === selectedDate) dayEl.classList.add('selected');
            if (daysWithEntries.has(day)) dayEl.classList.add('has-entries');

            // Holiday marker
            const holiday = holidayDates.get(dateStr);
            if (holiday) {
                dayEl.classList.add('is-holiday');
                if (holiday.is_half_day) dayEl.classList.add('is-half-day');
                dayEl.title = holiday.name;
            }

            dayEl.onclick = () => selectDate(dateStr);
            fragment.appendChild(dayEl);
        }

        // Fill remaining cells
        const totalCells = startWeekday + totalDays;
        const remain = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
        for (let i = 1; i <= remain; i++) {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day other-month';
            dayEl.textContent = i;
            fragment.appendChild(dayEl);
        }

        // Swap content in one shot
        container.innerHTML = '';
        container.appendChild(fragment);
    } finally {
        _renderInProgress = false;
    }
}

export function selectDate(dateStr) {
    selectedDate = dateStr;
    const date = new Date(dateStr);
    const title = document.getElementById('selectedDateTitle');
    if (title) title.textContent = formatDate(date);

    const entryDate = document.getElementById('entryDate');
    if (entryDate) entryDate.value = dateStr;

    // Just update the selected highlight — no full re-render
    document.querySelectorAll('#calendarDays .calendar-day').forEach(el => {
        el.classList.toggle('selected', el.dataset.date === dateStr);
    });

    renderSelectedDateEntries();
}

export async function renderSelectedDateEntries() {
    const container = document.getElementById('selectedDateEntries');
    if (!container || !selectedDate) return;

    try {
        const entries = await api.getEntries({ date_from: selectedDate, date_to: selectedDate });
        if (!entries || entries.length === 0) {
            container.innerHTML = `<p class="no-entries">${t('noEntries')}</p>`;
            return;
        }
        container.innerHTML = entries.map(e => createEntryCard(e)).join('');
    } catch (err) {
        container.innerHTML = `<p class="no-entries">${t('error')}</p>`;
    }
}

export function changeMonth(delta) {
    calendarMonth.setMonth(calendarMonth.getMonth() + delta);
    renderCalendar();
}
