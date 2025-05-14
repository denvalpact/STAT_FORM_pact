import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import MatchDetail from './pages/MatchDetail';

const App = () => {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/matches/:matchId" element={<MatchDetail />} />
            </Routes>
        </Router>
    );
};

export default App;