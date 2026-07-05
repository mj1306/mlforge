import { NavLink } from "react-router-dom";
import { ROUTES } from "../../constants/routes";

const LINKS = [
  { label: "Home", to: ROUTES.home },
  { label: "Workspace", to: ROUTES.workspace },
  { label: "Annotation", to: ROUTES.annotation },
];

export function NavBar() {
  return (
    <div className="flex fixed w-screen h-16 px-8 left-0 top-0 items-center justify-between z-50 bg-gradient-to-r from-brand via-brand-hover to-brand shadow-lg">
      <div className="flex items-center gap-2">
        <div className="w-9 h-9 bg-white/10 rounded-lg flex items-center justify-center border border-white/20">
          <span className="text-white font-bold text-lg">M</span>
        </div>
        <span className="text-white font-bold text-lg hidden md:block">MLForge</span>
      </div>

      <div className="flex items-center gap-1">
        {LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive ? "bg-white/20 text-white" : "text-white/80 hover:bg-white/10 hover:text-white"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>
    </div>
  );
}
