import Navbar from "../components/Navbar";

/*
  Shared page layout.
  If the sidebar is pinned, add left padding so content is not hidden.
*/
export default function PageLayout({ children }) {
    const sidebarPinned = localStorage.getItem("sidebarPinned") === "true";

    return (
        <div className="min-h-screen bg-slate-50">
            <Navbar />

            <main className={`${sidebarPinned ? "lg:pl-80" : ""}`}>
                <div className="container-shell py-10">{children}</div>
            </main>
        </div>
    );
}
