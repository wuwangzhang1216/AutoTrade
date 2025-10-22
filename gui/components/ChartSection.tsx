
import React, { useState } from 'react';
import { PerformanceChart } from './PerformanceChart';

const ToggleButton: React.FC<{ options: string[]; active: string; onToggle: (option: string) => void; }> = ({ options, active, onToggle }) => {
  return (
    <div className="flex bg-gray-900 bg-opacity-40 backdrop-blur-sm border border-arena-gray-700 rounded-md p-0.5">
      {options.map(option => (
        <button
          key={option}
          onClick={() => onToggle(option)}
          className={`px-2 sm:px-3 py-1.5 sm:py-1 text-xs font-bold rounded min-h-[36px] sm:min-h-0 ${active === option ? 'bg-arena-gray-100 text-arena-black' : 'text-arena-gray-400 hover:bg-arena-gray-800'}`}
        >
          {option}
        </button>
      ))}
    </div>
  );
};

export const ChartSection: React.FC = () => {
  // FIX: Corrected the state type to `'$' | '%'` to match the possible values and fix the initialization error on line 22.
  const [valueType, setValueType] = useState<'$' | '%'>('$');
  const [timeRange, setTimeRange] = useState<'72H' | 'ALL'>('ALL');

  return (
    <div className="bg-gray-900 bg-opacity-40 backdrop-blur-sm border border-arena-gray-700 p-2 sm:p-3 md:p-4 rounded-lg">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 sm:mb-4 gap-2 sm:gap-3">
        <h3 className="text-[10px] sm:text-xs md:text-sm font-bold tracking-widest text-arena-gray-400">TOTAL ACCOUNT VALUE</h3>
        <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
          <ToggleButton options={['$', '%']} active={valueType} onToggle={setValueType as any} />
          <ToggleButton options={['ALL', '72H']} active={timeRange} onToggle={setTimeRange as any} />
        </div>
      </div>
      <div className="h-[200px] sm:h-[280px] md:h-[350px] lg:h-[400px] w-full relative">
        <PerformanceChart valueType={valueType} timeRange={timeRange} />
      </div>
    </div>
  );
};