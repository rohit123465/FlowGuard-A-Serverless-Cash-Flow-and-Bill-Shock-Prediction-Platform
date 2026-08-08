import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export function LoginForm() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await signIn(email.trim(), password);
      const destination =
        (location.state as { from?: { pathname?: string } } | null)?.from
          ?.pathname ?? "/";
      navigate(destination, { replace: true });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sign-in failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="login-card" onSubmit={handleSubmit}>
      <div className="brand-mark" aria-hidden="true">FG</div>
      <p className="eyebrow">Cash-flow clarity</p>
      <h1>Welcome to FlowGuard</h1>
      <p className="muted">Sign in securely with your FlowGuard account.</p>

      <label>
        Email address
        <input
          type="email"
          autoComplete="username"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
      </label>
      <label>
        Password
        <input
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </label>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      <button className="button button-primary" type="submit" disabled={submitting}>
        {submitting ? "Signing in…" : "Sign in"}
      </button>
      <p className="login-note">Protected by Amazon Cognito and JWT authentication.</p>
    </form>
  );
}
