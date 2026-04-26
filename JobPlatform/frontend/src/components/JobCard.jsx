import { Link } from "react-router-dom";
import { useState } from "react";
import MatchScore from "./MatchScore";
import SkillTag from "./SkillTag";
import {
    isJobBookmarked,
    toggleBookmarkedJob,
} from "../services/session";

/*
  Job card for recommendation results.
  Uses richer dataset fields and backend-generated explanation bullets.
*/
export default function JobCard({ job }) {
    const [bookmarked, setBookmarked] = useState(isJobBookmarked(job.job_id));

    const handleToggleBookmark = () => {
        toggleBookmarkedJob(job);
        setBookmarked((prev) => !prev);
    };

    // Use backend-generated personalised bullets when available
    const whyMatches = Array.isArray(job.why_recommended_bullets)
        ? job.why_recommended_bullets.slice(0, 3)
        : [];

    // Keep only the cleanest few visible skill chips
    const visibleMatchedSkills = (job.matched_skills || []).slice(0, 3);
    const visibleMissingSkills = (job.missing_skills_top10 || []).slice(0, 2);

    return (
        <article className="card p-6">
            <div className="flex flex-col gap-5">
                {/* Top row */}
                <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                        {/* Prefer role for display, since that is now the stronger field */}
                        <h3 className="text-xl font-semibold text-slate-900">
                            {job.role || job.job_title}
                        </h3>

                        <p className="mt-1 text-sm font-medium text-slate-700">
                            {job.company_name}
                        </p>

                        <p className="mt-1 text-sm text-slate-600">
                            {job.location}, {job.country} · {job.work_type}
                            {job.salary_range && (
                                <p className="mt-1 text-sm font-medium text-emerald-700">
                                    Salary: {job.salary_range}
                                </p>
                            )}
                        </p>

                        <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                            Source: {job.job_portal}
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            type="button"
                            onClick={handleToggleBookmark}
                            className={`inline-flex h-10 w-10 items-center justify-center rounded-xl border transition ${
                                bookmarked
                                    ? "border-amber-300 bg-amber-50 text-amber-600"
                                    : "border-slate-200 bg-white text-slate-500 hover:bg-slate-100"
                            }`}
                            aria-label={bookmarked ? "Remove bookmark" : "Bookmark job"}
                            title={bookmarked ? "Remove bookmark" : "Save job"}
                        >
                            {bookmarked ? "★" : "☆"}
                        </button>
                    </div>
                </div>

                {/* Description snippet */}
                <p className="text-sm leading-6 text-slate-700">
                    {job.description_snippet}
                </p>

                {/* Personalised explanation bullets */}
                {whyMatches.length > 0 && (
                    <ul className="space-y-2 text-sm text-slate-700">
                        {whyMatches.map((point) => (
                            <li key={point} className="flex items-start gap-2">
                                <span className="mt-1 text-emerald-600">•</span>
                                <span>{point}</span>
                            </li>
                        ))}
                    </ul>
                )}

                {/* Skill chips */}
                <div className="flex flex-wrap gap-2">
                    {visibleMatchedSkills.map((skill) => (
                        <SkillTag key={skill} label={skill} variant="success" />
                    ))}

                    {visibleMissingSkills.map((skill) => (
                        <SkillTag key={skill} label={skill} variant="warning" />
                    ))}
                </div>

                {/* Bottom row */}
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="w-full lg:max-w-xs">
                        <MatchScore score={job.final_score || job.semantic_score || 0} />
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row">
                        <Link
                            to={`/jobs/${job.job_id}`}
                            state={{ job }}
                            className="btn-primary"
                        >
                            View details
                        </Link>
                    </div>
                </div>
            </div>
        </article>
    );
}
