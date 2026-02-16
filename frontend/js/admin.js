/* ==========================================
   Admin Module - User/Department/Holiday/Schedule management
   ========================================== */
import { api } from './api.js';
import { auth } from './auth.js';
import { t } from './i18n.js';
import { escapeHtml, showToast, openModal, closeModal } from './utils.js';

let departments = [];
let users = [];

export async function renderAdminTab() {
    if (!auth.canManageUsers) return;
    await Promise.all([loadDepartments(), loadUsers()]);
    renderUserList();
    renderDepartmentList();
    renderHolidayList();
}

async function loadDepartments() {
    try { departments = await api.getDepartments() || []; } catch (_) { departments = []; }
}

async function loadUsers() {
    try { users = await api.listUsers() || []; } catch (_) { users = []; }
}

// ===== Users (sorted by department) =====
function renderUserList() {
    const container = document.getElementById('adminUsersList');
    if (!container) return;

    if (users.length === 0) {
        container.innerHTML = `<p class="no-entries">${t('noData')}</p>`;
        return;
    }

    // Group users by department
    const grouped = {};
    const noDept = [];
    users.forEach(u => {
        const deptName = u.department_name || null;
        if (deptName) {
            if (!grouped[deptName]) grouped[deptName] = [];
            grouped[deptName].push(u);
        } else {
            noDept.push(u);
        }
    });

    let html = '';
    const sortedDepts = Object.keys(grouped).sort();
    for (const deptName of sortedDepts) {
        html += `<div class="dept-group-header">🏢 ${escapeHtml(deptName)} (${grouped[deptName].length})</div>`;
        html += grouped[deptName].map(u => renderUserCard(u)).join('');
    }
    if (noDept.length > 0) {
        html += `<div class="dept-group-header">📋 ${t('noDepartment') || 'Ohne Abteilung'} (${noDept.length})</div>`;
        html += noDept.map(u => renderUserCard(u)).join('');
    }
    container.innerHTML = html;
}

function renderUserCard(u) {
    const roleLabel = u.role === 'admin' ? t('roleAdmin') : u.role === 'abteilungsleiter' ? t('roleLeader') : t('roleWorker');
    const statusClass = u.is_active ? 'active' : 'inactive';
    const canEdit = auth.isAdmin || (auth.isLeader && u.role === 'worker');
    return `
        <div class="admin-user-card ${statusClass}">
            <div class="user-info">
                <div class="user-name">${escapeHtml(u.first_name)} ${escapeHtml(u.last_name)}</div>
                <div class="user-email">${escapeHtml(u.email)}</div>
                <span class="user-role badge-${u.role}">${escapeHtml(roleLabel)}</span>
            </div>
            <div class="user-actions">
                ${canEdit ? `<button class="schedule-user-btn icon-btn-sm" data-id="${u.id}" data-name="${escapeHtml(u.first_name)} ${escapeHtml(u.last_name)}" title="${t('sollZeitTitle')}">🕐</button>` : ''}
                ${canEdit ? `<button class="vacation-user-btn icon-btn-sm" data-id="${u.id}" data-name="${escapeHtml(u.first_name)} ${escapeHtml(u.last_name)}" title="${t('vacationDaysTitle')}">🏖️</button>` : ''}
                ${canEdit ? `<button class="edit-user-btn icon-btn-sm" data-id="${u.id}" title="${t('editTitle')}">✏️</button>` : ''}
                ${canEdit && u.role !== 'admin' ? `<button class="delete-user-btn icon-btn-sm" data-id="${u.id}" title="${t('deleteTitle')}">🗑️</button>` : ''}
            </div>
        </div>
    `;
}

export function openAddUserModal() {
    document.getElementById('userModalTitle').textContent = t('addUser');
    document.getElementById('userForm')?.reset();
    document.getElementById('userId').value = '';
    document.getElementById('userPassword').required = true;
    const roleSelect = document.getElementById('userRole');
    if (roleSelect) {
        if (auth.isLeader && !auth.isAdmin) {
            roleSelect.innerHTML = '<option value="worker">' + t('roleWorker') + '</option>';
        } else {
            roleSelect.innerHTML = `
                <option value="worker">${t('roleWorker')}</option>
                <option value="abteilungsleiter">${t('roleLeader')}</option>
                <option value="admin">${t('roleAdmin')}</option>
            `;
        }
    }
    populateDepartmentSelect();
    openModal('userModal');
}

