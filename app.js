/* ==========================================
   Zeit Tracking App - JavaScript
   ========================================== */

// ==========================================
// Translations
// ==========================================
const translations = {
    de: {
        appTitle: 'Zeit Tracking',
        tabTimer: 'Timer',
        tabCalendar: 'Kalender',
        tabReports: 'Berichte',
        tabData: 'Daten',
        timerStopped: 'Gestoppt',
        timerRunning: 'Läuft...',
        start: 'Start',
        stop: 'Stop',
        reset: 'Zurücksetzen',
        startedAt: 'Gestartet um:',
        todayEntries: 'Heutige Einträge',
        noEntries: 'Keine Einträge vorhanden',
        selectDate: 'Datum auswählen',
        selectDateHint: 'Klicken Sie auf ein Datum im Kalender',
        addEntry: 'Eintrag hinzufügen',
        editEntry: 'Eintrag bearbeiten',
        date: 'Datum',
        startTime: 'Startzeit',
        endTime: 'Endzeit',
        breakTime: 'Pause',
        breakMinutes: 'Pause (Minuten)',
        workTime: 'Arbeitszeit',
        description: 'Beschreibung',
        workDays: 'Arbeitstage',
        totalHours: 'Gesamtstunden',
        totalBreaks: 'Pausenzeit',
        avgPerDay: 'Ø pro Tag',
        exportPdf: 'PDF exportieren',
        exportData: 'Daten exportieren',
        exportDescription: 'Exportieren Sie Ihre Zeitdaten als Backup oder zur Verwendung in anderen Anwendungen.',
        exportJson: 'JSON exportieren',
        exportCsv: 'CSV exportieren',
        importData: 'Daten importieren',
        importDescription: 'Importieren Sie Zeitdaten aus einer JSON-Datei.',
        mergeMode: 'Zusammenführen (Duplikate vermeiden)',
        replaceMode: 'Ersetzen (alle Daten überschreiben)',
        selectFile: 'Datei auswählen',
        noFileSelected: 'Keine Datei ausgewählt',
        importBtn: 'Importieren',
        dangerZone: 'Gefahrenzone',
        deleteWarning: 'Achtung: Diese Aktion kann nicht rückgängig gemacht werden!',
        deleteAll: 'Alle Daten löschen',
        settings: 'Einstellungen',
        userName: 'Name',
        userNamePlaceholder: 'Ihr Name',
        companyName: 'Firma',
        companyPlaceholder: 'Firmenname (optional)',
        defaultBreak: 'Standard-Pausenzeit (Minuten)',
        cancel: 'Abbrechen',
        save: 'Speichern',
        confirm: 'Bestätigen',
        delete: 'Löschen',
        taskPlaceholder: 'Aufgabenbeschreibung (optional)',
        descriptionPlaceholder: 'Beschreibung (optional)',
        confirmDelete: 'Möchten Sie diesen Eintrag wirklich löschen?',
        confirmDeleteAll: 'Möchten Sie wirklich ALLE Daten löschen? Diese Aktion kann nicht rückgängig gemacht werden!',
        confirmReplace: 'Möchten Sie wirklich alle bestehenden Daten ersetzen?',
        entrySaved: 'Eintrag gespeichert',
        entryDeleted: 'Eintrag gelöscht',
        settingsSaved: 'Einstellungen gespeichert',
        dataExported: 'Daten exportiert',
        dataImported: 'Daten importiert',
        dataDeleted: 'Alle Daten gelöscht',
        importError: 'Fehler beim Importieren',
        invalidFile: 'Ungültige Datei',
        timerSaved: 'Zeiterfassung gespeichert',
        weekdayMo: 'Mo',
        weekdayTu: 'Di',
        weekdayWe: 'Mi',
        weekdayTh: 'Do',
        weekdayFr: 'Fr',
        weekdaySa: 'Sa',
        weekdaySu: 'So',
        months: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
        pdfTitle: 'Zeiterfassungsbericht',
        pdfGeneratedOn: 'Erstellt am',
        pdfPeriod: 'Zeitraum',
        pdfTotalWorktime: 'Gesamtarbeitszeit',
        pdfTotalBreaks: 'Gesamtpausen',
        pdfWorkdays: 'Arbeitstage',
        noEntriesForMonth: 'Keine Einträge für diesen Monat',
        hours: 'Stunden',
        minutes: 'Minuten'
    },
    en: {
        appTitle: 'Time Tracking',
        tabTimer: 'Timer',
        tabCalendar: 'Calendar',
        tabReports: 'Reports',
        tabData: 'Data',
        timerStopped: 'Stopped',
        timerRunning: 'Running...',
        start: 'Start',
        stop: 'Stop',
        reset: 'Reset',
        startedAt: 'Started at:',
        todayEntries: "Today's Entries",
        noEntries: 'No entries available',
        selectDate: 'Select Date',
        selectDateHint: 'Click on a date in the calendar',
        addEntry: 'Add Entry',
        editEntry: 'Edit Entry',
        date: 'Date',
        startTime: 'Start Time',
        endTime: 'End Time',
        breakTime: 'Break',
        breakMinutes: 'Break (Minutes)',
        workTime: 'Work Time',
        description: 'Description',
        workDays: 'Work Days',
        totalHours: 'Total Hours',
        totalBreaks: 'Break Time',
        avgPerDay: 'Avg per Day',
        exportPdf: 'Export PDF',
        exportData: 'Export Data',
        exportDescription: 'Export your time data as backup or for use in other applications.',
        exportJson: 'Export JSON',
        exportCsv: 'Export CSV',
        importData: 'Import Data',
        importDescription: 'Import time data from a JSON file.',
        mergeMode: 'Merge (avoid duplicates)',
        replaceMode: 'Replace (overwrite all data)',
        selectFile: 'Select File',
        noFileSelected: 'No file selected',
        importBtn: 'Import',
        dangerZone: 'Danger Zone',
        deleteWarning: 'Warning: This action cannot be undone!',
        deleteAll: 'Delete All Data',
        settings: 'Settings',
        userName: 'Name',
        userNamePlaceholder: 'Your name',
        companyName: 'Company',
        companyPlaceholder: 'Company name (optional)',
        defaultBreak: 'Default Break Time (Minutes)',
        cancel: 'Cancel',
        save: 'Save',
        confirm: 'Confirm',
        delete: 'Delete',
        taskPlaceholder: 'Task description (optional)',
        descriptionPlaceholder: 'Description (optional)',
        confirmDelete: 'Do you really want to delete this entry?',
        confirmDeleteAll: 'Do you really want to delete ALL data? This action cannot be undone!',
        confirmReplace: 'Do you really want to replace all existing data?',
        entrySaved: 'Entry saved',
        entryDeleted: 'Entry deleted',
        settingsSaved: 'Settings saved',
        dataExported: 'Data exported',
        dataImported: 'Data imported',
        dataDeleted: 'All data deleted',
        importError: 'Error importing data',
        invalidFile: 'Invalid file',
        timerSaved: 'Time entry saved',
        weekdayMo: 'Mo',
        weekdayTu: 'Tu',
        weekdayWe: 'We',
        weekdayTh: 'Th',
        weekdayFr: 'Fr',
        weekdaySa: 'Sa',
        weekdaySu: 'Su',
        months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        pdfTitle: 'Time Tracking Report',
        pdfGeneratedOn: 'Generated on',
        pdfPeriod: 'Period',
        pdfTotalWorktime: 'Total Work Time',
        pdfTotalBreaks: 'Total Breaks',
        pdfWorkdays: 'Work Days',
        noEntriesForMonth: 'No entries for this month',
        hours: 'hours',
        minutes: 'minutes'
    }
};

