/* ==========================================
   Entries Module - CRUD operations for entries
   ========================================== */
import { api } from './api.js';
import { t } from './i18n.js';
import { formatDateISO, parseTimeToMinutes, calculateWorkMinutes,
         showToast, openModal, closeModal, closeAllModals } from './utils.js';
import { renderTodayEntries } from './timer.js';
import { renderCalendar, renderSelectedDateEntries, getSelectedDate } from './calendar.js';

let editingEntryId = null;
let defaultBreak = 30;

export function setDefaultBreak(val) { defaultBreak = val; }

export function initEntryModal() {
    initTimePickers();
}

export function openAddEntryModal() {
    editingEntryId = null;
    const title = document.getElementById('entryModalTitle');
    if (title) title.textContent = t('addEntry');
    const date = document.getElementById('entryDate');
    if (date) date.value = getSelectedDate() || formatDateISO(new Date());
    setTimePickerValue('entryStart', '09:00');
    setTimePickerValue('entryEnd', '17:00');
    syncTimeInputs();
    const brk = document.getElementById('entryBreak');
    if (brk) brk.value = defaultBreak;
    const desc = document.getElementById('entryDescription');
    if (desc) desc.value = '';
    openModal('entryModal');
}

export async function openEditEntryModal(id) {
    try {
        // Fetch fresh entry data
        const entries = await api.getEntries({});
        const entry = entries?.find(e => e.id === id);
        if (!entry) { showToast(t('error'), 'error'); return; }

        editingEntryId = id;
        const title = document.getElementById('entryModalTitle');
        if (title) title.textContent = t('editEntry');
        const date = document.getElementById('entryDate');
        if (date) date.value = entry.date;
        setTimePickerValue('entryStart', entry.start_time);
        setTimePickerValue('entryEnd', entry.end_time);
        syncTimeInputs();
        const brk = document.getElementById('entryBreak');
        if (brk) brk.value = entry.break_minutes;
        const desc = document.getElementById('entryDescription');
        if (desc) desc.value = entry.description || '';
        openModal('entryModal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

export async function saveEntry() {
    const date = document.getElementById('entryDate')?.value;
    const startTime = document.getElementById('entryStart')?.value;
    const endTime = document.getElementById('entryEnd')?.value;
    const breakMinutes = parseInt(document.getElementById('entryBreak')?.value) || 0;
    const description = document.getElementById('entryDescription')?.value || '';

    if (!date || !startTime || !endTime) {
        showToast(t('errorFillAllFields'), 'error');
        return;
    }
    if (parseTimeToMinutes(startTime) > parseTimeToMinutes(endTime)) {
        showToast(t('errorInvalidTimeRange'), 'error');
        return;
    }

    const data = {
        date: date || null,
        start_time: startTime || null,
        end_time: endTime || null,
        break_minutes: breakMinutes,
        description: description || null,
    };

    try {
        if (editingEntryId) {
            await api.updateEntry(editingEntryId, data);
        } else {
            await api.createEntry(data);
        }
        editingEntryId = null;
        closeModal('entryModal');
        showToast(t('entrySaved'), 'success');
        refreshEntryViews();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

export async function confirmDeleteEntry(id) {
    editingEntryId = id;
    const msg = document.getElementById('confirmMessage');
    if (msg) msg.textContent = t('confirmDelete');
    const btn = document.getElementById('confirmAction');
    if (btn) btn.onclick = () => deleteEntry(id);
    openModal('confirmModal');
}

async function deleteEntry(id) {
    try {
        await api.deleteEntry(id);
        editingEntryId = null;
        closeModal('confirmModal');
        showToast(t('entryDeleted'), 'success');
        refreshEntryViews();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

export async function refreshEntryViews() {
    await Promise.all([
        renderTodayEntries(),
        renderSelectedDateEntries(),
        renderCalendar(),
    ]);
}

// ===== Time Picker Logic =====
function initTimePickers() {
    const timeInputs = ['entryStartHour', 'entryStartMin', 'entryEndHour', 'entryEndMin'];
    timeInputs.forEach(id => {
        const input = document.getElementById(id);
        if (!input) return;
        const isHour = id.includes('Hour');
        const max = isHour ? 23 : 59;
        let userTypedChars = 0;

        input.addEventListener('focus', e => { userTypedChars = 0; e.target.select(); });
        input.addEventListener('input', e => {
            e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 2);
            syncTimeInputs('desktop');
        });
        input.addEventListener('blur', e => {
            let val = parseInt(e.target.value) || 0;
            if (val > max) val = max;
            if (val < 0) val = 0;
            e.target.value = val.toString().padStart(2, '0');
            syncTimeInputs('desktop');
        });
        input.addEventListener('keydown', e => {
            if (/^[0-9]$/.test(e.key)) {
                if (input.selectionStart === 0 && input.selectionEnd === input.value.length) userTypedChars = 0;
            }
            if (e.key === 'Backspace' || e.key === 'Delete') userTypedChars = 0;
        });
        input.addEventListener('keyup', e => {
            if (/^[0-9]$/.test(e.key)) userTypedChars++;
            if (userTypedChars >= 2 && e.target.value.length === 2) {
                const inputs = timeInputs.map(i => document.getElementById(i)).filter(Boolean);
                const idx = inputs.indexOf(e.target);
                if (idx < inputs.length - 1) { inputs[idx + 1].focus(); inputs[idx + 1].select(); }
            }
        });
    });

    document.getElementById('entryStartMobile')?.addEventListener('change', () => syncTimeInputs('mobile'));
    document.getElementById('entryEndMobile')?.addEventListener('change', () => syncTimeInputs('mobile'));
    syncTimeInputs('desktop');
}

function syncTimeInputs(source = 'desktop') {
    if (source === 'mobile') {
        const startTime = document.getElementById('entryStartMobile')?.value || '09:00';
        const endTime = document.getElementById('entryEndMobile')?.value || '17:00';
        const s = document.getElementById('entryStart'); if (s) s.value = startTime;
        const e = document.getElementById('entryEnd'); if (e) e.value = endTime;
        const [sh, sm] = startTime.split(':');
        const [eh, em] = endTime.split(':');
        const esh = document.getElementById('entryStartHour'); if (esh) esh.value = sh;
        const esm = document.getElementById('entryStartMin'); if (esm) esm.value = sm;
        const eeh = document.getElementById('entryEndHour'); if (eeh) eeh.value = eh;
        const eem = document.getElementById('entryEndMin'); if (eem) eem.value = em;
    } else {
        const sh = (document.getElementById('entryStartHour')?.value || '09').padStart(2, '0');
        const sm = (document.getElementById('entryStartMin')?.value || '00').padStart(2, '0');
        const eh = (document.getElementById('entryEndHour')?.value || '17').padStart(2, '0');
        const em = (document.getElementById('entryEndMin')?.value || '00').padStart(2, '0');
        const startTime = `${sh}:${sm}`;
        const endTime = `${eh}:${em}`;
        const s = document.getElementById('entryStart'); if (s) s.value = startTime;
        const e = document.getElementById('entryEnd'); if (e) e.value = endTime;
        const esm = document.getElementById('entryStartMobile'); if (esm) esm.value = startTime;
        const eem = document.getElementById('entryEndMobile'); if (eem) eem.value = endTime;
    }
}

function setTimePickerValue(prefix, timeStr) {
    const [hours, minutes] = timeStr.split(':');
    const h = document.getElementById(`${prefix}Hour`);
    const m = document.getElementById(`${prefix}Min`);
    if (h) h.value = hours.padStart(2, '0');
    if (m) m.value = minutes.padStart(2, '0');
    const mobileId = prefix === 'entryStart' ? 'entryStartMobile' : 'entryEndMobile';
    const mob = document.getElementById(mobileId);
    if (mob) mob.value = `${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}`;
}
