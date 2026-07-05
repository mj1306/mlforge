import { useEffect } from "react";
import type { ReactNode } from "react";
import { HashRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { NavBar } from "./components/NavBar/NavBar";
import { ROUTES } from "./constants/routes";
import { Annotation } from "./pages/Annotation/Annotation";
import { AuthPage } from "./pages/Auth/AuthPage";
import { LiveDemo } from "./pages/Demo/LiveDemo";
import { Home } from "./pages/Home/Home";
import { MyModels } from "./pages/Models/MyModels";
import { WorkspaceMain } from "./pages/Workspace/WorkspaceMain";
import { useAuthStore } from "./store/useAuthStore";

/** Gate for pages that read/write per-user data. Home and the Live Demo stay
 * public -- the demo runs entirely in the browser and doubles as the
 * try-before-you-sign-up pitch. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { user, initialized } = useAuthStore();
  const location = useLocation();

  if (!initialized) {
    return <div className="flex flex-1 items-center justify-center text-gray-500">Loading…</div>;
  }
  if (!user) {
    return <Navigate to={ROUTES.login} state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
}

function App() {
  const init = useAuthStore((s) => s.init);

  useEffect(() => {
    void init();
  }, [init]);

  return (
    <HashRouter>
      <NavBar />
      <main className="flex-1 flex flex-col pt-16">
        <Routes>
          <Route path={ROUTES.home} element={<Home />} />
          <Route path={ROUTES.login} element={<AuthPage />} />
          <Route path={ROUTES.demo} element={<LiveDemo />} />
          <Route
            path={ROUTES.workspace}
            element={
              <RequireAuth>
                <WorkspaceMain />
              </RequireAuth>
            }
          />
          <Route
            path={ROUTES.annotation}
            element={
              <RequireAuth>
                <Annotation />
              </RequireAuth>
            }
          />
          <Route
            path={ROUTES.models}
            element={
              <RequireAuth>
                <MyModels />
              </RequireAuth>
            }
          />
        </Routes>
      </main>
    </HashRouter>
  );
}

export default App;