// ==========================================
// App State
// ==========================================
const state = {
    language: 'de',
    theme: 'light',
    settings: {
        userName: '',
        companyName: '',
        defaultBreak: 30
    },
    timer: {
        isRunning: false,
        startTime: null,
        elapsed: 0,
        description: ''
    },
    entries: [],
    selectedDate: null,
    calendarMonth: new Date(),
    reportMonth: new Date(),
    editingEntryId: null
};

// ==========================================
// Utility Functions
// ==========================================
function generateId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function formatTime(date) {
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(date) {
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatDateISO(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatDuration(minutes) {
    const h = Math.floor(minutes / 60);
    const m = Math.round(minutes % 60);
    return `${h}:${m.toString().padStart(2, '0')}`;
}

function formatTimerDisplay(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function parseTimeToMinutes(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
}

function calculateWorkMinutes(startTime, endTime, breakMinutes) {
    const startMinutes = parseTimeToMinutes(startTime);
    const endMinutes = parseTimeToMinutes(endTime);
    return Math.max(0, endMinutes - startMinutes - breakMinutes);
}

function t(key) {
    return translations[state.language][key] || key;
}

function getMonthName(date) {
    return t('months')[date.getMonth()];
}

// ==========================================
// LocalStorage Functions
// ==========================================
function saveToStorage(key, data) {
    try {
        localStorage.setItem(`zeittracking_${key}`, JSON.stringify(data));
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(`zeittracking_${key}`);
        return data ? JSON.parse(data) : defaultValue;
    } catch (e) {
        console.error('Error loading from localStorage:', e);
        return defaultValue;
    }
}

function loadState() {
    state.language = loadFromStorage('language', 'de');
    state.theme = loadFromStorage('theme', 'light');
    state.settings = loadFromStorage('settings', state.settings);
    state.entries = loadFromStorage('entries', []);
    state.timer = loadFromStorage('timer', state.timer);
    
    // Restore timer state
    if (state.timer.isRunning && state.timer.startTime) {
        state.timer.startTime = new Date(state.timer.startTime);
    }
}

function saveState() {
    saveToStorage('language', state.language);
    saveToStorage('theme', state.theme);
    saveToStorage('settings', state.settings);
    saveToStorage('entries', state.entries);
    saveToStorage('timer', state.timer);
}

// ==========================================
// UI Functions
// ==========================================
function updateTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[state.language][key]) {
            el.textContent = translations[state.language][key];
        }
    });
    
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[state.language][key]) {
            el.placeholder = translations[state.language][key];
        }
    });
}

function updateTheme() {
    document.body.setAttribute('data-theme', state.theme);
    document.getElementById('themeIcon').textContent = state.theme === 'light' ? '🌙' : '☀️';
}

