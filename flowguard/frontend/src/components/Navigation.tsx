import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Overview", icon: "◫" },
  { to: "/expenses", label: "Expenses", icon: "↘" },
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
      <div className="nav-section-label">Coming next</div>
      <span className="nav-link disabled"><span>↗</span>Income</span>
      <span className="nav-link disabled"><span>⌁</span>Commitments</span>
      <span className="nav-link disabled"><span>⌁</span>Forecast</span>
    </nav>
  );
}
