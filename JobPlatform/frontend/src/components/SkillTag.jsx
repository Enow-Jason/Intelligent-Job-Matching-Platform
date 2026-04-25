export default function SkillTag({ label, variant = "neutral" }) {
    const styles = {
        neutral: "bg-slate-100 text-slate-700",
        success: "bg-emerald-100 text-emerald-700",
        warning: "bg-amber-100 text-amber-700",
    };

    return (
        <span
            className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${styles[variant]}`}
        >
      {label}
    </span>
    );
}