function updateLanguageIcon() {
    document.getElementById('langIcon').textContent = state.language === 'de' ? '🇩🇪' : '🇬🇧';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-message">${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
}

// ==========================================
// Tab Navigation
// ==========================================
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Refresh content based on tab
    if (tabName === 'calendar') {
        renderCalendar();
    } else if (tabName === 'reports') {
        renderReport();
    } else if (tabName === 'timer') {
        renderTodayEntries();
    }
}

// ==========================================
// Timer Functions
// ==========================================
let timerInterval = null;

function startTimer() {
    state.timer.isRunning = true;
    state.timer.startTime = new Date();
    state.timer.description = document.getElementById('taskDescription').value;
    state.timer.elapsed = 0;
    saveState();
    
    updateTimerUI();
    timerInterval = setInterval(updateTimerDisplay, 1000);
}

function stopTimer() {
    if (!state.timer.isRunning) return;
    
    clearInterval(timerInterval);
    
    const endTime = new Date();
    const startTime = new Date(state.timer.startTime);
    const durationMs = endTime - startTime;
    const durationMinutes = Math.round(durationMs / 60000);
    
    // Create entry
    const entry = {
        id: generateId(),
        date: formatDateISO(startTime),
        startTime: formatTime(startTime),
        endTime: formatTime(endTime),
        breakMinutes: 0,
        description: state.timer.description,
        workMinutes: durationMinutes
    };
    
    state.entries.push(entry);
    
    // Reset timer
    state.timer.isRunning = false;
    state.timer.startTime = null;
    state.timer.elapsed = 0;
    state.timer.description = '';
    
    saveState();
    updateTimerUI();
    renderTodayEntries();
    showToast(t('timerSaved'), 'success');
}

function resetTimer() {
    clearInterval(timerInterval);
    state.timer.isRunning = false;
    state.timer.startTime = null;
    state.timer.elapsed = 0;
    document.getElementById('taskDescription').value = '';
    saveState();
    updateTimerUI();
}

function updateTimerDisplay() {
    if (!state.timer.isRunning || !state.timer.startTime) return;
    
    const now = Date.now();
    const start = new Date(state.timer.startTime).getTime();
    const elapsed = now - start;
    
    document.getElementById('timerTime').textContent = formatTimerDisplay(elapsed);
}

function updateTimerUI() {
    const startStopBtn = document.getElementById('startStopBtn');
    const startStopIcon = document.getElementById('startStopIcon');
    const startStopText = document.getElementById('startStopText');
    const resetBtn = document.getElementById('resetBtn');
    const timerStatus = document.getElementById('timerStatus');
    const timerInfo = document.getElementById('timerInfo');
    const startTimeDisplay = document.getElementById('startTimeDisplay');
    
    if (state.timer.isRunning) {
        startStopIcon.textContent = '⏹️';
        startStopText.textContent = t('stop');
        startStopBtn.classList.remove('btn-primary');
        startStopBtn.classList.add('btn-danger');
        resetBtn.disabled = false;
        timerStatus.textContent = t('timerRunning');
        timerInfo.classList.remove('hidden');
        startTimeDisplay.textContent = formatTime(new Date(state.timer.startTime));
        
        // Restore timer interval
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
        document.getElementById('timerTime').textContent = '00:00:00';
    }
}

// ==========================================
// Entries Functions
// ==========================================
function renderTodayEntries() {
    const today = formatDateISO(new Date());
    const todayEntries = state.entries.filter(e => e.date === today);
    const container = document.getElementById('todayEntriesList');
    
    if (todayEntries.length === 0) {
        container.innerHTML = `<p class="no-entries">${t('noEntries')}</p>`;
        return;
    }
    
    container.innerHTML = todayEntries.map(entry => createEntryCard(entry)).join('');
}

function renderSelectedDateEntries() {
    if (!state.selectedDate) return;
    
    const dateEntries = state.entries.filter(e => e.date === state.selectedDate);
    const container = document.getElementById('selectedDateEntries');
    
    if (dateEntries.length === 0) {
        container.innerHTML = `<p class="no-entries">${t('noEntries')}</p>`;
        return;
    }
    
    container.innerHTML = dateEntries.map(entry => createEntryCard(entry)).join('');
}

function createEntryCard(entry) {
    const workTime = formatDuration(entry.workMinutes || calculateWorkMinutes(entry.startTime, entry.endTime, entry.breakMinutes));
    
    return `
        <div class="entry-card" data-id="${entry.id}">
            <div class="entry-info">
                <div class="entry-time">
                    ${entry.startTime} - ${entry.endTime}
                    <span class="entry-duration">(${workTime})</span>
                </div>
                ${entry.description ? `<div class="entry-description">${entry.description}</div>` : ''}
                ${entry.breakMinutes > 0 ? `<div class="entry-break">☕ ${entry.breakMinutes} min</div>` : ''}
            </div>
            <div class="entry-actions">
                <button onclick="editEntry('${entry.id}')" title="Bearbeiten">✏️</button>
                <button onclick="confirmDeleteEntry('${entry.id}')" title="Löschen">🗑️</button>
            </div>
        </div>
    `;
}

