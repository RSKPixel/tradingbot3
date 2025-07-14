import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom';

const IntradayPivotScanner = () => {
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);
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
                setSignals(data.signals);
                setLoading(false);
                console.log(data.signals);
            })
    }, []);

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
        <div className='flex flex-row h-[calc(100vh-3rem)] w-full'>
            <div className='flex flex-col w-64 border-r border-sky-900 overflow-scroll'>
                <div className='font-bold text-center px-4 bg-amber-900 py-1'>Watchlist</div>

                {signals.length > 0 && (
                    <div className='flex flex-col text-sm  overflow-scroll'>
                        <ul>
                            {signals.map((signal, index) => (
                                <li key={index} className='px-2 py-1 hover:bg-sky-950 cursor-pointer'>
                                    <div>{signal.symbol}</div>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

            </div>
        </div>
    )

}

export default IntradayPivotScanner