export async function openEditUserModal(id) {
    const user = users.find(u => u.id === id);
    if (!user) return;
    document.getElementById('userModalTitle').textContent = t('editUser');
    document.getElementById('userId').value = user.id;
    document.getElementById('userEmail').value = user.email;
    document.getElementById('userFirstName').value = user.first_name;
    document.getElementById('userLastName').value = user.last_name;
    document.getElementById('userPassword').value = '';
    document.getElementById('userPassword').required = false;
    document.getElementById('userActive').checked = user.is_active;
    const roleSelect = document.getElementById('userRole');
    if (auth.isLeader && !auth.isAdmin) {
        roleSelect.innerHTML = '<option value="worker">' + t('roleWorker') + '</option>';
    } else {
        roleSelect.innerHTML = `
            <option value="worker">${t('roleWorker')}</option>
            <option value="abteilungsleiter">${t('roleLeader')}</option>
            <option value="admin">${t('roleAdmin')}</option>
        `;
    }
    roleSelect.value = user.role;
    populateDepartmentSelect(user.department_id);
    openModal('userModal');
}

function populateDepartmentSelect(selectedId = null) {
    const sel = document.getElementById('userDepartment');
    if (!sel) return;
    sel.innerHTML = '<option value="">--</option>' +
        departments.map(d =>
            `<option value="${d.id}" ${d.id === selectedId ? 'selected' : ''}>${escapeHtml(d.name)}</option>`
        ).join('');
}

export async function saveUser() {
    const id = document.getElementById('userId')?.value;
    const email = document.getElementById('userEmail')?.value;
    const firstName = document.getElementById('userFirstName')?.value;
    const lastName = document.getElementById('userLastName')?.value;
    const role = document.getElementById('userRole')?.value;
    const deptId = document.getElementById('userDepartment')?.value || null;
    const pw = document.getElementById('userPassword')?.value;
    const isActive = document.getElementById('userActive')?.checked ?? true;

    if (!email || !firstName || !lastName) {
        showToast(t('errorFillAllFields'), 'error'); return;
    }
    try {
        if (id) {
            // Update: only send fields that UserUpdate accepts
            const updateData = {
                email: email,
                first_name: firstName,
                last_name: lastName,
                role: role,
                department_id: deptId,
                is_active: isActive,
            };
            await api.updateUser(id, updateData);
        } else {
            // Create: requires password, no is_active field
            if (!pw) { showToast(t('errorFillAllFields'), 'error'); return; }
            await api.createUser({
                email: email,
                password: pw,
                first_name: firstName,
                last_name: lastName,
                role: role,
                department_id: deptId,
            });
        }
        closeModal('userModal');
        showToast(t('success'), 'success');
        await Promise.all([loadUsers(), loadDepartments()]);
        renderUserList();
        renderDepartmentList();
    } catch (err) { showToast(err.message, 'error'); }
}

export async function deleteUser(id) {
    const user = users.find(u => u.id === id);
    const name = user ? `${user.first_name} ${user.last_name}` : id;
    const msg = document.getElementById('deleteUserMsg');
    if (msg) msg.textContent = t('confirmHardDelete').replace('{name}', name) || `Delete "${name}"?`;

    openModal('deleteUserModal');

    // Wire up the two action buttons (remove old listeners via clone trick)
    const deactivateBtn = document.getElementById('deactivateUserBtn');
    const hardDeleteBtn = document.getElementById('hardDeleteUserBtn');

    const newDeactivate = deactivateBtn.cloneNode(true);
    deactivateBtn.parentNode.replaceChild(newDeactivate, deactivateBtn);
    const newHardDelete = hardDeleteBtn.cloneNode(true);
    hardDeleteBtn.parentNode.replaceChild(newHardDelete, hardDeleteBtn);

    newDeactivate.addEventListener('click', async () => {
        closeModal('deleteUserModal');
        try {
            await api.deleteUser(id);
            showToast(t('success'), 'success');
            await Promise.all([loadUsers(), loadDepartments()]);
            renderUserList();
            renderDepartmentList();
        } catch (err) { showToast(err.message, 'error'); }
    });

    newHardDelete.addEventListener('click', async () => {
        // Double-confirm for permanent deletion
        if (!confirm(t('confirmHardDelete'))) return;
        closeModal('deleteUserModal');
        try {
            await api.hardDeleteUser(id);
            showToast(t('success'), 'success');
            await Promise.all([loadUsers(), loadDepartments()]);
            renderUserList();
            renderDepartmentList();
        } catch (err) { showToast(err.message, 'error'); }
    });
}

