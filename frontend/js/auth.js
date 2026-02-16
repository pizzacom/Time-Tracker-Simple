/* ==========================================
   Auth Module - Login/Logout/Session
   ========================================== */
import { api } from './api.js';

const AUTH_KEY = 'zeittracker_auth';
const INACTIVITY_TIMEOUT = 15 * 60 * 1000; // 15 min
const WARNING_BEFORE = 2 * 60 * 1000;       // warn 2 min before
const TOKEN_LIFETIME = 15 * 60 * 1000;      // access token = 15 min

class AuthManager {
    constructor() {
        this._user = null;
        this._onLoginRequired = null;
        this._onLoginSuccess = null;
        this._inactivityTimer = null;
        this._warningTimer = null;
        this._sessionInterval = null;
        this._loginTimestamp = null;
    }

    get user() { return this._user; }
    get isLoggedIn() { return !!this._user; }
    get isAdmin() { return this._user?.role === 'admin'; }
    get isLeader() { return this._user?.role === 'abteilungsleiter'; }
    get isWorker() { return this._user?.role === 'worker'; }
    get canManageUsers() { return this.isAdmin || this.isLeader; }

    set onLoginRequired(cb) { this._onLoginRequired = cb; }
    set onLoginSuccess(cb) { this._onLoginSuccess = cb; }

    _saveSession(accessToken) {
        sessionStorage.setItem(AUTH_KEY, accessToken);
        this._loginTimestamp = Date.now();
        sessionStorage.setItem(AUTH_KEY + '_ts', String(this._loginTimestamp));
    }

    _loadSession() {
        this._loginTimestamp = parseInt(sessionStorage.getItem(AUTH_KEY + '_ts')) || null;
        return sessionStorage.getItem(AUTH_KEY);
    }

    _clearSession() {
        sessionStorage.removeItem(AUTH_KEY);
        sessionStorage.removeItem(AUTH_KEY + '_ts');
        this._user = null;
        this._loginTimestamp = null;
        api.accessToken = null;
        this._stopTimers();
    }

    // ===== Inactivity / Session Timer =====
    _startTimers() {
        this._stopTimers();
        this._resetInactivity();

        // Listen for user activity
        const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];
        this._activityHandler = () => this._resetInactivity();
        events.forEach(ev => document.addEventListener(ev, this._activityHandler, { passive: true }));

        // Session countdown (update every second)
        this._sessionInterval = setInterval(() => this._updateSessionDisplay(), 1000);
        // Show timer immediately
        this._updateSessionDisplay();

        // Click-to-renew handler on session timer
        const timerEl = document.getElementById('sessionTimer');
        if (timerEl) {
            this._timerClickHandler = async () => {
                const refreshed = await api.refreshToken();
                if (refreshed) {
                    this._saveSession(api.accessToken);
                    timerEl.classList.remove('warning');
                }
            };
            timerEl.addEventListener('click', this._timerClickHandler);
        }
    }

    _stopTimers() {
        if (this._inactivityTimer) { clearTimeout(this._inactivityTimer); this._inactivityTimer = null; }
        if (this._warningTimer) { clearTimeout(this._warningTimer); this._warningTimer = null; }
        if (this._sessionInterval) { clearInterval(this._sessionInterval); this._sessionInterval = null; }
        if (this._activityHandler) {
            ['mousedown', 'keydown', 'touchstart', 'scroll'].forEach(ev =>
                document.removeEventListener(ev, this._activityHandler)
            );
            this._activityHandler = null;
        }
        const timerEl = document.getElementById('sessionTimer');
        if (timerEl) {
            timerEl.classList.remove('visible', 'warning');
            if (this._timerClickHandler) {
                timerEl.removeEventListener('click', this._timerClickHandler);
                this._timerClickHandler = null;
            }
        }
    }

    _resetInactivity() {
        if (this._inactivityTimer) clearTimeout(this._inactivityTimer);
        if (this._warningTimer) clearTimeout(this._warningTimer);

        // Warning before logout
        this._warningTimer = setTimeout(() => {
            const timerEl = document.getElementById('sessionTimer');
            if (timerEl) { timerEl.classList.add('warning'); }
        }, INACTIVITY_TIMEOUT - WARNING_BEFORE);

        // Auto-logout
        this._inactivityTimer = setTimeout(() => {
            this.logout();
        }, INACTIVITY_TIMEOUT);

        // Remove warning class on activity
        const timerEl = document.getElementById('sessionTimer');
        if (timerEl) timerEl.classList.remove('warning');

        // Reset token timestamp on activity (we'll refresh token proactively)
        this._refreshTokenIfNeeded();
    }

    async _refreshTokenIfNeeded() {
        if (!this._loginTimestamp) return;
        const elapsed = Date.now() - this._loginTimestamp;
        // Refresh token if > 12 min old (before 15 min expiry)
        if (elapsed > TOKEN_LIFETIME - 3 * 60 * 1000) {
            const refreshed = await api.refreshToken();
            if (refreshed) {
                this._saveSession(api.accessToken);
            }
        }
    }

    _updateSessionDisplay() {
        const timerEl = document.getElementById('sessionTimer');
        if (!timerEl || !this._loginTimestamp) return;
        timerEl.classList.add('visible');
        const elapsed = Date.now() - this._loginTimestamp;
        const remaining = Math.max(0, TOKEN_LIFETIME - elapsed);
        const min = Math.floor(remaining / 60000);
        const sec = Math.floor((remaining % 60000) / 1000);
        timerEl.textContent = `${min}:${String(sec).padStart(2, '0')}`;
        if (remaining < WARNING_BEFORE) {
            timerEl.classList.add('warning');
        }
    }

    async init() {
        // Set up unauthorized handler
        api.onUnauthorized = () => {
            this._clearSession();
            if (this._onLoginRequired) this._onLoginRequired();
        };

        // Try to restore session
        const token = this._loadSession();
        if (token) {
            api.accessToken = token;
            try {
                this._user = await api.getMe();
                this._startTimers();
                return true;
            } catch (_) {
                // Token expired, try refresh
                const refreshed = await api.refreshToken();
                if (refreshed) {
                    this._saveSession(api.accessToken);
                    try {
                        this._user = await api.getMe();
                        this._startTimers();
                        return true;
                    } catch (_) { /* fall through */ }
                }
            }
        } else {
            // No saved token - try refresh cookie
            const refreshed = await api.refreshToken();
            if (refreshed) {
                this._saveSession(api.accessToken);
                try {
                    this._user = await api.getMe();
                    this._startTimers();
                    return true;
                } catch (_) { /* fall through */ }
            }
        }

        this._clearSession();
        return false;
    }

    async login(email, password) {
        const data = await api.login(email, password);
        this._saveSession(data.access_token);
        this._user = await api.getMe();
        this._startTimers();
        if (this._onLoginSuccess) this._onLoginSuccess(this._user);
        return this._user;
    }

    async logout() {
        await api.logout();
        this._clearSession();
        if (this._onLoginRequired) this._onLoginRequired();
    }

    async refreshProfile() {
        this._user = await api.getMe();
        return this._user;
    }
}

export const auth = new AuthManager();
export default auth;