function editEntry(id) {
    const entry = state.entries.find(e => e.id === id);
    if (!entry) return;
    
    state.editingEntryId = id;
    
    document.getElementById('entryModalTitle').textContent = t('editEntry');
    document.getElementById('entryDate').value = entry.date;
    setTimePickerValue('entryStart', entry.startTime);
    setTimePickerValue('entryEnd', entry.endTime);
    syncTimeInputs();
    document.getElementById('entryBreak').value = entry.breakMinutes;
    document.getElementById('entryDescription').value = entry.description || '';
    
    openModal('entryModal');
}

function saveEntry() {
    const date = document.getElementById('entryDate').value;
    const startTime = document.getElementById('entryStart').value;
    const endTime = document.getElementById('entryEnd').value;
    const breakMinutes = parseInt(document.getElementById('entryBreak').value) || 0;
    const description = document.getElementById('entryDescription').value;
    
    if (!date || !startTime || !endTime) {
        showToast('Bitte füllen Sie alle Pflichtfelder aus', 'error');
        return;
    }
    
    const workMinutes = calculateWorkMinutes(startTime, endTime, breakMinutes);
    
    if (state.editingEntryId) {
        // Update existing entry
        const index = state.entries.findIndex(e => e.id === state.editingEntryId);
        if (index !== -1) {
            state.entries[index] = {
                ...state.entries[index],
                date,
                startTime,
                endTime,
                breakMinutes,
                description,
                workMinutes
            };
        }
        state.editingEntryId = null;
    } else {
        // Create new entry
        state.entries.push({
            id: generateId(),
            date,
            startTime,
            endTime,
            breakMinutes,
            description,
            workMinutes
        });
    }
    
    saveState();
    closeModal('entryModal');
    renderTodayEntries();
    renderSelectedDateEntries();
    renderCalendar();
    showToast(t('entrySaved'), 'success');
}

function confirmDeleteEntry(id) {
    state.editingEntryId = id;
    document.getElementById('confirmMessage').textContent = t('confirmDelete');
    document.getElementById('confirmAction').onclick = () => deleteEntry(id);
    openModal('confirmModal');
}

function deleteEntry(id) {
    state.entries = state.entries.filter(e => e.id !== id);
    state.editingEntryId = null;
    saveState();
    closeModal('confirmModal');
    renderTodayEntries();
    renderSelectedDateEntries();
    renderCalendar();
    showToast(t('entryDeleted'), 'success');
}

// ==========================================
// Calendar Functions
// ==========================================
function renderCalendar() {
    const year = state.calendarMonth.getFullYear();
    const month = state.calendarMonth.getMonth();
    
    // Update month title
    document.getElementById('currentMonth').textContent = `${getMonthName(state.calendarMonth)} ${year}`;
    
    const container = document.getElementById('calendarDays');
    container.innerHTML = '';
    
    // Get first day of month and total days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const totalDays = lastDay.getDate();
    
    // Get starting weekday (0 = Sunday, convert to Monday start)
    let startWeekday = firstDay.getDay() - 1;
    if (startWeekday < 0) startWeekday = 6;
    
    // Get entries for this month
    const monthEntries = state.entries.filter(e => {
        const [entryYear, entryMonth] = e.date.split('-').map(Number);
        return entryYear === year && (entryMonth - 1) === month;
    });
    
    const daysWithEntries = new Set(monthEntries.map(e => parseInt(e.date.split('-')[2])));
    
    const today = new Date();
    const todayStr = formatDateISO(today);
    
    // Add empty cells for days before first of month
    for (let i = 0; i < startWeekday; i++) {
        const prevMonth = new Date(year, month, 0);
        const day = prevMonth.getDate() - startWeekday + i + 1;
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day other-month';
        dayEl.textContent = day;
        container.appendChild(dayEl);
    }
    
    // Add days of current month
    for (let day = 1; day <= totalDays; day++) {
        const dateStr = formatDateISO(new Date(year, month, day));
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';
        dayEl.textContent = day;
        dayEl.dataset.date = dateStr;
        
        if (dateStr === todayStr) {
            dayEl.classList.add('today');
        }
        
        if (dateStr === state.selectedDate) {
            dayEl.classList.add('selected');
        }
        
        if (daysWithEntries.has(day)) {
            dayEl.classList.add('has-entries');
        }
        
        dayEl.onclick = () => selectDate(dateStr);
        container.appendChild(dayEl);
    }
    
    // Add empty cells to complete the grid
    const totalCells = startWeekday + totalDays;
    const remainingCells = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    
    for (let i = 1; i <= remainingCells; i++) {
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day other-month';
        dayEl.textContent = i;
        container.appendChild(dayEl);
    }
}

function selectDate(dateStr) {
    state.selectedDate = dateStr;
    
    // Update selected date title
    const date = new Date(dateStr);
    document.getElementById('selectedDateTitle').textContent = formatDate(date);
    
    // Set default date for new entry modal
    document.getElementById('entryDate').value = dateStr;
    
    renderCalendar();
    renderSelectedDateEntries();
}

function changeMonth(delta) {
    state.calendarMonth.setMonth(state.calendarMonth.getMonth() + delta);
    renderCalendar();
}

