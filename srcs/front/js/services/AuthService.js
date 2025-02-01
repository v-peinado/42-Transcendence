import { AuthCore } from './auth/AuthCore.js';
import { AuthUtils } from './auth/AuthUtils.js';
import { AuthGDPR } from './auth/AuthGDPR.js';
import { AuthProfile } from './auth/AuthProfile.js';
import { Auth42 } from './auth/Auth42.js';
import { Auth2FA } from './auth/Auth2FA.js';
import { AuthEmail } from './auth/AuthEmail.js';
import { AuthPassword } from './auth/AuthPassword.js';
import { AuthRegister } from './auth/AuthRegister.js';

class AuthService {
    static API_URL = '/api';

    // Core auth methods
    static login = AuthCore.login;
    static logout = AuthCore.logout;
    static register = AuthRegister.register;

    // Utility methods
    static clearSession = AuthUtils.clearSession;
    static clearAllCookies = AuthUtils.clearAllCookies;
    static getCSRFToken = AuthUtils.getCSRFToken;
    static mapBackendError = AuthUtils.mapBackendError;

    // Delegación a otros servicios
    static getGDPRSettings = AuthGDPR.getGDPRSettings;
    static updateGDPRSettings = AuthGDPR.updateGDPRSettings;
    static downloadUserData = AuthGDPR.downloadUserData;

    static getUserProfile = AuthProfile.getUserProfile;
    static updateProfile = AuthProfile.updateProfile;
    static updateProfileImage = AuthProfile.updateProfileImage;
    static deleteAccount = AuthProfile.deleteAccount;

    // 42 metods
    static get42AuthUrl = Auth42.get42AuthUrl;
    static handle42Callback = Auth42.handle42Callback;
    static handleFortyTwoCallback = Auth42.handleFortyTwoCallback;

    static enable2FA = Auth2FA.enable2FA;
    static disable2FA = Auth2FA.disable2FA;
    static verify2FACode = Auth2FA.verify2FACode;
    static generateQR = Auth2FA.generateQR;
    static validateQR = Auth2FA.validateQR;

    // 
    static verifyEmail = AuthEmail.verifyEmail;
    static verifyEmailChange = AuthEmail.verifyEmailChange;
    
    static requestPasswordReset = AuthPassword.requestPasswordReset;
    static resetPassword = AuthPassword.resetPassword;
}

export default AuthService;
