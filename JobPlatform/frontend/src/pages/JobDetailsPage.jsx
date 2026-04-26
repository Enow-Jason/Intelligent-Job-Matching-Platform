import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import PageLayout from "../layout/PageLayout";
import SkillTag from "../components/SkillTag";
import MatchScore from "../components/MatchScore";
import ReturnToDashboardButton from "../components/ReturnToDashboardButton";
import {
    isJobBookmarked,
    toggleBookmarkedJob,
} from "../services/session";

/*
  Job details page for a selected recommendation result.
  Uses backend-generated personalised explanation bullets.
*/
export default function JobDetailsPage() {
    const { jobId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    const job = location.state?.job;

    const [bookmarked, setBookmarked] = useState(
        job ? isJobBookmarked(job.job_id) : false
    );

    if (!job) {
        return (
            <PageLayout>
                <div className="card p-8">
                    <ReturnToDashboardButton />
                    <h1 className="text-xl font-semibold text-slate-900">Job not found</h1>
                    <p className="mt-2 text-sm text-slate-600">
                        We could not load details for job ID: {jobId}
                    </p>
                    <button onClick={() => navigate("/dashboard")} className="btn-primary mt-6">
                        Back to dashboard
                    </button>
                </div>
            </PageLayout>
        );
    }

    const handleToggleBookmark = () => {
        toggleBookmarkedJob(job);
        setBookmarked((prev) => !prev);
    };

    const whyRecommended = Array.isArray(job.why_recommended_bullets)
        ? job.why_recommended_bullets
        : [];

    const visibleMatchedSkills = (job.matched_skills || []).slice(0, 6);
    const visibleMissingSkills = (job.missing_skills_top10 || []).slice(0, 6);

    return (
        <PageLayout>
            <ReturnToDashboardButton />

            <div className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
                <div className="space-y-8">
                    <div className="card p-8">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                {/* Prefer role as the main displayed label */}
                                <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                                    {job.role || job.job_title}
                                </h1>

                                {/* Keep job title visible as secondary context if different */}
                                {job.job_title && job.job_title !== job.role && (
                                    <p className="mt-2 text-sm text-slate-500">
                                        Posting title: {job.job_title}
                                    </p>
                                )}

                                <p className="mt-2 text-sm font-medium text-slate-700">
                                    {job.company_name}
                                </p>

                                <p className="mt-1 text-sm text-slate-600">
                                    {job.location}, {job.country} · {job.work_type}
                                </p>

                                <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                                    Source: {job.job_portal}
                                </p>
                            </div>

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

                        <div className="mt-6 grid gap-4 sm:grid-cols-2">
                            <div>
                                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                    Experience
                                </p>
                                <p className="mt-1 text-sm text-slate-800">
                                    {job.experience || "Not specified"}
                                </p>
                            </div>

                            <div>
                                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                    Qualifications
                                </p>
                                <p className="mt-1 text-sm text-slate-800">
                                    {job.qualifications || "Not specified"}
                                </p>
                            </div>
                        </div>

                        <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                Salary
                            </p>
                            <p className="mt-1 text-sm text-slate-800">
                                {job.salary_range || "Not specified"}
                            </p>
                        </div>

                        <div className="mt-8">
                            <h2 className="text-lg font-semibold text-slate-900">Job description</h2>
                            <p className="mt-3 text-sm leading-7 text-slate-700">
                                {job.job_description}
                            </p>
                        </div>
                    </div>

                    <div className="card p-8">
                        <h2 className="text-lg font-semibold text-slate-900">
                            Why this was recommended
                        </h2>

                        {whyRecommended.length > 0 ? (
                            <ul className="mt-4 space-y-3 text-sm text-slate-700">
                                {whyRecommended.map((point) => (
                                    <li key={point}>• {point}</li>
                                ))}
                            </ul>
                        ) : (
                            <p className="mt-4 text-sm text-slate-600">
                                This role was recommended because it is semantically close to the content of your CV.
                            </p>
                        )}

                        {visibleMatchedSkills.length > 0 && (
                            <div className="mt-5 flex flex-wrap gap-2">
                                {visibleMatchedSkills.map((skill) => (
                                    <SkillTag key={skill} label={skill} variant="success" />
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="card p-8">
                        <h2 className="text-lg font-semibold text-slate-900">
                            Skill gaps and suggested learning
                        </h2>

                        <p className="mt-3 text-sm text-slate-600">
                            These are the main skills you may want to strengthen to improve fit for this role.
                        </p>

                        <div className="mt-5 flex flex-wrap gap-2">
                            {visibleMissingSkills.map((skill) => (
                                <SkillTag key={skill} label={skill} variant="warning" />
                            ))}
                        </div>
                    </div>
                </div>

                <aside className="space-y-6">
                    <div className="card p-6">
                        <MatchScore score={job.final_score || job.semantic_score || 0} />

                        <a
                            href="#"
                            onClick={(e) => e.preventDefault()}
                            className="btn-primary mt-6 w-full"
                        >
                            View source
                        </a>
                    </div>
                </aside>
            </div>
        </PageLayout>
    );
}
