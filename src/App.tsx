// Main application component - routing and auth provider setup

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import LandingPage from './pages/LandingPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public route - landing page */}
          <Route path="/" element={<LandingPage />} />
          
          {/* Temporary catch-all - will add more routes next */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;