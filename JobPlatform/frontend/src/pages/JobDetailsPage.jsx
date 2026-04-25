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
*/
export default function JobDetailsPage() {
    const { jobId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    const job = location.state?.job;
    const profile = location.state?.profile;

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

    const whyRecommended = [];

    if (profile?.inferred_role && job?.role) {
        whyRecommended.push(
            `Your uploaded resume is most aligned with roles similar to ${job.role}.`
        );
    }

    if (job.matched_skills?.length) {
        whyRecommended.push(
            `Matched skills include ${job.matched_skills.slice(0, 3).join(", ")}.`
        );
    }

    if (job.experience) {
        whyRecommended.push(
            `This opportunity expects ${job.experience}, which was considered during reranking.`
        );
    }

    return (
        <PageLayout>
            <ReturnToDashboardButton />

            <div className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
                <div className="space-y-8">
                    <div className="card p-8">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                                    {job.job_title}
                                </h1>

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

                        <ul className="mt-4 space-y-3 text-sm text-slate-700">
                            {whyRecommended.map((point) => (
                                <li key={point}>• {point}</li>
                            ))}
                        </ul>

                        <div className="mt-5 flex flex-wrap gap-2">
                            {(job.matched_skills || []).map((skill) => (
                                <SkillTag key={skill} label={skill} variant="success" />
                            ))}
                        </div>
                    </div>

                    <div className="card p-8">
                        <h2 className="text-lg font-semibold text-slate-900">
                            Skill gaps and suggested learning
                        </h2>

                        <p className="mt-3 text-sm text-slate-600">
                            These are the main skills you may want to strengthen to improve fit for this role.
                        </p>

                        <div className="mt-5 flex flex-wrap gap-2">
                            {(job.missing_skills_top10 || []).map((skill) => (
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
