/* ==========================================
   API Client Module - Communicates with Backend
   ========================================== */

const API_BASE = '/api/v1';

class ApiClient {
    constructor() {
        this._accessToken = null;
        this._onUnauthorized = null;
    }

    set accessToken(token) {
        this._accessToken = token;
    }

    get accessToken() {
        return this._accessToken;
    }

    set onUnauthorized(cb) {
        this._onUnauthorized = cb;
    }

    _headers(extra = {}) {
        const h = { 'Content-Type': 'application/json', ...extra };
        if (this._accessToken) {
            h['Authorization'] = `Bearer ${this._accessToken}`;
        }
        return h;
    }

    async _request(method, path, body = null, options = {}) {
        const url = `${API_BASE}${path}`;
        const config = {
            method,
            headers: this._headers(options.headers),
            credentials: 'include', // Send cookies (refresh token)
        };
        if (body && method !== 'GET') {
            config.body = JSON.stringify(body);
        }

        let response;
        try {
            response = await fetch(url, config);
        } catch (err) {
            throw new Error('Network error. Server might be offline.');
        }

        // Handle 401 - try refresh token
        if (response.status === 401 && !options._isRetry) {
            const refreshed = await this._tryRefresh();
            if (refreshed) {
                return this._request(method, path, body, { ...options, _isRetry: true });
            }
            if (this._onUnauthorized) this._onUnauthorized();
            throw new Error('Session expired');
        }

        if (response.status === 204) return null;

        const data = await response.json().catch(() => null);
        if (!response.ok) {
            let msg = `Error ${response.status}`;
            if (data?.detail) {
                if (typeof data.detail === 'string') {
                    msg = data.detail;
                } else if (Array.isArray(data.detail)) {
                    // FastAPI validation errors: [{loc: [...], msg: "...", type: "..."}]
                    msg = data.detail.map(e => {
                        const field = e.loc?.slice(-1)[0] || '';
                        return field ? `${field}: ${e.msg}` : e.msg;
                    }).join('; ');
                } else {
                    msg = JSON.stringify(data.detail);
                }
            }
            throw new Error(msg);
        }
        return data;
    }

    async _tryRefresh() {
        try {
            const res = await fetch(`${API_BASE}/auth/refresh`, {
                method: 'POST',
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                this._accessToken = data.access_token;
                return true;
            }
        } catch (_) { /* ignore */ }
        return false;
    }

    async _downloadFile(path, filename) {
        const url = `${API_BASE}${path}`;
        const res = await fetch(url, {
            headers: this._headers(),
            credentials: 'include',
        });
        if (res.status === 401) {
            const refreshed = await this._tryRefresh();
            if (refreshed) return this._downloadFile(path, filename);
            if (this._onUnauthorized) this._onUnauthorized();
            throw new Error('Session expired');
        }
        if (!res.ok) throw new Error(`Download failed: ${res.status}`);
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
    }

    // ===== Auth =====
    async login(email, password) {
        const data = await this._request('POST', '/auth/login', { email, password });
        this._accessToken = data.access_token;
        return data;
    }

    async logout() {
        try { await this._request('POST', '/auth/logout'); } catch (_) {}
        this._accessToken = null;
    }

    async refreshToken() {
        return this._tryRefresh();
    }

    // ===== Users =====
    async getMe() {
        return this._request('GET', '/users/me');
    }

    async updateMe(data) {
        return this._request('PUT', '/users/me', data);
    }

    // ===== Timer (server-side persistence) =====
    async getTimerState() {
        return this._request('GET', '/timer');
    }

    async saveTimerState(startTime, description) {
        return this._request('PUT', '/timer', {
            start_time: startTime,
            description: description || null,
        });
    }

    async clearTimerState() {
        return this._request('DELETE', '/timer');
    }

    // ===== Personal Data Export/Import =====
    async exportPersonalData() {
        return this._request('GET', '/data/export');
    }

    async exportUserData(userId) {
        return this._request('GET', `/data/export/${userId}`);
    }

    async importPersonalData(data, mode = 'merge') {
        return this._request('POST', `/data/import?mode=${mode}`, data);
    }

    async importUserData(userId, data, mode = 'merge') {
        return this._request('POST', `/data/import/${userId}?mode=${mode}`, data);
    }

    async changePassword(currentPassword, newPassword) {
        return this._request('POST', '/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword,
        });
    }

    async exportBackup() {
        return this._downloadFile('/backup/export', 'zeittracker_backup.json');
    }

    async importBackup(file) {
        const url = `${API_BASE}/backup/import`;
        const formData = new FormData();
        formData.append('file', file);
        const config = {
            method: 'POST',
            headers: {},
            credentials: 'include',
            body: formData,
        };
        if (this._accessToken) {
            config.headers['Authorization'] = `Bearer ${this._accessToken}`;
        }
        let response;
        try {
            response = await fetch(url, config);
        } catch (err) {
            throw new Error('Network error.');
        }
        if (response.status === 401) {
            const refreshed = await this._tryRefresh();
            if (refreshed) return this.importBackup(file);
            if (this._onUnauthorized) this._onUnauthorized();
            throw new Error('Session expired');
        }
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Import failed');
        return data;
    }

    async listUsers() {
        return this._request('GET', '/users');
    }

    async createUser(data) {
        return this._request('POST', '/users', data);
    }

    async updateUser(id, data) {
        return this._request('PUT', `/users/${id}`, data);
    }

    async deleteUser(id) {
        return this._request('DELETE', `/users/${id}`);
    }

