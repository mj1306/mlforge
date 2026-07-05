import { LogOut, UserCircle } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { ROUTES } from "../../constants/routes";
import { useAuthStore } from "../../store/useAuthStore";

const LINKS = [
  { label: "Home", to: ROUTES.home },
  { label: "Live Demo", to: ROUTES.demo },
  { label: "Workspace", to: ROUTES.workspace },
  { label: "Annotation", to: ROUTES.annotation },
  { label: "My Models", to: ROUTES.models },
];

export function NavBar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate(ROUTES.home);
  };

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

        <div className="ml-3 pl-3 border-l border-white/20 flex items-center gap-2">
          {user ? (
            <>
              <span className="hidden sm:inline-flex items-center gap-1.5 text-white/90 text-sm">
                <UserCircle className="w-4 h-4" /> {user.username}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                title="Sign out"
                className="inline-flex items-center gap-1 px-3 py-2 rounded-md text-sm font-medium text-white/80 hover:bg-white/10 hover:text-white transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </>
          ) : (
            <NavLink
              to={ROUTES.login}
              className="px-3 py-2 rounded-md text-sm font-medium bg-white/15 text-white hover:bg-white/25 transition-colors"
            >
              Sign in
            </NavLink>
          )}
        </div>
      </div>
    </div>
  );
}
