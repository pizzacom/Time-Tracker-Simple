/* ==========================================
   Main App Module - Orchestrates all modules
   ========================================== */
import { auth } from './auth.js';
import { t, loadLanguage, setLanguage, getLanguage, updateDOMTranslations } from './i18n.js';
import { formatDateISO, showToast, closeAllModals, saveLocal, loadLocal } from './utils.js';
import { initTimer, startTimer, stopTimer, resetTimer, renderTodayEntries } from './timer.js';
import { renderCalendar, changeMonth, selectDate, getSelectedDate, renderSelectedDateEntries } from './calendar.js';
import { initEntryModal, openAddEntryModal, openEditEntryModal, saveEntry, confirmDeleteEntry, refreshEntryViews } from './entries.js';
import { renderReport, changeReportMonth, getReportMonth, exportPdf, exportExcel, exportCsv } from './reports.js';
import { renderOvertimeTab, openUseOvertimeModal, submitUseOvertime,
         renderAbsencesSection, openAddAbsenceModal, submitAddAbsence, deleteAbsence,
         deleteOvertimeEntry } from './overtime.js';
import { renderAdminTab, openAddUserModal, openEditUserModal, saveUser, deleteUser,
         openAddDeptModal, openEditDeptModal, saveDepartment, deleteDepartment,
         openAddHolidayModal, saveHoliday, deleteHoliday, autoGenerateHolidays,
         openScheduleModal, saveSchedule,
         openVacationModal, saveVacationBudget } from './admin.js';

import api from './api.js';

// ===== State =====
let theme = 'light';

function updateTheme() {
    document.body.setAttribute('data-theme', theme);
    const icon = document.getElementById('themeIcon');
    if (icon) icon.textContent = theme === 'light' ? '🌙' : '☀️';
}

function updateLanguageIcon() {
    const icon = document.getElementById('langIcon');
    if (icon) icon.textContent = getLanguage() === 'de' ? '🇩🇪' : '🇬🇧';
}

function switchTab(tabName) {
    localStorage.setItem('activeTab', tabName);
    document.querySelectorAll('.tab-btn').forEach(btn =>
        btn.classList.toggle('active', btn.dataset.tab === tabName)
    );
    document.querySelectorAll('.tab-content').forEach(c =>
        c.classList.toggle('active', c.id === `${tabName}-tab`)
    );

    if (tabName === 'calendar') { renderCalendar(); renderSelectedDateEntries(); }
    else if (tabName === 'reports') renderReport();
    else if (tabName === 'timer') renderTodayEntries();
    else if (tabName === 'overtime') { renderOvertimeTab(); renderAbsencesSection(); }
    else if (tabName === 'admin') renderAdminTab();
    else if (tabName === 'data') initDataTab();
}

function setupVisibility() {
    // Show/hide tabs based on role
    const overtimeTab = document.querySelector('[data-tab="overtime"]');
    const adminTab = document.querySelector('[data-tab="admin"]');

    if (overtimeTab) overtimeTab.style.display = '';
    if (adminTab) {
        adminTab.style.display = auth.canManageUsers ? '' : 'none';
    }

    // Backup section only for admin role
    const backupSection = document.getElementById('backupSection');
    if (backupSection) {
        backupSection.style.display = (auth.user?.role === 'admin') ? '' : 'none';
    }

    // Show user info
    const userDisplay = document.getElementById('userDisplay');
    if (userDisplay && auth.user) {
        userDisplay.textContent = `${auth.user.first_name} ${auth.user.last_name}`;
        userDisplay.title = auth.user.email;
    }

    // Show logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.style.display = '';
}

async function handleLogout() {
    await auth.logout();
    // Redirect to login
    window.location.href = 'login.html';
}

