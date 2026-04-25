import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signUpUser } from "../services/api";
import { setAuthUser, clearRecommendationData } from "../services/session";

export default function SignUpPage() {
    const navigate = useNavigate();

    const [form, setForm] = useState({
        firstName: "",
        lastName: "",
        pronouns: "",
        email: "",
        password: "",
        confirmPassword: "",
    });

    const [errors, setErrors] = useState({});
    const [serverError, setServerError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const validate = () => {
        const nextErrors = {};

        if (!form.firstName.trim()) nextErrors.firstName = "First name is required.";
        if (!form.lastName.trim()) nextErrors.lastName = "Last name is required.";
        if (!form.pronouns.trim()) nextErrors.pronouns = "Please select your pronouns.";
        if (!form.email.trim()) nextErrors.email = "Email is required.";
        if (!form.password.trim()) nextErrors.password = "Password is required.";
        if (form.password.length < 8) {
            nextErrors.password = "Password must be at least 8 characters.";
        }
        if (form.confirmPassword !== form.password) {
            nextErrors.confirmPassword = "Passwords do not match.";
        }

        setErrors(nextErrors);
        return Object.keys(nextErrors).length === 0;
    };

    const handleChange = (event) => {
        setForm((prev) => ({
            ...prev,
            [event.target.name]: event.target.value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setServerError("");

        if (!validate()) return;

        try {
            setSubmitting(true);

            const result = await signUpUser(form);

            setAuthUser({
                firstName: result.firstName,
                lastName: result.lastName,
                pronouns: result.pronouns,
                email: result.email,
            });

            clearRecommendationData();

            // Go to dashboard after sign-up
            navigate("/dashboard");
        } catch (error) {
            setServerError(
                error?.response?.data?.message ||
                error?.response?.data ||
                "Could not create account."
            );
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
            <div className="card w-full max-w-md p-8">
                <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
                <p className="mt-2 text-sm text-slate-600">
                    Start getting AI-powered job recommendations tailored to your CV.
                </p>

                <form onSubmit={handleSubmit} className="mt-8 space-y-5">
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
                            {errors.firstName && (
                                <p className="mt-2 text-sm text-rose-600">{errors.firstName}</p>
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
                            {errors.lastName && (
                                <p className="mt-2 text-sm text-rose-600">{errors.lastName}</p>
                            )}
                        </div>
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
                        {errors.pronouns && (
                            <p className="mt-2 text-sm text-rose-600">{errors.pronouns}</p>
                        )}
                    </div>

                    <div>
                        <label className="label">Email</label>
                        <input
                            name="email"
                            type="email"
                            className="input"
                            value={form.email}
                            onChange={handleChange}
                            placeholder="you@example.com"
                        />
                        {errors.email && (
                            <p className="mt-2 text-sm text-rose-600">{errors.email}</p>
                        )}
                    </div>

                    <div>
                        <label className="label">Password</label>
                        <input
                            name="password"
                            type="password"
                            className="input"
                            value={form.password}
                            onChange={handleChange}
                            placeholder="Create a password"
                        />
                        {errors.password && (
                            <p className="mt-2 text-sm text-rose-600">{errors.password}</p>
                        )}
                    </div>

                    <div>
                        <label className="label">Confirm password</label>
                        <input
                            name="confirmPassword"
                            type="password"
                            className="input"
                            value={form.confirmPassword}
                            onChange={handleChange}
                            placeholder="Confirm your password"
                        />
                        {errors.confirmPassword && (
                            <p className="mt-2 text-sm text-rose-600">{errors.confirmPassword}</p>
                        )}
                    </div>

                    {serverError && (
                        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                            {serverError}
                        </div>
                    )}

                    <button type="submit" className="btn-primary w-full" disabled={submitting}>
                        {submitting ? "Creating account..." : "Create Account"}
                    </button>
                </form>

                <p className="mt-6 text-sm text-slate-600">
                    Already have an account?{" "}
                    <Link to="/signin" className="font-medium text-indigo-600 hover:text-indigo-700">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}
