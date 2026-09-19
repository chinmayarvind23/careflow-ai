import { BrowserRouter, Routes, Route } from "react-router-dom"
import LandingPage from "./pages/LandingPage"
import PortalPage from "./pages/PortalPage"
import ReferralDetailPage from "./pages/ReferralDetailPage"
import ProcessingPage from "./pages/ProcessingPage"
import ReviewPage from "./pages/ReviewPage"
import EligibilityPage from "./pages/EligibilityPage"
import PlacementPage from "./pages/PlacementPage"
import SchedulingPage from "./pages/SchedulingPage"
import CompletePage from "./pages/CompletePage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/portal" element={<PortalPage />} />
        <Route path="/referral/:id" element={<ReferralDetailPage />} />
        <Route path="/processing/:id" element={<ProcessingPage />} />
        <Route path="/review/:id" element={<ReviewPage />} />
        <Route path="/eligibility/:id" element={<EligibilityPage />} />
        <Route path="/placement/:id" element={<PlacementPage />} />
        <Route path="/schedule/:id" element={<SchedulingPage />} />
        <Route path="/complete/:id" element={<CompletePage />} />
      </Routes>
    </BrowserRouter>
  )
}