// ===== Event Delegation =====
function initEventDelegation() {
    document.addEventListener('click', async (e) => {
        const target = e.target.closest('button');
        if (!target) return;

        // Entry edit/delete (delegated from dynamic content)
        if (target.classList.contains('edit-entry-btn')) {
            const id = target.dataset.id;
            if (id) openEditEntryModal(id);
        }
        if (target.classList.contains('delete-entry-btn')) {
            const id = target.dataset.id;
            if (id) confirmDeleteEntry(id);
        }

        // Admin: edit/delete user
        if (target.classList.contains('edit-user-btn')) {
            const id = target.dataset.id;
            if (id) openEditUserModal(id);
        }
        if (target.classList.contains('delete-user-btn')) {
            const id = target.dataset.id;
            if (id) deleteUser(id);
        }

        // Admin: schedule / vacation
        if (target.classList.contains('schedule-user-btn')) {
            const id = target.dataset.id;
            const name = target.dataset.name;
            if (id) openScheduleModal(id, name);
        }
        if (target.classList.contains('vacation-user-btn')) {
            const id = target.dataset.id;
            const name = target.dataset.name;
            if (id) openVacationModal(id, name);
        }

        // Admin: dept edit/delete
        if (target.classList.contains('edit-dept-btn')) {
            const id = target.dataset.id;
            const name = target.dataset.name;
            if (id) openEditDeptModal(id, name);
        }
        if (target.classList.contains('delete-dept-btn')) {
            const id = target.dataset.id;
            if (id) deleteDepartment(id);
        }

        // Admin: delete holiday
        if (target.classList.contains('delete-holiday-btn')) {
            const id = target.dataset.id;
            if (id) deleteHoliday(id);
        }

        // Absence delete
        if (target.classList.contains('delete-absence-btn')) {
            const id = target.dataset.id;
            if (id) deleteAbsence(id);
        }

        // Overtime history delete
        if (target.classList.contains('delete-overtime-btn')) {
            const id = target.dataset.id;
            if (id) deleteOvertimeEntry(id);
        }
    });
}

function initEventListeners() {
    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn =>
        btn.addEventListener('click', () => switchTab(btn.dataset.tab))
    );

    // Theme toggle
    document.getElementById('themeToggle')?.addEventListener('click', () => {
        theme = theme === 'light' ? 'dark' : 'light';
        updateTheme();
        saveLocal('theme', theme);
    });

    // Language toggle
    document.getElementById('langToggle')?.addEventListener('click', () => {
        const newLang = getLanguage() === 'de' ? 'en' : 'de';
        setLanguage(newLang);
        updateLanguageIcon();
        updateDOMTranslations();
        // Re-render the active tab to update JS-generated translations
        const activeTab = localStorage.getItem('activeTab') || 'timer';
        switchTab(activeTab);
    });

    // Settings
    document.getElementById('settingsBtn')?.addEventListener('click', openSettings);
    document.getElementById('saveSettings')?.addEventListener('click', saveSettings);

    // Timer
    document.getElementById('startStopBtn')?.addEventListener('click', () => {
        const timerBtn = document.getElementById('startStopIcon');
        if (timerBtn?.textContent === '⏹️') {
            stopTimer(() => refreshEntryViews());
        } else {
            startTimer();
        }
    });
    document.getElementById('resetBtn')?.addEventListener('click', resetTimer);

    // Calendar nav
    document.getElementById('prevMonth')?.addEventListener('click', () => changeMonth(-1));
    document.getElementById('nextMonth')?.addEventListener('click', () => changeMonth(1));

    // Report nav
    document.getElementById('prevReportMonth')?.addEventListener('click', () => changeReportMonth(-1));
    document.getElementById('nextReportMonth')?.addEventListener('click', () => changeReportMonth(1));

    // Add entry
    document.getElementById('addEntryBtn')?.addEventListener('click', openAddEntryModal);
    document.getElementById('saveEntry')?.addEventListener('click', saveEntry);

    // Export (reports tab)
    document.getElementById('exportPdfBtn')?.addEventListener('click', exportPdf);
    document.getElementById('exportExcelBtn')?.addEventListener('click', exportExcel);
    document.getElementById('exportCsvBtn')?.addEventListener('click', exportCsv);

    // Export (data tab) – uses selected user if leader/admin
    document.getElementById('exportPdfBtn2')?.addEventListener('click', handleDataExportPdf);
    document.getElementById('exportExcelBtn2')?.addEventListener('click', handleDataExportExcel);
    document.getElementById('exportCsvBtn2')?.addEventListener('click', handleDataExportCsv);
    document.getElementById('exportJsonBtn')?.addEventListener('click', handleExportJson);

    // Import (data tab)
    document.getElementById('importJsonFile')?.addEventListener('change', (e) => {
        const name = e.target.files?.[0]?.name;
        const label = document.getElementById('importFileName');
        if (label) label.textContent = name || t('noFileSelected');
    });
    document.getElementById('importJsonBtn')?.addEventListener('click', handleImportJson);

    // Overtime
    document.getElementById('useOvertimeBtn')?.addEventListener('click', openUseOvertimeModal);
    document.getElementById('submitUseOvertime')?.addEventListener('click', submitUseOvertime);

    // Absences
    document.getElementById('addAbsenceBtn')?.addEventListener('click', openAddAbsenceModal);
    document.getElementById('submitAddAbsence')?.addEventListener('click', submitAddAbsence);

    // Admin
    document.getElementById('addUserBtn')?.addEventListener('click', openAddUserModal);
    document.getElementById('saveUserBtn')?.addEventListener('click', saveUser);
    document.getElementById('addDeptBtn')?.addEventListener('click', openAddDeptModal);
    document.getElementById('saveDeptBtn')?.addEventListener('click', saveDepartment);
    document.getElementById('addHolidayBtn')?.addEventListener('click', openAddHolidayModal);
    document.getElementById('saveHolidayBtn')?.addEventListener('click', saveHoliday);
    document.getElementById('autoGenHolidaysBtn')?.addEventListener('click', autoGenerateHolidays);
    document.getElementById('saveScheduleBtn')?.addEventListener('click', saveSchedule);
    document.getElementById('saveVacationBtn')?.addEventListener('click', saveVacationBudget);

    // Change password
    document.getElementById('openChangePasswordBtn')?.addEventListener('click', () => {
        const { closeModal, openModal } = import('./utils.js').then ? {} : {};
        import('./utils.js').then(({ closeModal, openModal }) => {
            closeModal('settingsModal');
            document.getElementById('currentPasswordInput').value = '';
            document.getElementById('newPasswordInput').value = '';
            document.getElementById('confirmPasswordInput').value = '';
            openModal('changePasswordModal');
        });
    });
    document.getElementById('submitChangePassword')?.addEventListener('click', handleChangePassword);

    // Backup
    document.getElementById('exportBackupBtn')?.addEventListener('click', handleExportBackup);
    document.getElementById('importBackupFile')?.addEventListener('change', handleImportBackup);

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);

    // Modal close buttons
    document.querySelectorAll('[data-close-modal]').forEach(btn =>
        btn.addEventListener('click', closeAllModals)
    );
    document.querySelectorAll('.modal').forEach(modal =>
        modal.addEventListener('click', e => { if (e.target === modal) closeAllModals(); })
    );
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAllModals(); });
}

