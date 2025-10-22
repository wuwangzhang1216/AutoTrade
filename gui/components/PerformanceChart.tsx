
import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Customized, DotProps } from 'recharts';
import { MODELS_DATA } from '../constants';
import type { ModelData } from '../types';

interface PerformanceChartProps {
    valueType: '$' | '%';
    timeRange: 'ALL' | '72H';
}

const CustomizedLabel: React.FC<any> = (props) => {
    const { x, y, index, data, dataKey, valueType, isMobile } = props;
    const model = MODELS_DATA.find(m => m.id === dataKey);

    // Hide labels on mobile to prevent overflow
    if (!model || index !== data.length - 1 || isMobile) {
        return null;
    }

    const { icon: Icon, color } = model;
    const currentValue = data[index][dataKey];

    // When valueType is '%', the data is already converted to percentage
    const displayValue = valueType === '%'
        ? `${currentValue.toFixed(2)}%`
        : `$${currentValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    return (
        <g transform={`translate(${x},${y})`}>
            <foreignObject x={15} y={-18} width="150" height="36">
                <div
                    className="flex items-center space-x-2 px-3 py-1.5 rounded-md shadow-2xl border border-opacity-20"
                    style={{
                        backgroundColor: `${color}f0`, // Add slight transparency
                        color: model.id === 'grok' ? '#0D0D0D' : '#FFFFFF',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        fontFamily: "'Inter', sans-serif",
                        fontSize: '10px',
                        fontWeight: 600,
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)'
                    }}
                >
                    <Icon style={{ color: model.id === 'grok' ? '#0D0D0D' : '#FFFFFF' }} size={16} />
                    <span className="whitespace-nowrap">{displayValue}</span>
                </div>
            </foreignObject>
        </g>
    );
};

const CustomizedEndPoint: React.FC<any> = (props) => {
    const { cx, cy, dataKey, index, data } = props;
    const model = MODELS_DATA.find(m => m.id === dataKey);

    if (!model || index !== data.length - 1) {
        return null;
    }

    const { icon: Icon, color } = model;

    // For BTC, use smaller size as it's a baseline
    const isBtc = model.id === 'btcHold';
    const outerRadius = isBtc ? 10 : 12;
    const mainRadius = isBtc ? 7.5 : 9;
    const innerRadius = isBtc ? 6 : 7;
    const iconSize = isBtc ? 12 : 14;

    return (
        <g>
            {/* Outer glow effect */}
            <circle cx={cx} cy={cy} r={outerRadius} fill={color} opacity={isBtc ? 0.15 : 0.2} />
            {/* Main circle with model color */}
            <circle cx={cx} cy={cy} r={mainRadius} fill={color} stroke="none" opacity={isBtc ? 0.7 : 1} />
            {/* Icon container with white or dark background */}
            <circle cx={cx} cy={cy} r={innerRadius} fill={model.id === 'grok' ? '#0D0D0D' : '#FFFFFF'} opacity={0.95} />
            <foreignObject x={cx - 9} y={cy - 9} width="18" height="18">
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '18px',
                    height: '18px'
                }}>
                    <Icon style={{ color: color }} size={iconSize} />
                </div>
            </foreignObject>
        </g>
    )
}

const CustomTooltip: React.FC<any> = ({ active, payload, label, valueType }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-arena-black border border-arena-gray-700 p-4 rounded-lg shadow-2xl backdrop-blur-sm" style={{ backgroundColor: 'rgba(13, 13, 13, 0.95)' }}>
                <p className="label text-sm text-arena-gray-400 mb-2 font-semibold">{`${label}`}</p>
                {payload.map((pld: any) => {
                    const model = MODELS_DATA.find(m => m.id === pld.dataKey);
                    if (!model) return null;

                    const currentValue = pld.value;

                    // When valueType is '%', the data is already converted to percentage
                    const displayValue = valueType === '%'
                        ? `${currentValue.toFixed(2)}%`
                        : `$${currentValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

                    const Icon = model.icon;

                    return (
                        <div key={pld.dataKey} className="flex items-center justify-between space-x-6 py-1">
                            <div className="flex items-center space-x-2">
                                <Icon style={{ color: pld.color }} size={16} />
                                <span className="text-sm" style={{ color: pld.color }}>{model.name}</span>
                            </div>
                            <span className="font-bold text-sm" style={{ color: pld.color }}>
                                {displayValue}
                            </span>
                        </div>
                    );
                })}
            </div>
        );
    }

    return null;
};