// ==========================================
// Reports Functions
// ==========================================
function renderReport() {
    const year = state.reportMonth.getFullYear();
    const month = state.reportMonth.getMonth();
    
    // Update month title
    document.getElementById('reportMonth').textContent = `${getMonthName(state.reportMonth)} ${year}`;
    
    // Filter entries for this month
    const monthEntries = state.entries.filter(e => {
        const entryDate = new Date(e.date);
        return entryDate.getFullYear() === year && entryDate.getMonth() === month;
    }).sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Calculate statistics
    const uniqueDays = new Set(monthEntries.map(e => e.date));
    const totalWorkMinutes = monthEntries.reduce((sum, e) => 
        sum + (e.workMinutes || calculateWorkMinutes(e.startTime, e.endTime, e.breakMinutes)), 0);
    const totalBreakMinutes = monthEntries.reduce((sum, e) => sum + (e.breakMinutes || 0), 0);
    const avgMinutes = uniqueDays.size > 0 ? totalWorkMinutes / uniqueDays.size : 0;
    
    // Update summary cards
    document.getElementById('totalDays').textContent = uniqueDays.size;
    document.getElementById('totalHours').textContent = formatDuration(totalWorkMinutes);
    document.getElementById('totalBreaks').textContent = formatDuration(totalBreakMinutes);
    document.getElementById('avgHours').textContent = formatDuration(avgMinutes);
    
    // Render table
    const tbody = document.getElementById('reportTableBody');
    
    if (monthEntries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">${t('noEntriesForMonth')}</td></tr>`;
        return;
    }
    
    tbody.innerHTML = monthEntries.map(entry => {
        const workMinutes = entry.workMinutes || calculateWorkMinutes(entry.startTime, entry.endTime, entry.breakMinutes);
        return `
            <tr>
                <td>${formatDate(new Date(entry.date))}</td>
                <td>${entry.startTime}</td>
                <td>${entry.endTime}</td>
                <td>${entry.breakMinutes} min</td>
                <td>${formatDuration(workMinutes)}</td>
                <td>${entry.description || '-'}</td>
            </tr>
        `;
    }).join('');
}

function changeReportMonth(delta) {
    state.reportMonth.setMonth(state.reportMonth.getMonth() + delta);
    renderReport();
}

// ==========================================
// PDF Export
// ==========================================
function getWeekdayShort(dateStr) {
    const days = state.language === 'de' 
        ? ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.']
        : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return days[date.getDay()];
}