// ===== Settings =====
async function openSettings() {
    const { openModal } = await import('./utils.js');
    if (auth.user) {
        document.getElementById('userNameSetting').value = auth.user.first_name || '';
        document.getElementById('companyName').value = loadLocal('companyName', '');
        document.getElementById('defaultBreak').value = loadLocal('defaultBreak', 30);
    }
    openModal('settingsModal');
}

async function saveSettings() {
    const { closeModal } = await import('./utils.js');
    const companyName = document.getElementById('companyName')?.value || '';
    const defaultBreak = parseInt(document.getElementById('defaultBreak')?.value) || 30;
    saveLocal('companyName', companyName);
    saveLocal('defaultBreak', defaultBreak);

    const brk = document.getElementById('entryBreak');
    if (brk) brk.value = defaultBreak;

    closeModal('settingsModal');
    showToast(t('settingsSaved'), 'success');
}

// ===== Change Password =====
async function handleChangePassword() {
    const current = document.getElementById('currentPasswordInput')?.value;
    const newPw = document.getElementById('newPasswordInput')?.value;
    const confirm = document.getElementById('confirmPasswordInput')?.value;

    if (!current || !newPw || !confirm) {
        showToast(t('errorFillAllFields'), 'error');
        return;
    }
    if (newPw.length < 6) {
        showToast(t('passwordTooShort'), 'error');
        return;
    }
    if (newPw !== confirm) {
        showToast(t('passwordMismatch'), 'error');
        return;
    }
    try {
        await api.changePassword(current, newPw);
        closeAllModals();
        showToast(t('passwordChanged'), 'success');
    } catch (e) {
        showToast(e.message || t('error'), 'error');
    }
}

// ===== Backup =====
async function handleExportBackup() {
    try {
        await api.exportBackup();
        showToast(t('backupExported'), 'success');
    } catch (e) {
        showToast(e.message || t('error'), 'error');
    }
}

// ===== Data Tab (user selector + export) =====
function _getSelectedDataUserId() {
    const sel = document.getElementById('dataUserSelect');
    return sel?.value || '';
}

async function initDataTab() {
    const section = document.getElementById('dataUserSelectSection');
    if (!section) return;

    if (!auth.canManageUsers) {
        section.style.display = 'none';
        return;
    }

    section.style.display = '';
    const sel = document.getElementById('dataUserSelect');
    if (!sel) return;

    // Populate user list (keep first option = "my data")
    try {
        const users = await api.listUsers();
        // Keep the first "Meine Daten" option, then add users
        sel.innerHTML = `<option value="">${t('myData')}</option>`;
        users.forEach(u => {
            if (!u.is_active) return;
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = `${u.first_name} ${u.last_name} (${u.email})`;
            sel.appendChild(opt);
        });
    } catch (_) { /* ignore – keep just "my data" */ }
}

