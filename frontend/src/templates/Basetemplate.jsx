import React from 'react'
import { Link } from 'react-router-dom'

const Basetemplate = ({ children }) => {
    return (
        <div className='flex flex-col w-full gap-0 h-screen'>
            <div className='flex flex-row h-12 bg-sky-900 items-center px-4'>
                <div className='text-lg font-bold'>TradingBot</div>
                <div className='ms-auto'></div>
                <Link to={"/intraday-pivot-scanner"} className='text-xs font-bold cursor-pointer border rounded-lg bg-green-900 p-2 border-green-800 hover:bg-green-800 shadow-lg'>Intraday Pivot Scanner</Link>
            </div>

            <div className='flex flex-col'>{children}</div>

        </div>
    )
}

export default Basetemplate