// ===== Schedule Management =====
export async function openScheduleModal(userId, userName) {
    document.getElementById('scheduleUserId').value = userId;
    document.getElementById('scheduleUserName').textContent = userName;
    try {
        const schedule = await api.getUserSchedule(userId);
        if (schedule) {
            document.getElementById('schedValidFrom').value = schedule.valid_from ?? '';
            document.getElementById('schedMon').value = schedule.monday_minutes ?? 480;
            document.getElementById('schedTue').value = schedule.tuesday_minutes ?? 480;
            document.getElementById('schedWed').value = schedule.wednesday_minutes ?? 480;
            document.getElementById('schedThu').value = schedule.thursday_minutes ?? 480;
            document.getElementById('schedFri').value = schedule.friday_minutes ?? 480;
            document.getElementById('schedSat').value = schedule.saturday_minutes ?? 0;
            document.getElementById('schedSun').value = schedule.sunday_minutes ?? 0;
        } else {
            const startOfYear = new Date().getFullYear() + '-01-01';
            document.getElementById('schedValidFrom').value = startOfYear;
            ['Mon','Tue','Wed','Thu','Fri'].forEach(d => document.getElementById('sched'+d).value = 480);
            ['Sat','Sun'].forEach(d => document.getElementById('sched'+d).value = 0);
        }
    } catch (_) {
        const startOfYear = new Date().getFullYear() + '-01-01';
        document.getElementById('schedValidFrom').value = startOfYear;
        ['Mon','Tue','Wed','Thu','Fri'].forEach(d => document.getElementById('sched'+d).value = 480);
        ['Sat','Sun'].forEach(d => document.getElementById('sched'+d).value = 0);
    }
    openModal('scheduleModal');
}

export async function saveSchedule() {
    const userId = document.getElementById('scheduleUserId').value;
    if (!userId) return;
    const validFrom = document.getElementById('schedValidFrom').value;
    if (!validFrom) { showToast(t('errorFillAllFields'), 'error'); return; }
    const data = {
        valid_from: validFrom,
        monday_minutes: parseInt(document.getElementById('schedMon').value) || 0,
        tuesday_minutes: parseInt(document.getElementById('schedTue').value) || 0,
        wednesday_minutes: parseInt(document.getElementById('schedWed').value) || 0,
        thursday_minutes: parseInt(document.getElementById('schedThu').value) || 0,
        friday_minutes: parseInt(document.getElementById('schedFri').value) || 0,
        saturday_minutes: parseInt(document.getElementById('schedSat').value) || 0,
        sunday_minutes: parseInt(document.getElementById('schedSun').value) || 0,
    };
    try {
        await api.setUserSchedule(userId, data);
        closeModal('scheduleModal');
        showToast(t('success'), 'success');
        await renderAdminTab();
    } catch (err) { showToast(err.message, 'error'); }
}

// ===== Vacation Budget =====
export async function openVacationModal(userId, userName) {
    document.getElementById('vacUserId').value = userId;
    document.getElementById('vacUserName').textContent = userName;
    const year = new Date().getFullYear();
    document.getElementById('vacYear').value = year;
    document.getElementById('vacTotalDays').value = 30;
    openModal('vacationModal');
}

export async function saveVacationBudget() {
    const userId = document.getElementById('vacUserId').value;
    const year = parseInt(document.getElementById('vacYear').value);
    const totalDays = parseInt(document.getElementById('vacTotalDays').value);
    if (!userId || !year || isNaN(totalDays)) { showToast(t('errorFillAllFields'), 'error'); return; }
    try {
        await api.setVacationBudget(userId, totalDays, year);
        closeModal('vacationModal');
        showToast(t('success'), 'success');
        await renderAdminTab();
    } catch (err) { showToast(err.message, 'error'); }
}

