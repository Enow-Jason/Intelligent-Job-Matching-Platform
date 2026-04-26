/*
  Theme service.

  Handles:
  - reading the saved theme from localStorage
  - applying the theme to the root HTML element
  - validating allowed theme values
  - storing theme per logged-in user
*/

const THEME_KEY = "appTheme";

export const THEMES = {
    LIGHT: "light",
    WARM: "warm",
};

export function isValidTheme(theme) {
    return Object.values(THEMES).includes(theme);
}

/*
  Read the current logged-in user directly from localStorage
  so theme storage is scoped per account.
*/
function getCurrentUserEmail() {
    try {
        const raw = localStorage.getItem("authUser");
        if (!raw) return null;

        const user = JSON.parse(raw);
        return user?.email?.toLowerCase()?.trim() || null;
    } catch (error) {
        return null;
    }
}

function getScopedThemeKey() {
    const email = getCurrentUserEmail();
    return email ? `${THEME_KEY}:${email}` : `${THEME_KEY}:anonymous`;
}

export function getStoredTheme() {
    const saved = localStorage.getItem(getScopedThemeKey());

    if (saved && isValidTheme(saved)) {
        return saved;
    }

    return THEMES.LIGHT;
}

export function setTheme(theme) {
    const safeTheme = isValidTheme(theme) ? theme : THEMES.LIGHT;

    document.documentElement.setAttribute("data-theme", safeTheme);
    localStorage.setItem(getScopedThemeKey(), safeTheme);

    return safeTheme;
}

export function initializeTheme() {
    const theme = getStoredTheme();
    setTheme(theme);
    return theme;
}