    async hardDeleteUser(id) {
        return this._request('DELETE', `/users/${id}/permanent`);
    }

    // ===== Entries =====
    async getEntries(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._request('GET', `/entries${qs ? '?' + qs : ''}`);
    }

    async createEntry(data) {
        return this._request('POST', '/entries', data);
    }

    async updateEntry(id, data) {
        return this._request('PUT', `/entries/${id}`, data);
    }

    async deleteEntry(id) {
        return this._request('DELETE', `/entries/${id}`);
    }

    async getUserEntries(userId, params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._request('GET', `/entries/user/${userId}${qs ? '?' + qs : ''}`);
    }

    // ===== Overtime =====
    async getOvertimeBalance() {
        return this._request('GET', '/overtime/balance');
    }

    async getOvertimeHistory(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._request('GET', `/overtime/history${qs ? '?' + qs : ''}`);
    }

    async useOvertime(data) {
        return this._request('POST', '/overtime/use', data);
    }

    async deleteOvertimeEntry(id) {
        return this._request('DELETE', `/overtime/${id}`);
    }

    async getUserOvertime(userId) {
        return this._request('GET', `/overtime/user/${userId}`);
    }

    // ===== Absences =====
    async getAbsences(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._request('GET', `/absences${qs ? '?' + qs : ''}`);
    }

    async createAbsence(data) {
        return this._request('POST', '/absences', data);
    }

    async deleteAbsence(id) {
        return this._request('DELETE', `/absences/${id}`);
    }

    async getUserAbsences(userId, params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._request('GET', `/absences/user/${userId}${qs ? '?' + qs : ''}`);
    }

    async getVacationBudget(year) {
        return this._request('GET', `/absences/vacation-budget?year=${year}`);
    }

    // ===== Departments =====
    async getDepartments() {
        return this._request('GET', '/departments');
    }

    async createDepartment(data) {
        return this._request('POST', '/departments', data);
    }

    async updateDepartment(id, data) {
        return this._request('PUT', `/departments/${id}`, data);
    }

    async deleteDepartment(id) {
        return this._request('DELETE', `/departments/${id}`);
    }

    // ===== Holidays =====
    async getHolidays(year) {
        return this._request('GET', `/holidays?year=${year}`);
    }

    async createHoliday(data) {
        return this._request('POST', '/holidays', data);
    }

    async deleteHoliday(id) {
        return this._request('DELETE', `/holidays/${id}`);
    }

    async autoGenerateHolidays(year) {
        return this._request('POST', `/holidays/auto-generate?year=${year}`);
    }

    // ===== Schedule =====
    async getMySchedule() {
        return this._request('GET', '/schedule');
    }

    async setMySchedule(data) {
        return this._request('POST', '/schedule', data);
    }

    async getUserSchedule(userId) {
        return this._request('GET', `/schedule/user/${userId}`);
    }

    async setUserSchedule(userId, data) {
        return this._request('PUT', `/schedule/user/${userId}`, data);
    }

    // ===== Vacation Budget =====
    async setVacationBudget(userId, totalDays, year) {
        return this._request('PUT', `/absences/vacation-budget/${userId}?year=${year}`, { total_days: totalDays });
    }

    // ===== Reports =====
    async getMonthlyReport(year, month) {
        return this._request('GET', `/reports/monthly?year=${year}&month=${month}`);
    }

    async getDepartmentReport(deptId, year, month) {
        return this._request('GET', `/reports/department/${deptId}?year=${year}&month=${month}`);
    }

    async getSystemSummary(year, month) {
        return this._request('GET', `/reports/summary?year=${year}&month=${month}`);
    }

    // ===== Export =====
    async downloadPdf(year, month) {
        const fn = `Zeiterfassung_${year}_${String(month).padStart(2, '0')}.pdf`;
        return this._downloadFile(`/export/pdf?year=${year}&month=${month}`, fn);
    }

    async downloadExcel(year, month) {
        const fn = `Zeiterfassung_${year}_${String(month).padStart(2, '0')}.xlsx`;
        return this._downloadFile(`/export/excel?year=${year}&month=${month}`, fn);
    }

    async downloadCsv(year, month) {
        const fn = `Zeiterfassung_${year}_${String(month).padStart(2, '0')}.csv`;
        return this._downloadFile(`/export/csv?year=${year}&month=${month}`, fn);
    }

    async downloadUserPdf(userId, year, month) {
        const fn = `Zeiterfassung_${userId}_${year}_${String(month).padStart(2, '0')}.pdf`;
        return this._downloadFile(`/export/pdf/${userId}?year=${year}&month=${month}`, fn);
    }

    async downloadUserExcel(userId, year, month) {
        const fn = `Zeiterfassung_${userId}_${year}_${String(month).padStart(2, '0')}.xlsx`;
        return this._downloadFile(`/export/excel/${userId}?year=${year}&month=${month}`, fn);
    }

    async downloadUserCsv(userId, year, month) {
        const fn = `Zeiterfassung_${userId}_${year}_${String(month).padStart(2, '0')}.csv`;
        return this._downloadFile(`/export/csv/${userId}?year=${year}&month=${month}`, fn);
    }

    async downloadDeptExcel(deptId, year, month) {
        const fn = `Abteilung_${deptId}_${year}_${String(month).padStart(2, '0')}.xlsx`;
        return this._downloadFile(`/export/department/${deptId}/excel?year=${year}&month=${month}`, fn);
    }
}

export const api = new ApiClient();
export default api;
