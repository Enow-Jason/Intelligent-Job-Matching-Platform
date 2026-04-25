import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../layout/PageLayout";
import UploadDropzone from "../components/UploadDropzone";
import InfoTooltip from "../components/InfoTooltip";
import ChangePasswordForm from "../components/ChangePasswordForm";
import ReturnToDashboardButton from "../components/ReturnToDashboardButton";
import useRecommendations from "../hooks/useRecommendations";
import {
    setRecommendationData,
    getAuthUser,
} from "../services/session";
import { getUserProfile, saveUserProfile } from "../services/api";

export default function ProfilePage() {
    const navigate = useNavigate();
    const { fetchRecommendations, loading, error } = useRecommendations();

    const [activeTab, setActiveTab] = useState("personal");
    const [file, setFile] = useState(null);
    const [formErrors, setFormErrors] = useState({});
    const [saveMessage, setSaveMessage] = useState("");
    const [profileLoading, setProfileLoading] = useState(true);

    const [form, setForm] = useState({
        firstName: "",
        lastName: "",
        pronouns: "",
        email: "",
        location: "",
        targetRole: "",
        yearsOfExperience: "",
        keySkills: "",
        topK: 8,
    });

    useEffect(() => {
        const authUser = getAuthUser();

        if (!authUser?.email) {
            setProfileLoading(false);
            return;
        }

        async function loadProfile() {
            try {
                const profile = await getUserProfile(authUser.email);

                setForm({
                    firstName: profile.firstName || "",
                    lastName: profile.lastName || "",
                    pronouns: profile.pronouns || "",
                    email: profile.email || "",
                    location: profile.location || "",
                    targetRole: profile.targetRole || "",
                    yearsOfExperience: profile.yearsOfExperience ?? "",
                    keySkills: profile.keySkills || "",
                    topK: profile.preferredTopK || 8,
                });
            } catch (err) {
                console.error("Failed to load profile:", err);

                setForm((prev) => ({
                    ...prev,
                    firstName: authUser.firstName || "",
                    lastName: authUser.lastName || "",
                    pronouns: authUser.pronouns || "",
                    email: authUser.email || "",
                }));
            } finally {
                setProfileLoading(false);
            }
        }

        loadProfile();
    }, []);

    const handleChange = (event) => {
        setSaveMessage("");
        setForm((prev) => ({
            ...prev,
            [event.target.name]: event.target.value,
        }));
    };

    const validate = () => {
        const nextErrors = {};

        if (!form.firstName.trim()) nextErrors.firstName = "First name is required.";
        if (!form.lastName.trim()) nextErrors.lastName = "Last name is required.";
        if (!form.pronouns.trim()) nextErrors.pronouns = "Pronouns are required.";
        if (!form.targetRole.trim()) nextErrors.targetRole = "Target role is required.";
        if (!file) nextErrors.file = "Please upload your CV.";

        const topKNumber = Number(form.topK);
        if (!form.topK || Number.isNaN(topKNumber) || topKNumber < 1 || topKNumber > 20) {
            nextErrors.topK = "Enter a number between 1 and 20.";
        }

        setFormErrors(nextErrors);
        return Object.keys(nextErrors).length === 0;
    };

    const handleSaveProfile = async () => {
        try {
            setSaveMessage("");
            await saveUserProfile(form);
            setSaveMessage("Profile saved successfully.");
        } catch (err) {
            console.error(err);
            setSaveMessage("Could not save profile.");
        }
    };

    const handleGenerateRecommendations = async () => {
        if (!validate()) return;

        try {
            await saveUserProfile(form);

            const response = await fetchRecommendations({
                ...form,
                topK: Number(form.topK),
                file,
            });

            setRecommendationData(response);
            navigate("/dashboard");
        } catch (err) {
            console.error(err);
        }
    };

    if (profileLoading) {
        return (
            <PageLayout>
                <div className="card p-8">
                    <p className="text-sm text-slate-600">Loading profile...</p>
                </div>
            </PageLayout>
        );
    }

    return (
        <PageLayout>
            <div className="mx-auto max-w-5xl">
                <ReturnToDashboardButton />

                <div>
                    <h1 className="section-title">Your profile</h1>
                    <p className="section-subtitle">
                        Manage your personal details, security settings, and recommendation preferences.
                    </p>
                </div>

                <div className="mt-8 flex gap-3 border-b border-slate-200">
                    <button
                        type="button"
                        onClick={() => setActiveTab("personal")}
                        className={`border-b-2 px-4 py-3 text-sm font-medium ${
                            activeTab === "personal"
                                ? "border-indigo-600 text-indigo-600"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        Personal Information
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveTab("career")}
                        className={`border-b-2 px-4 py-3 text-sm font-medium ${
                            activeTab === "career"
                                ? "border-indigo-600 text-indigo-600"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        Recommendation Profile
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveTab("security")}
                        className={`border-b-2 px-4 py-3 text-sm font-medium ${
                            activeTab === "security"
                                ? "border-indigo-600 text-indigo-600"
                                : "border-transparent text-slate-500 hover:text-slate-800"
                        }`}
                    >
                        Security
                    </button>
                </div>

                {saveMessage && (
                    <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                        {saveMessage}
                    </div>
                )}

                <div className="mt-8">
                    {activeTab === "personal" && (
                        <div className="card p-6 sm:p-8">
                            <div className="grid gap-5 sm:grid-cols-2">
                                <div>
                                    <label className="label">First name</label>
                                    <input
                                        name="firstName"
                                        className="input"
                                        value={form.firstName}
                                        onChange={handleChange}
                                        placeholder="First name"
                                    />
                                    {formErrors.firstName && (
                                        <p className="mt-2 text-sm text-rose-600">{formErrors.firstName}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="label">Last name</label>
                                    <input
                                        name="lastName"
                                        className="input"
                                        value={form.lastName}
                                        onChange={handleChange}
                                        placeholder="Last name"
                                    />
                                    {formErrors.lastName && (
                                        <p className="mt-2 text-sm text-rose-600">{formErrors.lastName}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="label">Pronouns</label>
                                    <select
                                        name="pronouns"
                                        className="input"
                                        value={form.pronouns}
                                        onChange={handleChange}
                                    >
                                        <option value="">Select pronouns</option>
                                        <option value="She/Her">She/Her</option>
                                        <option value="He/Him">He/Him</option>
                                        <option value="They/Them">They/Them</option>
                                        <option value="Prefer not to say">Prefer not to say</option>
                                    </select>
                                    {formErrors.pronouns && (
                                        <p className="mt-2 text-sm text-rose-600">{formErrors.pronouns}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="label">Email</label>
                                    <input
                                        name="email"
                                        className="input bg-slate-50"
                                        value={form.email}
                                        readOnly
                                    />
                                </div>

                                <div className="sm:col-span-2">
                                    <label className="label">Location</label>
                                    <input
                                        name="location"
                                        className="input"
                                        value={form.location}
                                        onChange={handleChange}
                                        placeholder="e.g. Leicester, UK"
                                    />
                                </div>
                            </div>

                            <div className="mt-6">
                                <button
                                    type="button"
                                    onClick={handleSaveProfile}
                                    className="btn-secondary"
                                >
                                    Save Personal Information
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === "career" && (
                        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                            <div className="card p-6 sm:p-8">
                                <div className="grid gap-5">
                                    <div>
                                        <label className="label flex items-center">
                                            Target role
                                            <InfoTooltip text="This helps the recommendation engine understand your intended role direction when ranking jobs against your uploaded CV." />
                                        </label>
                                        <input
                                            name="targetRole"
                                            className="input"
                                            value={form.targetRole}
                                            onChange={handleChange}
                                            placeholder="e.g. Graduate Cloud Engineer"
                                        />
                                        {formErrors.targetRole && (
                                            <p className="mt-2 text-sm text-rose-600">{formErrors.targetRole}</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="label flex items-center">
                                            Years of experience
                                            <InfoTooltip text="This helps the system avoid ranking roles that are unrealistically senior for your current stage." />
                                        </label>
                                        <input
                                            name="yearsOfExperience"
                                            type="number"
                                            min="0"
                                            className="input"
                                            value={form.yearsOfExperience}
                                            onChange={handleChange}
                                            placeholder="0"
                                        />
                                    </div>

                                    <div>
                                        <label className="label flex items-center">
                                            Key skills
                                            <InfoTooltip text="These skills support the uploaded CV and help improve match explanations, skill gap insights, and overall recommendation relevance." />
                                        </label>
                                        <textarea
                                            name="keySkills"
                                            rows="4"
                                            className="input resize-none"
                                            value={form.keySkills}
                                            onChange={handleChange}
                                            placeholder="e.g. AWS, Python, Terraform, Docker"
                                        />
                                    </div>

                                    <div>
                                        <label className="label flex items-center">
                                            Number of recommendations
                                            <InfoTooltip text="Enter how many jobs you want to see. Use a value between 1 and 20 depending on whether you want a short shortlist or a broader set of options." />
                                        </label>
                                        <input
                                            name="topK"
                                            type="number"
                                            min="1"
                                            max="20"
                                            className="input"
                                            value={form.topK}
                                            onChange={handleChange}
                                            placeholder="e.g. 8"
                                        />
                                        {formErrors.topK && (
                                            <p className="mt-2 text-sm text-rose-600">{formErrors.topK}</p>
                                        )}
                                    </div>
                                </div>

                                <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                                    <button
                                        type="button"
                                        onClick={handleSaveProfile}
                                        className="btn-secondary"
                                    >
                                        Save Recommendation Profile
                                    </button>

                                    <button
                                        type="button"
                                        onClick={handleGenerateRecommendations}
                                        className="btn-primary"
                                        disabled={loading}
                                    >
                                        {loading ? "Generating Recommendations..." : "Generate Recommendations"}
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-5">
                                <UploadDropzone file={file} onFileChange={setFile} />
                                {formErrors.file && (
                                    <p className="text-sm text-rose-600">{formErrors.file}</p>
                                )}

                                {error && (
                                    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                                        {error}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === "security" && <ChangePasswordForm />}
                </div>
            </div>
        </PageLayout>
    );
}
