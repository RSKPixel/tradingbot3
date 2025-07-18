import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom';
import moment from 'moment';

const IntradayPivotScanner = () => {
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [calls, setCalls] = useState("Buy");
    const [selectedSignals, setSelectedSignals] = useState([]);
    const [symbols, setSymbols] = useState([]);
    const [selectedSymbolData, setSelectedSymbolData] = useState(null);
    const api = 'http://127.0.0.1:8000'

    useEffect(() => {
        fetch(`${api}/intraday-pivot-signals`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                setSignals(data.signals);
                setLoading(false);
            })
    }, []);

    useEffect(() => {
        if (calls === "Buy") {
            setSelectedSignals(signals.filter(signal => signal.Signal === "Buy"));
            setSymbols([...new Set(signals.filter(signal => signal.Signal === "Buy").map(signal => signal.symbol))]);
        } else if (calls === "Sell") {
            setSelectedSignals(signals.filter(signal => signal.Signal === "Sell"));
            setSymbols([...new Set(signals.filter(signal => signal.Signal === "Sell").map(signal => signal.symbol))]);
        }
    }, [calls, signals]);

    if (loading) {
        // loading spinner with message with background blured
        return (
            <div className="fixed inset-0 bg-opacity-50 backdrop-blur-sm flex items-center justify-center gap-10">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
                <p className="text-gray-700 mt-4">Loading...</p>
            </div>
        );
    }

    return (
        <div className='flex flex-row h-full w-full'>
            <div className='flex flex-col w-64 border-r border-sky-900 overflow-scroll bg-neutral-900 text-sm'>

                <div className='flex flex-row justify-between border-b border-sky-900'>
                    <div className={`cursor-pointer px-2 py-1 border-r border-sky-800 text-center w-full ${calls === "Buy" ? 'bg-green-800' : ''}`} onClick={() => setCalls("Buy")}>
                        Buy Calls
                    </div>
                    <div className={`cursor-pointer px-2 py-1 border-sky-800 text-center w-full ${calls === "Sell" ? 'bg-green-800' : ''}`} onClick={() => setCalls("Sell")}>
                        Sell Calls</div>
                </div>
                {selectedSignals && selectedSignals.length > 0 && (
                    <div className='flex flex-col text-sm h-full  overflow-scroll '>
                        <ul>
                            {symbols.map((symbol, index) => (
                                <li key={index} className='flex flex-row px-2 py-1 hover:bg-neutral-800 cursor-pointer'
                                    onClick={() => {
                                        const symbolData = selectedSignals.filter(signal => signal.symbol === symbol);
                                        symbolData.sort((a, b) => new Date(a.date) - new Date(b.date));
                                        setSelectedSymbolData(symbolData);
                                    }}>
                                    <div>{symbol}</div>
                                    <div className='ms-auto'></div>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
                <div className='mt-auto'></div>
                <div className='border-t py-1 px-2 border-sky-900 bg-neutral-900'>Settings</div>
            </div>

            <div className='flex flex-col p-4 w-full'>
                <div className='text-lg font-bold mb-4'>Intraday Pivot Scanner</div>
                <div className='flex flex-col gap-2 text-sm'>
                    <div className='flex flex-row w-full items-center justify-center gap-2'>
                        {selectedSymbolData && selectedSymbolData.length > 0 ? (
                            selectedSymbolData.map((signal, index) => (
                                <div key={index} className='p-2 border border-sky-800 rounded-lg bg-neutral-800'>
                                    <div className='font-bold'>{signal.symbol}</div>
                                    <div>Signal: {signal.Signal}</div>
                                    <div>Date: {moment(signal.date).format('DD-MM-YYYY HH:mm')}</div>
                                </div>
                            ))
                        ) : (
                            <p>No signals available for the selected call type.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )

}

export default IntradayPivotScanner