import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Overview", icon: "◫" },
  { to: "/expenses", label: "Expenses", icon: "↘" },
  { to: "/income", label: "Income", icon: "↗" },
  { to: "/commitments", label: "Commitments", icon: "⌁" },
  { to: "/forecast", label: "Forecast", icon: "⌁" },
];

export function Navigation() {
  return (
    <nav className="navigation" aria-label="Primary navigation">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.to === "/"}
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          <span aria-hidden="true">{link.icon}</span>
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
