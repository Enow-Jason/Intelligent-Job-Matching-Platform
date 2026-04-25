import { useState } from "react";
import { changeUserPassword } from "../services/api";
import { getAuthUser } from "../services/session";

/*
  Form for changing a local account password.
*/
export default function ChangePasswordForm() {
    const authUser = getAuthUser();

    const [form, setForm] = useState({
        currentPassword: "",
        newPassword: "",
        confirmNewPassword: "",
    });

    const [errors, setErrors] = useState({});
    const [serverMessage, setServerMessage] = useState("");
    const [serverError, setServerError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const handleChange = (event) => {
        setServerMessage("");
        setServerError("");

        setForm((prev) => ({
            ...prev,
            [event.target.name]: event.target.value,
        }));
    };

    const validate = () => {
        const nextErrors = {};

        if (!form.currentPassword.trim()) {
            nextErrors.currentPassword = "Current password is required.";
        }

        if (!form.newPassword.trim()) {
            nextErrors.newPassword = "New password is required.";
        } else if (form.newPassword.length < 8) {
            nextErrors.newPassword = "New password must be at least 8 characters.";
        }

        if (form.confirmNewPassword !== form.newPassword) {
            nextErrors.confirmNewPassword = "New passwords do not match.";
        }

        setErrors(nextErrors);
        return Object.keys(nextErrors).length === 0;
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setServerMessage("");
        setServerError("");

        if (!validate()) return;

        try {
            setSubmitting(true);

            await changeUserPassword({
                email: authUser?.email,
                currentPassword: form.currentPassword,
                newPassword: form.newPassword,
            });

            setServerMessage("Password updated successfully.");
            setForm({
                currentPassword: "",
                newPassword: "",
                confirmNewPassword: "",
            });
        } catch (error) {
            setServerError(
                error?.response?.data?.message ||
                error?.response?.data ||
                "Could not update password."
            );
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="card p-6 sm:p-8">
            <h2 className="text-lg font-semibold text-slate-900">Security</h2>
            <p className="mt-2 text-sm text-slate-600">
                Update your password for this local account.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-5">
                <div>
                    <label className="label">Current password</label>
                    <input
                        name="currentPassword"
                        type="password"
                        className="input"
                        value={form.currentPassword}
                        onChange={handleChange}
                        placeholder="Enter current password"
                    />
                    {errors.currentPassword && (
                        <p className="mt-2 text-sm text-rose-600">{errors.currentPassword}</p>
                    )}
                </div>

                <div>
                    <label className="label">New password</label>
                    <input
                        name="newPassword"
                        type="password"
                        className="input"
                        value={form.newPassword}
                        onChange={handleChange}
                        placeholder="Enter new password"
                    />
                    {errors.newPassword && (
                        <p className="mt-2 text-sm text-rose-600">{errors.newPassword}</p>
                    )}
                </div>

                <div>
                    <label className="label">Confirm new password</label>
                    <input
                        name="confirmNewPassword"
                        type="password"
                        className="input"
                        value={form.confirmNewPassword}
                        onChange={handleChange}
                        placeholder="Confirm new password"
                    />
                    {errors.confirmNewPassword && (
                        <p className="mt-2 text-sm text-rose-600">{errors.confirmNewPassword}</p>
                    )}
                </div>

                {serverMessage && (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                        {serverMessage}
                    </div>
                )}

                {serverError && (
                    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                        {serverError}
                    </div>
                )}

                <button type="submit" className="btn-secondary" disabled={submitting}>
                    {submitting ? "Updating..." : "Change Password"}
                </button>
            </form>
        </div>
    );
}
