/*
  Theme service.

  Handles:
  - reading the saved theme from localStorage
  - applying the theme to the root HTML element
  - validating allowed theme values
*/

const THEME_KEY = "appTheme";

/*
  Allowed theme names.
*/
export const THEMES = {
    LIGHT: "light",
    WARM: "warm",
};

/*
  Validate a candidate theme value.
*/
export function isValidTheme(theme) {
    return Object.values(THEMES).includes(theme);
}

/*
  Return the saved theme or a safe default.
*/
export function getStoredTheme() {
    const saved = localStorage.getItem(THEME_KEY);

    if (saved && isValidTheme(saved)) {
        return saved;
    }

    return THEMES.LIGHT;
}

/*
  Apply a theme to the document root and persist it.
*/
export function setTheme(theme) {
    const safeTheme = isValidTheme(theme) ? theme : THEMES.LIGHT;

    document.documentElement.setAttribute("data-theme", safeTheme);
    localStorage.setItem(THEME_KEY, safeTheme);

    return safeTheme;
}

/*
  Initialize theme on app startup.
*/
export function initializeTheme() {
    const theme = getStoredTheme();
    setTheme(theme);
    return theme;
}
