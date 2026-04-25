import { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
    isAuthenticated,
    clearUserSession,
} from "../services/session";
import {
    THEMES,
    getStoredTheme,
    setTheme,
} from "../services/theme";

/*
  Navbar with:
  - left-side hamburger menu
  - centered site name
  - optional pinned sidebar mode
  - logout on navbar and in drawer
  - theme selector in the drawer
*/
export default function Navbar() {
    const navigate = useNavigate();
    const loggedIn = isAuthenticated();

    const [menuOpen, setMenuOpen] = useState(false);
    const [sidebarPinned, setSidebarPinned] = useState(() => {
        return localStorage.getItem("sidebarPinned") === "true";
    });
    const [selectedTheme, setSelectedTheme] = useState(getStoredTheme());

    useEffect(() => {
        localStorage.setItem("sidebarPinned", String(sidebarPinned));
    }, [sidebarPinned]);

    const navClass = ({ isActive }) =>
        `block rounded-xl px-4 py-3 text-sm font-medium transition ${
            isActive
                ? "bg-indigo-50 text-indigo-600"
                : "theme-text-soft hover:bg-slate-100 hover:text-slate-900"
        }`;

    const handleLogout = () => {
        clearUserSession();
        setMenuOpen(false);
        navigate("/signin");
    };

    const handleThemeChange = (event) => {
        const nextTheme = event.target.value;
        setSelectedTheme(setTheme(nextTheme));
    };

    const drawerContent = (
        <>
            <div className="flex h-16 items-center justify-between border-b theme-border px-5">
                <div>
                    <p className="text-sm font-semibold theme-text">Menu</p>
                    <p className="text-xs theme-text-muted">
                        Navigation and preferences
                    </p>
                </div>

                {!sidebarPinned && (
                    <button
                        type="button"
                        onClick={() => setMenuOpen(false)}
                        className="inline-flex h-9 w-9 items-center justify-center rounded-lg border theme-border theme-surface-muted theme-text-soft hover:bg-slate-100"
                        aria-label="Close navigation menu"
                    >
                        ✕
                    </button>
                )}
            </div>

            <div className="border-b theme-border px-4 py-4">
                <label className="flex items-center justify-between gap-4 rounded-xl theme-surface-muted px-4 py-3">
          <span className="text-sm font-medium theme-text-soft">
            Keep menu open
          </span>

                    <input
                        type="checkbox"
                        checked={sidebarPinned}
                        onChange={(e) => {
                            const next = e.target.checked;
                            setSidebarPinned(next);

                            if (!next) {
                                setMenuOpen(false);
                            }
                        }}
                        className="h-4 w-4 accent-indigo-600"
                    />
                </label>
            </div>

            {/* Theme selection */}
            <div className="border-b theme-border px-4 py-4">
                <label className="label">Theme</label>
                <select
                    className="input"
                    value={selectedTheme}
                    onChange={handleThemeChange}
                >
                    <option value={THEMES.LIGHT}>Light</option>
                    <option value={THEMES.WARM}>Warm</option>
                </select>
            </div>

            <nav className="flex flex-col gap-4 p-4">
                <NavLink
                    to="/dashboard"
                    className={navClass}
                    onClick={() => !sidebarPinned && setMenuOpen(false)}
                >
                    Dashboard
                </NavLink>

                <NavLink
                    to="/profile"
                    className={navClass}
                    onClick={() => !sidebarPinned && setMenuOpen(false)}
                >
                    Profile
                </NavLink>

                <NavLink
                    to="/saved-jobs"
                    className={navClass}
                    onClick={() => !sidebarPinned && setMenuOpen(false)}
                >
                    Saved Jobs
                </NavLink>

                <button
                    type="button"
                    onClick={handleLogout}
                    className="mt-2 block w-full rounded-xl px-4 py-3 text-left text-sm font-medium text-rose-600 transition hover:bg-rose-50 hover:text-rose-700"
                >
                    Logout
                </button>
            </nav>
        </>
    );

    return (
        <>
            <header className="border-b theme-border bg-[color:var(--surface)]/90 backdrop-blur">
                <div className="container-shell relative flex h-16 items-center justify-between">
                    <div className="-ml-2 flex items-center">
                        {loggedIn && !sidebarPinned && (
                            <button
                                type="button"
                                onClick={() => setMenuOpen(true)}
                                className="inline-flex h-10 w-10 items-center justify-center rounded-xl border theme-border bg-[color:var(--surface)] theme-text-soft transition hover:bg-[color:var(--surface-muted)]"
                                aria-label="Open navigation menu"
                            >
                                ☰
                            </button>
                        )}
                    </div>

                    <div className="pointer-events-none absolute inset-x-0 flex justify-center">
                        <Link
                            to={loggedIn ? "/dashboard" : "/"}
                            className="pointer-events-auto text-lg font-bold tracking-tight theme-text"
                        >
                            GradMatch AI
                        </Link>
                    </div>

                    <div className="ml-auto mr-1 flex items-center">
                        {loggedIn ? (
                            <button
                                type="button"
                                onClick={handleLogout}
                                className="inline-flex items-center justify-center rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:bg-rose-100 hover:text-rose-700"
                            >
                                Logout
                            </button>
                        ) : (
                            <div className="flex items-center gap-3">
                                <Link to="/signin" className="btn-secondary">
                                    Sign In
                                </Link>
                                <Link to="/signup" className="btn-primary">
                                    Get Started
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {loggedIn && !sidebarPinned && menuOpen && (
                <div
                    className="fixed inset-0 z-40 bg-slate-900/30"
                    onClick={() => setMenuOpen(false)}
                />
            )}

            {loggedIn && !sidebarPinned && (
                <aside
                    className={`fixed left-0 top-0 z-50 h-full w-80 transform border-r theme-border bg-[color:var(--surface)] shadow-soft transition-transform duration-300 ${
                        menuOpen ? "translate-x-0" : "-translate-x-full"
                    }`}
                >
                    {drawerContent}
                </aside>
            )}

            {loggedIn && sidebarPinned && (
                <aside className="fixed left-0 top-16 z-30 h-[calc(100%-4rem)] w-80 border-r theme-border bg-[color:var(--surface)]">
                    {drawerContent}
                </aside>
            )}
        </>
    );
}
