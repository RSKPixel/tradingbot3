import { use, useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Basetemplate from './templates/Basetemplate';
import IntradayPivotScanner from './pages/scanners/IntradayPivotScanner';

function App() {

    return (
        <Router>
            <Basetemplate>
                <Routes>
                    <Route path="/" element={<div>Welcome to TradingBot</div>} />
                    <Route path="/intraday-pivot-scanner" element={<IntradayPivotScanner />} />
                </Routes>
            </Basetemplate>
        </Router>
    );
}

export default App
