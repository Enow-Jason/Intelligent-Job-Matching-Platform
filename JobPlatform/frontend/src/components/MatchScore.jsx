export default function MatchScore({ score = 0 }) {
    // Convert 0-1 backend score into percentage for UI
    const percentage = Math.round(score * 100);

    return (
        <div className="w-full">
            <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Match Score
        </span>
                <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
          {percentage}%
        </span>
            </div>

            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                    className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}