export const PerformanceChart: React.FC<PerformanceChartProps> = ({ valueType, timeRange }) => {
    const [rawChartData, setRawChartData] = useState<any[]>([{
        date: "Now",
        gpt5: 10000,
        claude: 10000,
        gemini: 10000,
        grok: 10000,
        deepseek: 10000,
        qwen: 10000,
        btcHold: 10000
    }]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('http://localhost:8003/api/performance/chart');
                const data = await response.json();
                if (data && data.length > 0) {
                    setRawChartData(data);
                }
            } catch (error) {
                console.error('Failed to fetch performance chart data:', error);
            }
        };

        // Initial fetch
        fetchData();

        // Refresh every 30 seconds
        const interval = setInterval(fetchData, 30000);

        return () => clearInterval(interval);
    }, []);

    // Filter data by time range
    const filteredData = useMemo(() => {
        if (timeRange === 'ALL') {
            return rawChartData;
        }
        // 72H - show last 72 data points (assuming data is at regular intervals)
        const hours72InPoints = Math.min(72, rawChartData.length);
        return rawChartData.slice(-hours72InPoints);
    }, [rawChartData, timeRange]);

    // Get the initial values for percentage calculation
    const initialValues = useMemo(() => {
        if (filteredData.length === 0) return {};
        const firstPoint = filteredData[0];
        const values: Record<string, number> = {};
        MODELS_DATA.forEach(model => {
            if (firstPoint[model.id] !== undefined) {
                values[model.id] = firstPoint[model.id];
            }
        });
        return values;
    }, [filteredData]);

    // Transform data based on value type
    const chartData = useMemo(() => {
        if (valueType === '$') {
            return filteredData;
        }

        // Convert to percentage
        if (filteredData.length === 0) return [];

        return filteredData.map(point => {
            const newPoint: any = { date: point.date };
            MODELS_DATA.forEach(model => {
                const currentValue = point[model.id];
                const initialValue = initialValues[model.id];
                if (currentValue !== undefined && initialValue !== undefined && initialValue !== 0) {
                    newPoint[model.id] = ((currentValue - initialValue) / initialValue) * 100;
                } else {
                    newPoint[model.id] = 0;
                }
            });
            return newPoint;
        });
    }, [filteredData, valueType, initialValues]);

    // Calculate smart interval for x-axis based on data length
    const xAxisInterval = useMemo(() => {
        const dataLength = chartData.length;
        if (dataLength <= 20) return 0; // Show all labels
        if (dataLength <= 50) return Math.floor(dataLength / 15); // ~15 labels
        if (dataLength <= 100) return Math.floor(dataLength / 12); // ~12 labels
        if (dataLength <= 200) return Math.floor(dataLength / 10); // ~10 labels
        return Math.floor(dataLength / 8); // ~8 labels for very large datasets
    }, [chartData.length]);

    // Responsive margins based on screen width
    const [windowWidth, setWindowWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);

    useEffect(() => {
        const handleResize = () => setWindowWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const isMobile = windowWidth < 768;
    const chartMargins = isMobile
        ? { top: 20, right: 10, left: -5, bottom: 5 }
        : { top: 30, right: 150, left: 15, bottom: 15 };
    const fontSize = isMobile ? 8 : 10;
    const xAxisAngle = isMobile ? -45 : -15;
    const yAxisWidth = isMobile ? 45 : 65;
    const xAxisHeight = isMobile ? 40 : 55;

    return (
        <ResponsiveContainer width="100%" height="100%">
            <LineChart
                data={chartData}
                margin={chartMargins}
            >
                <defs>
                    {MODELS_DATA.map((model: ModelData) => (
                        <linearGradient key={`gradient-${model.id}`} id={`gradient-${model.id}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={model.color} stopOpacity={model.id === 'btcHold' ? 0.1 : 0.2}/>
                            <stop offset="95%" stopColor={model.color} stopOpacity={0}/>
                        </linearGradient>
                    ))}
                    {/* Shadow filters for depth */}
                    <filter id="line-shadow" x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
                        <feOffset dx="0" dy="1" result="offsetblur"/>
                        <feComponentTransfer>
                            <feFuncA type="linear" slope="0.3"/>
                        </feComponentTransfer>
                        <feMerge>
                            <feMergeNode/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>
                <CartesianGrid
                    strokeDasharray="1 3"
                    stroke="rgba(255, 255, 255, 0.08)"
                    vertical={false}
                    strokeOpacity={1}
                    strokeWidth={0.5}
                />
                <XAxis
                    dataKey="date"
                    stroke="rgba(255, 255, 255, 0.15)"
                    tick={{ fontSize: fontSize, fill: 'rgba(255, 255, 255, 0.6)', fontWeight: 600, fontFamily: "'Courier New', monospace" }}
                    axisLine={{ stroke: 'rgba(255, 255, 255, 0.15)', strokeWidth: 1 }}
                    tickLine={{ stroke: 'rgba(255, 255, 255, 0.1)', strokeWidth: 1 }}
                    interval={xAxisInterval}
                    angle={xAxisAngle}
                    textAnchor="end"
                    height={xAxisHeight}
                />
                <YAxis
                    stroke="rgba(255, 255, 255, 0.15)"
                    tick={{ fontSize: fontSize, fill: 'rgba(255, 255, 255, 0.6)', fontWeight: 600, fontFamily: "'Courier New', monospace" }}
                    axisLine={{ stroke: 'rgba(255, 255, 255, 0.15)', strokeWidth: 1 }}
                    tickLine={{ stroke: 'rgba(255, 255, 255, 0.1)', strokeWidth: 1 }}
                    tickFormatter={(value: number) =>
                        valueType === '%'
                            ? `${value.toFixed(0)}%`
                            : value >= 1000
                                ? isMobile ? `$${(value / 1000).toFixed(1)}k` : `$${(value / 1000).toFixed(1)}k`
                                : `$${value.toFixed(0)}`
                    }
                    domain={valueType === '%' ? ['auto', 'auto'] : ['dataMin - 500', 'dataMax + 500']}
                    tickCount={isMobile ? 5 : 6}
                    width={yAxisWidth}
                />
                <Tooltip
                    content={<CustomTooltip valueType={valueType} />}
                    cursor={{ stroke: '#444444', strokeWidth: 1, strokeDasharray: '5 5' }}
                />

                {MODELS_DATA.map((model: ModelData) => (
                    <Line
                        key={model.id}
                        type="monotone"
                        dataKey={model.id}
                        stroke={model.color}
                        strokeWidth={isMobile ? (model.id === 'btcHold' ? 1.5 : 2) : (model.id === 'btcHold' ? 2 : 2.5)}
                        dot={false}
                        activeDot={{ r: isMobile ? 4 : 6, strokeWidth: 2, stroke: model.color, fill: 'rgba(13, 13, 13, 0.95)' }}
                        strokeDasharray={model.id === 'btcHold' ? '5 5' : '0'}
                        animationDuration={1000}
                        animationEasing="ease-in-out"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        opacity={model.id === 'btcHold' ? 0.7 : 1}
                    >
                         {/* This renders the icon and label at the end of the line */}
                        <Customized
                            component={(props: any) => <CustomizedEndPoint {...props} data={chartData} />}
                        />
                         <Customized
                            component={(props: any) => <CustomizedLabel {...props} data={chartData} valueType={valueType} isMobile={isMobile} />}
                        />
                    </Line>
                ))}
            </LineChart>
        </ResponsiveContainer>
    );
};
