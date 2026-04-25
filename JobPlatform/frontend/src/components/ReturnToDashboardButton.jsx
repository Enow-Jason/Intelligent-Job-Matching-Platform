import { Link } from "react-router-dom";

/*
  Reusable button for pages outside the dashboard.
  Display this above the page title so navigation feels easier.
*/
export default function ReturnToDashboardButton() {
    return (
        <div className="mb-5">
            <Link to="/dashboard" className="btn-secondary">
                Return to Dashboard
            </Link>
        </div>
    );
}
