import React from 'react'
import { Link } from 'react-router-dom'

const Basetemplate = ({ children }) => {
    return (
        <div className='flex flex-col w-full gap-0 h-screen'>
            <div className='flex flex-row h-10 border-b border-sky-800 bg-sky-950 items-center px-4 shadow-lg'>
                <div className='font-bold w-64'>TradingBot</div>
                <div className='ms-auto'></div>
                <Link to={"/intraday-pivot-scanner"} className='text-xs font-bold cursor-pointer border rounded-lg bg-green-900 p-2 border-green-800 hover:bg-green-800 shadow-lg'>Intraday Pivot Scanner</Link>
            </div>

            <div className='flex flex-col h-[calc(100vh-2.5rem)]'>{children}</div>

        </div>
    )
}

export default Basetemplate