function exportPdf() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    const year = state.reportMonth.getFullYear();
    const month = state.reportMonth.getMonth();
    const monthName = getMonthName(state.reportMonth);
    
    // Get all days in month
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    // Create entries map for quick lookup
    const entriesMap = {};
    state.entries.forEach(e => {
        const [entryYear, entryMonth] = e.date.split('-').map(Number);
        if (entryYear === year && (entryMonth - 1) === month) {
            entriesMap[e.date] = e;
        }
    });
    
    // Calculate totals
    const entriesArray = Object.values(entriesMap);
    const totalWorkMinutes = entriesArray.reduce((sum, e) => 
        sum + (e.workMinutes || calculateWorkMinutes(e.startTime, e.endTime, e.breakMinutes)), 0);
    const totalBreakMinutes = entriesArray.reduce((sum, e) => sum + (e.breakMinutes || 0), 0);
    const totalGrossMinutes = entriesArray.reduce((sum, e) => {
        const gross = parseTimeToMinutes(e.endTime) - parseTimeToMinutes(e.startTime);
        return sum + gross;
    }, 0);
    const workDays = entriesArray.length;
    
    // ===== HEADER =====
    doc.setFontSize(22);
    doc.setTextColor(40, 40, 40);
    doc.setFont(undefined, 'bold');
    doc.text('Zeiterfassung', 105, 18, { align: 'center' });
    
    doc.setFontSize(14);
    doc.setFont(undefined, 'normal');
    doc.setTextColor(80, 80, 80);
    doc.text(`${monthName} ${year}`, 105, 26, { align: 'center' });
    
    // User info line
    if (state.settings.userName || state.settings.companyName) {
        doc.setFontSize(10);
        doc.setTextColor(100, 100, 100);
        const userLine = [state.settings.userName, state.settings.companyName].filter(Boolean).join(' • ');
        doc.text(userLine, 105, 33, { align: 'center' });
    }
    
    // ===== TABLE =====
    const tableData = [];
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${(month + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        const entry = entriesMap[dateStr];
        const weekday = getWeekdayShort(dateStr);
        const dayStr = day.toString().padStart(2, '0') + '.' + (month + 1).toString().padStart(2, '0');
        
        if (entry) {
            const workMinutes = entry.workMinutes || calculateWorkMinutes(entry.startTime, entry.endTime, entry.breakMinutes);
            const totalMinutes = parseTimeToMinutes(entry.endTime) - parseTimeToMinutes(entry.startTime);
            tableData.push([
                dayStr,
                weekday,
                entry.startTime,
                entry.endTime,
                formatDuration(entry.breakMinutes),
                formatDuration(totalMinutes),
                formatDuration(workMinutes),
                entry.description || '–'
            ]);
        } else {
            tableData.push([dayStr, weekday, '–', '–', '–', '–', '–', '–']);
        }
    }
    
    // Summary row
    tableData.push([
        { content: 'Summe', styles: { fontStyle: 'bold', fillColor: [245, 245, 245] } },
        { content: '', styles: { fillColor: [245, 245, 245] } },
        { content: '', styles: { fillColor: [245, 245, 245] } },
        { content: '', styles: { fillColor: [245, 245, 245] } },
        { content: formatDuration(totalBreakMinutes), styles: { fontStyle: 'bold', fillColor: [245, 245, 245] } },
        { content: formatDuration(totalGrossMinutes), styles: { fontStyle: 'bold', fillColor: [245, 245, 245] } },
        { content: formatDuration(totalWorkMinutes), styles: { fontStyle: 'bold', fillColor: [245, 245, 245] } },
        { content: `${workDays}T • 0U • 0K`, styles: { fontStyle: 'bold', fillColor: [245, 245, 245], halign: 'left' } }
    ]);
    
    const startY = (state.settings.userName || state.settings.companyName) ? 38 : 32;
    
    doc.autoTable({
        startY: startY,
        head: [['Datum', 'Tag', 'Von', 'Bis', 'Pause', 'Gesamt', 'Arbeit', 'Beschreibung']],
        body: tableData,
        theme: 'plain',
        headStyles: {
            fillColor: [79, 70, 229],
            textColor: 255,
            fontStyle: 'bold',
            fontSize: 8,
            cellPadding: 2,
            halign: 'center'
        },
        styles: {
            fontSize: 8,
            cellPadding: 1.8,
            lineColor: [220, 220, 220],
            lineWidth: 0.1,
            halign: 'center',
            valign: 'middle',
            textColor: [50, 50, 50]
        },
        alternateRowStyles: {
            fillColor: [250, 250, 252]
        },
        columnStyles: {
            0: { cellWidth: 16 },
            1: { cellWidth: 12 },
            2: { cellWidth: 14 },
            3: { cellWidth: 14 },
            4: { cellWidth: 14 },
            5: { cellWidth: 16 },
            6: { cellWidth: 16 },
            7: { cellWidth: 'auto', halign: 'left', cellPadding: { left: 4, right: 2, top: 1.8, bottom: 1.8 } }
        },
        margin: { left: 20, right: 20 },
        tableLineColor: [200, 200, 200],
        tableLineWidth: 0.1
    });
    
    // ===== FOOTER SUMMARY =====
    const finalY = doc.lastAutoTable.finalY + 8;
    
    // Summary line with bullet points
    doc.setFontSize(9);
    doc.setTextColor(60, 60, 60);
    doc.setFont(undefined, 'bold');
    const summaryText = `Arbeitszeit: ${formatDuration(totalWorkMinutes)}  •  Pausen: ${formatDuration(totalBreakMinutes)}  •  Arbeitstage: ${workDays}  •  Urlaub: 0  •  Krank: 0`;
    doc.text(summaryText, 105, finalY, { align: 'center' });
    
    // Created date
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.setFont(undefined, 'normal');
    const today = new Date();
    doc.text(`Erstellt am ${today.getDate().toString().padStart(2, '0')}.${(today.getMonth() + 1).toString().padStart(2, '0')}.${today.getFullYear()}`, 105, finalY + 6, { align: 'center' });
    
    // Save
    doc.save(`Zeiterfassung_${year}_${(month + 1).toString().padStart(2, '0')}.pdf`);
    showToast(t('dataExported'), 'success');
}