// ===== Departments =====
function renderDepartmentList() {
    const container = document.getElementById('adminDeptsList');
    if (!container) return;
    if (!auth.isAdmin) {
        container.innerHTML = '';
        const parentSection = container.closest('.admin-section');
        if (parentSection) parentSection.style.display = 'none';
        return;
    }
    if (departments.length === 0) {
        container.innerHTML = `<p class="no-entries">${t('noData')}</p>`;
        return;
    }
    container.innerHTML = departments.map(d => `
        <div class="admin-dept-card">
            <div class="dept-info">
                <div class="dept-name">${escapeHtml(d.name)}</div>
                <div class="dept-count">${d.member_count ?? 0} ${t('adminUsers')}</div>
            </div>
            <div class="dept-actions">
                <button class="edit-dept-btn icon-btn-sm" data-id="${d.id}" data-name="${escapeHtml(d.name)}" title="${t('renameTitle')}">✏️</button>
                ${(d.member_count ?? 0) === 0 ? `<button class="delete-dept-btn icon-btn-sm" data-id="${d.id}" title="${t('deleteTitle')}">🗑️</button>` : ''}
            </div>
        </div>
    `).join('');
}

export function openAddDeptModal() {
    document.getElementById('deptForm')?.reset();
    document.getElementById('deptModalTitle').textContent = t('addDepartment');
    document.getElementById('deptId').value = '';
    openModal('deptModal');
}

export function openEditDeptModal(id, name) {
    document.getElementById('deptModalTitle').textContent = t('editDepartment') || 'Abteilung bearbeiten';
    document.getElementById('deptId').value = id;
    document.getElementById('deptName').value = name;
    openModal('deptModal');
}

export async function saveDepartment() {
    const id = document.getElementById('deptId')?.value;
    const name = document.getElementById('deptName')?.value;
    if (!name) { showToast(t('errorFillAllFields'), 'error'); return; }
    try {
        if (id) { await api.updateDepartment(id, { name }); }
        else { await api.createDepartment({ name }); }
        closeModal('deptModal');
        showToast(t('success'), 'success');
        await Promise.all([loadDepartments(), loadUsers()]);
        renderDepartmentList();
        renderUserList();
    } catch (err) { showToast(err.message, 'error'); }
}

export async function deleteDepartment(id) {
    try {
        await api.deleteDepartment(id);
        showToast(t('success'), 'success');
        await Promise.all([loadDepartments(), loadUsers()]);
        renderDepartmentList();
        renderUserList();
    } catch (err) { showToast(err.message, 'error'); }
}

// ===== Holidays =====
async function renderHolidayList() {
    const container = document.getElementById('adminHolidaysList');
    if (!container) return;
    if (!auth.isAdmin) {
        container.innerHTML = '';
        const parentSection = container.closest('.admin-section');
        if (parentSection) parentSection.style.display = 'none';
        return;
    }
    try {
        const year = new Date().getFullYear();
        const holidays = await api.getHolidays(year);
        if (!holidays || holidays.length === 0) {
            container.innerHTML = `<p class="no-entries">${t('noData')}</p>`;
            return;
        }
        container.innerHTML = holidays.map(h => `
            <div class="admin-holiday-card">
                <div class="holiday-info">
                    <span class="holiday-date">${escapeHtml(h.date)}</span>
                    <span class="holiday-name">${escapeHtml(h.name)}</span>
                    ${h.is_half_day ? '<span class="badge-half">½</span>' : ''}
                </div>
                <button class="delete-holiday-btn icon-btn-sm" data-id="${h.id}" title="${t('delete')}">🗑️</button>
            </div>
        `).join('');
    } catch (_) {
        container.innerHTML = `<p class="no-entries">${t('error')}</p>`;
    }
}

export function openAddHolidayModal() {
    document.getElementById('holidayForm')?.reset();
    openModal('holidayModal');
}

export async function saveHoliday() {
    const date = document.getElementById('holidayDate')?.value;
    const name = document.getElementById('holidayNameInput')?.value;
    const isHalfDay = document.getElementById('holidayHalfDay')?.checked || false;
    if (!date || !name) { showToast(t('errorFillAllFields'), 'error'); return; }
    try {
        await api.createHoliday({ date, name, is_half_day: isHalfDay });
        closeModal('holidayModal');
        showToast(t('success'), 'success');
        renderHolidayList();
    } catch (err) { showToast(err.message, 'error'); }
}

export async function deleteHoliday(id) {
    try { await api.deleteHoliday(id); showToast(t('success'), 'success'); renderHolidayList(); }
    catch (err) { showToast(err.message, 'error'); }
}

export async function autoGenerateHolidays() {
    const year = new Date().getFullYear();
    try {
        const generated = await api.autoGenerateHolidays(year);
        showToast(`${generated?.length ?? 0} Feiertage generiert`, 'success');
        renderHolidayList();
    } catch (err) { showToast(err.message, 'error'); }
}