async function handleDataExportPdf() {
    try {
        const userId = _getSelectedDataUserId();
        const rm = getReportMonth();
        const year = rm.getFullYear();
        const month = rm.getMonth() + 1;
        if (userId) {
            await api.downloadUserPdf(userId, year, month);
        } else {
            await api.downloadPdf(year, month);
        }
        showToast(t('dataExported'), 'success');
    } catch (e) { showToast(e.message || t('error'), 'error'); }
}

async function handleDataExportExcel() {
    try {
        const userId = _getSelectedDataUserId();
        const rm = getReportMonth();
        const year = rm.getFullYear();
        const month = rm.getMonth() + 1;
        if (userId) {
            await api.downloadUserExcel(userId, year, month);
        } else {
            await api.downloadExcel(year, month);
        }
        showToast(t('dataExported'), 'success');
    } catch (e) { showToast(e.message || t('error'), 'error'); }
}

async function handleDataExportCsv() {
    try {
        const userId = _getSelectedDataUserId();
        const rm = getReportMonth();
        const year = rm.getFullYear();
        const month = rm.getMonth() + 1;
        if (userId) {
            await api.downloadUserCsv(userId, year, month);
        } else {
            await api.downloadCsv(year, month);
        }
        showToast(t('dataExported'), 'success');
    } catch (e) { showToast(e.message || t('error'), 'error'); }
}

// ===== Personal Data Export/Import =====
async function handleExportJson() {
    try {
        const userId = _getSelectedDataUserId();
        let data;
        if (userId) {
            data = await api.exportUserData(userId);
        } else {
            data = await api.exportPersonalData();
        }
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const name = data.user ? `${data.user.last_name}_${data.user.first_name}` : 'daten';
        const now = new Date();
        a.download = `zeittracker_${name}_${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(t('dataExported'), 'success');
    } catch (e) {
        showToast(e.message || t('error'), 'error');
    }
}

async function handleImportJson() {
    const fileInput = document.getElementById('importJsonFile');
    const file = fileInput?.files?.[0];
    if (!file) {
        showToast(t('noFileSelected'), 'error');
        return;
    }

    const modeRadio = document.querySelector('input[name="importMode"]:checked');
    const mode = modeRadio?.value || 'merge';

    if (mode === 'replace') {
        const confirmed = window.confirm(t('confirmReplace'));
        if (!confirmed) return;
    }

    try {
        const text = await file.text();
        const data = JSON.parse(text);
        const payload = {
            entries: data.entries || [],
            absences: data.absences || [],
        };
        const userId = _getSelectedDataUserId();
        let result;
        if (userId) {
            result = await api.importUserData(userId, payload, mode);
        } else {
            result = await api.importPersonalData(payload, mode);
        }
        showToast(result.message || t('dataImported'), 'success');
        // Refresh current tab data
        const activeTab = localStorage.getItem('activeTab') || 'timer';
        switchTab(activeTab);
    } catch (e) {
        if (e instanceof SyntaxError) {
            showToast(t('invalidFile'), 'error');
        } else {
            showToast(e.message || t('importError'), 'error');
        }
    }
    // Reset file input
    fileInput.value = '';
    const label = document.getElementById('importFileName');
    if (label) label.textContent = t('noFileSelected');
}

async function handleImportBackup(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    const confirmed = window.confirm(t('backupImportWarning'));
    if (!confirmed) {
        e.target.value = '';
        return;
    }

    try {
        const result = await api.importBackup(file);
        showToast(result.message || t('backupSuccess'), 'success');
        // Refresh the page to pick up restored data
        setTimeout(() => window.location.reload(), 1500);
    } catch (err) {
        showToast(err.message || t('error'), 'error');
    }
    e.target.value = '';
}

// ===== Init =====
async function init() {
    // Load preferences
    loadLanguage();
    theme = loadLocal('theme', 'light') || 'light';
    updateTheme();
    updateLanguageIcon();

    // Check auth
    const loggedIn = await auth.init();
    if (!loggedIn) {
        window.location.href = 'login.html';
        return;
    }

    // Setup UI
    setupVisibility();
    updateDOMTranslations();
    initEntryModal();
    await initTimer();
    initEventListeners();
    initEventDelegation();

    // Select today and render
    selectDate(formatDateISO(new Date()));

    // Restore last active tab (this will render the appropriate tab content)
    const savedTab = localStorage.getItem('activeTab') || 'timer';
    switchTab(savedTab);

    // Service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js').catch(() => {});
    }
}

document.addEventListener('DOMContentLoaded', init);