// ==========================================
// Data Export/Import
// ==========================================
function exportJson() {
    const data = {
        version: '1.0',
        exportDate: new Date().toISOString(),
        settings: state.settings,
        entries: state.entries
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `zeiterfassung_backup_${formatDateISO(new Date())}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast(t('dataExported'), 'success');
}

function exportCsv() {
    const sortedEntries = [...state.entries].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    const headers = [t('date'), t('startTime'), t('endTime'), t('breakTime'), t('workTime'), t('description')];
    const rows = sortedEntries.map(entry => {
        const workMinutes = entry.workMinutes || calculateWorkMinutes(entry.startTime, entry.endTime, entry.breakMinutes);
        return [
            formatDate(new Date(entry.date)),
            entry.startTime,
            entry.endTime,
            entry.breakMinutes,
            formatDuration(workMinutes),
            `"${(entry.description || '').replace(/"/g, '""')}"`
        ].join(';');
    });
    
    const csv = [headers.join(';'), ...rows].join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `zeiterfassung_${formatDateISO(new Date())}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast(t('dataExported'), 'success');
}

function handleImportFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('importBtn').disabled = false;
}

function importData() {
    const fileInput = document.getElementById('importFile');
    const file = fileInput.files[0];
    if (!file) return;
    
    const importMode = document.querySelector('input[name="importMode"]:checked').value;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = JSON.parse(e.target.result);
            
            if (!data.entries || !Array.isArray(data.entries)) {
                throw new Error('Invalid file format');
            }
            
            if (importMode === 'replace') {
                // Show confirmation for replace mode
                document.getElementById('confirmMessage').textContent = t('confirmReplace');
                document.getElementById('confirmAction').onclick = () => {
                    state.entries = data.entries;
                    if (data.settings) {
                        state.settings = { ...state.settings, ...data.settings };
                    }
                    saveState();
                    closeModal('confirmModal');
                    refreshAllViews();
                    showToast(t('dataImported'), 'success');
                };
                openModal('confirmModal');
            } else {
                // Merge mode - avoid duplicates by checking id
                const existingIds = new Set(state.entries.map(e => e.id));
                const newEntries = data.entries.filter(e => !existingIds.has(e.id));
                
                // Also check for same date/time entries without matching ID
                newEntries.forEach(newEntry => {
                    const duplicate = state.entries.find(e => 
                        e.date === newEntry.date && 
                        e.startTime === newEntry.startTime && 
                        e.endTime === newEntry.endTime
                    );
                    if (!duplicate) {
                        state.entries.push(newEntry);
                    }
                });
                
                saveState();
                refreshAllViews();
                showToast(t('dataImported'), 'success');
            }
            
            // Reset file input
            fileInput.value = '';
            document.getElementById('fileName').textContent = t('noFileSelected');
            document.getElementById('importBtn').disabled = true;
            
        } catch (error) {
            console.error('Import error:', error);
            showToast(t('importError'), 'error');
        }
    };
    
    reader.readAsText(file);
}

function confirmDeleteAll() {
    document.getElementById('confirmMessage').textContent = t('confirmDeleteAll');
    document.getElementById('confirmAction').onclick = deleteAllData;
    openModal('confirmModal');
}

function deleteAllData() {
    state.entries = [];
    saveState();
    closeModal('confirmModal');
    refreshAllViews();
    showToast(t('dataDeleted'), 'success');
}

function refreshAllViews() {
    renderTodayEntries();
    renderCalendar();
    renderSelectedDateEntries();
    renderReport();
}

// ==========================================
// Settings
// ==========================================
function openSettings() {
    document.getElementById('userName').value = state.settings.userName;
    document.getElementById('companyName').value = state.settings.companyName;
    document.getElementById('defaultBreak').value = state.settings.defaultBreak;
    openModal('settingsModal');
}

function saveSettings() {
    state.settings.userName = document.getElementById('userName').value;
    state.settings.companyName = document.getElementById('companyName').value;
    state.settings.defaultBreak = parseInt(document.getElementById('defaultBreak').value) || 30;
    
    // Update default break in entry modal
    document.getElementById('entryBreak').value = state.settings.defaultBreak;
    
    saveState();
    closeModal('settingsModal');
    showToast(t('settingsSaved'), 'success');
}

// ==========================================
// Event Listeners
// ==========================================
function initEventListeners() {
    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', () => {
        state.theme = state.theme === 'light' ? 'dark' : 'light';
        updateTheme();
        saveState();
    });
    
    // Language toggle
    document.getElementById('langToggle').addEventListener('click', () => {
        state.language = state.language === 'de' ? 'en' : 'de';
        updateLanguageIcon();
        updateTranslations();
        refreshAllViews();
        saveState();
    });
    
    // Settings
    document.getElementById('settingsBtn').addEventListener('click', openSettings);
    document.getElementById('saveSettings').addEventListener('click', saveSettings);
    
    // Timer controls
    document.getElementById('startStopBtn').addEventListener('click', () => {
        if (state.timer.isRunning) {
            stopTimer();
        } else {
            startTimer();
        }
    });
    document.getElementById('resetBtn').addEventListener('click', resetTimer);
    
    // Calendar navigation
    document.getElementById('prevMonth').addEventListener('click', () => changeMonth(-1));
    document.getElementById('nextMonth').addEventListener('click', () => changeMonth(1));
    
    // Report navigation
    document.getElementById('prevReportMonth').addEventListener('click', () => changeReportMonth(-1));
    document.getElementById('nextReportMonth').addEventListener('click', () => changeReportMonth(1));
    
    // Add entry button
    document.getElementById('addEntryBtn').addEventListener('click', () => {
        state.editingEntryId = null;
        document.getElementById('entryModalTitle').textContent = t('addEntry');
        document.getElementById('entryDate').value = state.selectedDate || formatDateISO(new Date());
        setTimePickerValue('entryStart', '09:00');
        setTimePickerValue('entryEnd', '17:00');
        syncTimeInputs();
        document.getElementById('entryBreak').value = state.settings.defaultBreak;
        document.getElementById('entryDescription').value = '';
        openModal('entryModal');
    });
    
    // Save entry
    document.getElementById('saveEntry').addEventListener('click', saveEntry);
    
    // Export buttons
    document.getElementById('exportPdfBtn').addEventListener('click', exportPdf);
    document.getElementById('exportJsonBtn').addEventListener('click', exportJson);
    document.getElementById('exportCsvBtn').addEventListener('click', exportCsv);
    
    // Import
    document.getElementById('importFile').addEventListener('change', handleImportFile);
    document.getElementById('importBtn').addEventListener('click', importData);
    
    // Delete all
    document.getElementById('deleteAllBtn').addEventListener('click', confirmDeleteAll);
    
    // Modal close buttons
    document.querySelectorAll('[data-close-modal]').forEach(btn => {
        btn.addEventListener('click', closeAllModals);
    });
    
    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeAllModals();
        });
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeAllModals();
    });
}

// ==========================================
// Custom Time Picker
// ==========================================
function isMobileView() {
    return window.matchMedia('(max-width: 768px)').matches;
}

function initTimePickers() {
    // Set default values for desktop inputs
    document.getElementById('entryStartHour').value = '09';
    document.getElementById('entryStartMin').value = '00';
    document.getElementById('entryEndHour').value = '17';
    document.getElementById('entryEndMin').value = '00';
    
    // Set default values for mobile inputs
    document.getElementById('entryStartMobile').value = '09:00';
    document.getElementById('entryEndMobile').value = '17:00';
    
    // Desktop: Add input validation and auto-formatting
    const timeInputs = ['entryStartHour', 'entryStartMin', 'entryEndHour', 'entryEndMin'];
    timeInputs.forEach(id => {
        const input = document.getElementById(id);
        const isHour = id.includes('Hour');
        const max = isHour ? 23 : 59;
        
        // Only allow numbers
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            if (e.target.value.length > 2) {
                e.target.value = e.target.value.slice(0, 2);
            }
            syncTimeInputs('desktop');
        });
        
        // Format on blur (add leading zero, validate range)
        input.addEventListener('blur', (e) => {
            let val = parseInt(e.target.value) || 0;
            if (val > max) val = max;
            if (val < 0) val = 0;
            e.target.value = val.toString().padStart(2, '0');
            syncTimeInputs('desktop');
        });
        
        // Auto-jump to next field
        input.addEventListener('keyup', (e) => {
            if (e.target.value.length === 2 && !e.key.includes('Arrow') && e.key !== 'Tab' && e.key !== 'Backspace') {
                const inputs = timeInputs.map(i => document.getElementById(i));
                const currentIndex = inputs.indexOf(e.target);
                if (currentIndex < inputs.length - 1) {
                    inputs[currentIndex + 1].focus();
                    inputs[currentIndex + 1].select();
                }
            }
        });
        
        // Select all on focus
        input.addEventListener('focus', (e) => {
            e.target.select();
        });
    });
    
    // Mobile: Add change listeners for native time inputs
    document.getElementById('entryStartMobile').addEventListener('change', () => syncTimeInputs('mobile'));
    document.getElementById('entryEndMobile').addEventListener('change', () => syncTimeInputs('mobile'));
    
    // Sync hidden inputs
    syncTimeInputs('desktop');
}

function syncTimeInputs(source = 'desktop') {
    if (source === 'mobile') {
        // Mobile native time picker changed - sync to hidden inputs and desktop inputs
        const startTime = document.getElementById('entryStartMobile').value || '09:00';
        const endTime = document.getElementById('entryEndMobile').value || '17:00';
        
        document.getElementById('entryStart').value = startTime;
        document.getElementById('entryEnd').value = endTime;
        
        // Also sync desktop inputs (in case user resizes window)
        const [startHour, startMin] = startTime.split(':');
        const [endHour, endMin] = endTime.split(':');
        document.getElementById('entryStartHour').value = startHour;
        document.getElementById('entryStartMin').value = startMin;
        document.getElementById('entryEndHour').value = endHour;
        document.getElementById('entryEndMin').value = endMin;
    } else {
        // Desktop text inputs changed - sync to hidden inputs and mobile inputs
        const startHour = document.getElementById('entryStartHour').value.padStart(2, '0');
        const startMin = document.getElementById('entryStartMin').value.padStart(2, '0');
        const endHour = document.getElementById('entryEndHour').value.padStart(2, '0');
        const endMin = document.getElementById('entryEndMin').value.padStart(2, '0');
        
        const startTime = `${startHour}:${startMin}`;
        const endTime = `${endHour}:${endMin}`;
        
        document.getElementById('entryStart').value = startTime;
        document.getElementById('entryEnd').value = endTime;
        
        // Also sync mobile inputs (in case user resizes window)
        document.getElementById('entryStartMobile').value = startTime;
        document.getElementById('entryEndMobile').value = endTime;
    }
}

function setTimePickerValue(prefix, timeStr) {
    const [hours, minutes] = timeStr.split(':');
    // Set desktop inputs
    document.getElementById(`${prefix}Hour`).value = hours.padStart(2, '0');
    document.getElementById(`${prefix}Min`).value = minutes.padStart(2, '0');
    // Set mobile inputs
    const mobileId = prefix === 'entryStart' ? 'entryStartMobile' : 'entryEndMobile';
    document.getElementById(mobileId).value = `${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}`;
}

// ==========================================
// Initialization
// ==========================================
function init() {
    // Load saved state
    loadState();
    
    // Apply theme and language
    updateTheme();
    updateLanguageIcon();
    updateTranslations();
    
    // Initialize custom time pickers
    initTimePickers();
    
    // Initialize timer UI
    updateTimerUI();
    
    // Set default break value
    document.getElementById('entryBreak').value = state.settings.defaultBreak;
    
    // Select today's date by default
    state.selectedDate = formatDateISO(new Date());
    state.calendarMonth = new Date();
    state.reportMonth = new Date();
    
    // Render initial views
    renderTodayEntries();
    renderCalendar();
    renderReport();
    
    // Initialize event listeners
    initEventListeners();
    
    // Register Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed:', err));
    }
}

// Start app when DOM is ready
document.addEventListener('DOMContentLoaded', init);
