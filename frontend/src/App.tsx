import { HashRouter, Route, Routes } from "react-router-dom";
import { NavBar } from "./components/NavBar/NavBar";
import { ROUTES } from "./constants/routes";
import { Annotation } from "./pages/Annotation/Annotation";
import { Home } from "./pages/Home/Home";
import { WorkspaceMain } from "./pages/Workspace/WorkspaceMain";

function App() {
  return (
    <HashRouter>
      <NavBar />
      <main className="flex-1 flex flex-col pt-16">
        <Routes>
          <Route path={ROUTES.home} element={<Home />} />
          <Route path={ROUTES.workspace} element={<WorkspaceMain />} />
          <Route path={ROUTES.annotation} element={<Annotation />} />
        </Routes>
      </main>
    </HashRouter>
  );
}

export default App;
