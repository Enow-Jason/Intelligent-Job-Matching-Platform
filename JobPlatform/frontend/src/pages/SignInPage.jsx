import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signInUser } from "../services/api";
import { setAuthUser, clearRecommendationData } from "../services/session";

export default function SignInPage() {
    const navigate = useNavigate();

    const [form, setForm] = useState({
        email: "",
        password: "",
    });

    const [errors, setErrors] = useState({});
    const [serverError, setServerError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const validate = () => {
        const nextErrors = {};

        if (!form.email.trim()) nextErrors.email = "Email is required.";
        if (!form.password.trim()) nextErrors.password = "Password is required.";

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

            const result = await signInUser(form);

            setAuthUser({
                firstName: result.firstName,
                lastName: result.lastName,
                pronouns: result.pronouns,
                email: result.email,
            });

            clearRecommendationData();

            // Go to dashboard after sign-in
            navigate("/dashboard");
        } catch (error) {
            setServerError(
                error?.response?.data?.message ||
                error?.response?.data ||
                "Could not sign in with those credentials."
            );
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
            <div className="card w-full max-w-md p-8">
                <h1 className="text-2xl font-bold text-slate-900">Welcome back</h1>
                <p className="mt-2 text-sm text-slate-600">
                    Sign in to continue managing your recommendations.
                </p>

                <form onSubmit={handleSubmit} className="mt-8 space-y-5">
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
                            placeholder="Enter your password"
                        />
                        {errors.password && (
                            <p className="mt-2 text-sm text-rose-600">{errors.password}</p>
                        )}
                    </div>

                    {serverError && (
                        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                            {serverError}
                        </div>
                    )}

                    <button type="submit" className="btn-primary w-full" disabled={submitting}>
                        {submitting ? "Signing in..." : "Sign In"}
                    </button>
                </form>

                <p className="mt-6 text-sm text-slate-600">
                    Don’t have an account?{" "}
                    <Link to="/signup" className="font-medium text-indigo-600 hover:text-indigo-700">
                        Create one
                    </Link>
                </p>
            </div>
        </div>
    );
}
