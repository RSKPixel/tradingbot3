import { use, useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Basetemplate from './templates/Basetemplate';
import IntradayPivotScanner from './pages/scanners/IntradayPivotScanner';
import Scanner from './pages/scanners/Scanner';

function App() {

    return (
        <Router>
            <Basetemplate>
                <Routes>
                    <Route path="/" element={<div>Welcome to TradingBot</div>} />
                    <Route path="/intraday-pivot-scanner" element={<IntradayPivotScanner />} />
                    <Route path="/intraday-emarsi-scanner" element={<Scanner statergy={"EMARSI"} />} />

                </Routes>
            </Basetemplate>
        </Router>
    );
}

export default App
