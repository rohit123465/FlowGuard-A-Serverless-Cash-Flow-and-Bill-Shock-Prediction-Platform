import { Link } from "react-router-dom";

export function DashboardPage() {
  const today = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long" }).format(new Date());
  return (
    <>
      <div className="page-heading"><div><p className="eyebrow">{today}</p><h1>Your financial command centre</h1><p className="muted">FlowGuard is connected to your secured AWS backend.</p></div><Link className="button button-primary" to="/expenses">Open expenses</Link></div>
      <section className="hero-card"><div><span className="health-badge">● System healthy</span><h2>Your foundation is live.</h2><p>Authentication, protected API access and DynamoDB persistence are ready. Start by keeping your expense ledger current.</p><Link to="/expenses">Review monthly spending →</Link></div><div className="hero-orbit" aria-hidden="true"><span>£</span></div></section>
      <section className="next-grid"><article><span>01</span><h3>Expenses</h3><p>Add, edit and remove real records through the deployed API.</p><Link to="/expenses"><strong>Open expenses →</strong></Link></article><article><span>02</span><h3>Income & commitments</h3><p>Record expected inflows, recurring bills and contractual obligations.</p><Link to="/income"><strong>Manage cash flow →</strong></Link></article><article><span>03</span><h3>Forecast intelligence</h3><p>Visualise safe-to-spend and bill-shock risks from the deterministic engine.</p><Link to="/forecast"><strong>Run a forecast →</strong></Link></article></section>
    </>
  );
}
