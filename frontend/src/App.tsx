import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import Artist from "./pages/Artist";
import Onboarding from "./pages/Onboarding";
import Similar from "./pages/Similar";
import { Login, Register } from "./pages/Auth";
import Collections from "./pages/Collections";
import Explore from "./pages/Explore";
import ForYou from "./pages/ForYou";
import NotFound from "./pages/NotFound";
import Privacy from "./pages/Privacy";
import Profile from "./pages/Profile";
import Search from "./pages/Search";
import TagPage from "./pages/TagPage";

export default function App() {
  return (
    <Routes>
      {/* la scelta iniziale è a tutto schermo: niente barra di navigazione sopra i suoi pulsanti */}
      <Route path="benvenuto" element={<Onboarding />} />
      <Route element={<AppShell />}>
        <Route index element={<ForYou />} />
        <Route path="esplora" element={<Explore />} />
        <Route path="esplora/:kind/:slug" element={<TagPage />} />
        <Route path="cerca" element={<Search />} />
        <Route path="artista/:id" element={<Artist />} />
        <Route path="simili/:id" element={<Similar />} />
        <Route path="raccolte" element={<Collections />} />
        <Route path="profilo" element={<Profile />} />
        <Route path="accedi" element={<Login />} />
        <Route path="registrati" element={<Register />} />
        <Route path="privacy" element={<Privacy />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
