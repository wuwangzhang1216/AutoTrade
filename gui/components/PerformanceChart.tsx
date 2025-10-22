
import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';
import { MODELS_DATA } from '../constants';
import type { ModelData } from '../types';

interface PerformanceChartProps {
    valueType: '$' | '%';
    timeRange: 'ALL' | '72H';
}

const CustomDot: React.FC<any> = (props) => {
    const { cx, cy, dataKey, index, payload, onClick } = props;

    // Validate that we have all required data
    if (!payload || index === undefined || cx === undefined || cy === undefined || isNaN(cx) || isNaN(cy)) {
        return null;
    }

    // Validate that cx and cy are reasonable values (not 0, not at edges)
    if (cx <= 0 || cy <= 0) {
        return null;
    }

    // Check if the actual data value exists for this model
    const value = payload[dataKey];
    if (value === undefined || value === null || isNaN(value)) {
        return null;
    }

    const model = MODELS_DATA.find(m => m.id === dataKey);
    if (!model) {
        return null;
    }

    const { icon: Icon, color } = model;

    // For BTC, use smaller size as it's a baseline
    const isBtc = model.id === 'btcHold';
    const outerRadius = isBtc ? 8 : 11;
    const mainRadius = isBtc ? 6.5 : 9;
    const iconSize = isBtc ? 10 : 14;
    const halfIconSize = iconSize / 2;

    return (
        <g
            onClick={(e) => {
                e.stopPropagation();
                if (onClick) onClick();
            }}
            style={{ cursor: 'pointer' }}
        >
            {/* Outer glow effect */}
            <circle cx={cx} cy={cy} r={outerRadius} fill={color} opacity={0.3} />
            {/* Main circle with model color */}
            <circle cx={cx} cy={cy} r={mainRadius} fill={color} stroke="rgba(0,0,0,0.2)" strokeWidth={1} />
            {/* Icon - white color for visibility */}
            <foreignObject
                x={cx - halfIconSize}
                y={cy - halfIconSize}
                width={iconSize}
                height={iconSize}
                style={{ overflow: 'visible', pointerEvents: 'none' }}
            >
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: `${iconSize}px`,
                    height: `${iconSize}px`
                }}>
                    <Icon style={{ color: '#FFFFFF' }} size={iconSize} />
                </div>
            </foreignObject>
        </g>
    )
}

const CustomTooltip: React.FC<any> = ({ active, payload, valueType, selectedLine }) => {
    if (!active || !payload || !payload.length || !selectedLine) {
        return null;
    }

    // Only show tooltip for the selected line
    const selectedEntry = payload.find((entry: any) => entry.dataKey === selectedLine);
    if (!selectedEntry) return null;

    const model = MODELS_DATA.find(m => m.id === selectedLine);
    if (!model) return null;

    const value = selectedEntry.value;
    const formattedValue = valueType === '%'
        ? `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
        : `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    return (
        <div
            className="bg-[#1a1a1a] border-2 rounded-lg px-3 py-2 shadow-xl"
            style={{ borderColor: model.color }}
        >
            <div className="flex items-center gap-2">
                <span className="text-xs font-bold" style={{ color: model.color }}>
                    {formattedValue}
                </span>
            </div>
        </div>
    );
}


export const PerformanceChart: React.FC<PerformanceChartProps> = ({ valueType, timeRange }) => {
    // Responsive window width detection - must be defined first
    const [windowWidth, setWindowWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);

    // Track which line is selected (clicked)
    const [selectedLine, setSelectedLine] = useState<string | null>(null);

    // Track which line is being hovered for visual feedback
    const [hoveredLine, setHoveredLine] = useState<string | null>(null);

    useEffect(() => {
        const handleResize = () => setWindowWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const isMobile = windowWidth < 768;

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

    // On mobile, sample the data to reduce points and improve performance
    const optimizedData = useMemo(() => {
        if (!isMobile || filteredData.length <= 50) {
            return filteredData;
        }
        // Sample every nth point to keep around 40-50 points on mobile
        const sampleRate = Math.ceil(filteredData.length / 45);
        const sampled = filteredData.filter((_, index) => index % sampleRate === 0 || index === filteredData.length - 1);
        return sampled;
    }, [filteredData, isMobile]);

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
            return optimizedData;
        }

        // Convert to percentage
        if (optimizedData.length === 0) return [];

        return optimizedData.map(point => {
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
    }, [optimizedData, valueType, initialValues]);

    // Calculate smart interval for x-axis based on data length
    const xAxisInterval = useMemo(() => {
        const dataLength = chartData.length;

        if (isMobile) {
            // Fewer labels on mobile for better readability
            if (dataLength <= 20) return Math.floor(dataLength / 8); // ~8 labels max
            if (dataLength <= 40) return Math.floor(dataLength / 6); // ~6 labels
            return Math.floor(dataLength / 5); // ~5 labels for more data
        }

        // Desktop interval calculation
        if (dataLength <= 20) return 0; // Show all labels
        if (dataLength <= 50) return Math.floor(dataLength / 15); // ~15 labels
        if (dataLength <= 100) return Math.floor(dataLength / 12); // ~12 labels
        if (dataLength <= 200) return Math.floor(dataLength / 10); // ~10 labels
        return Math.floor(dataLength / 8); // ~8 labels for very large datasets
    }, [chartData.length, isMobile]);

    // Chart responsive settings - minimal margins for maximum chart space
    const chartMargins = isMobile
        ? { top: 10, right: 5, left: -5, bottom: 2 }
        : { top: 15, right: 10, left: 5, bottom: 5 };
    const fontSize = isMobile ? 8 : 10;
    const xAxisAngle = isMobile ? -45 : -15;
    const yAxisWidth = isMobile ? 42 : 55;
    const xAxisHeight = isMobile ? 35 : 45;

    return (
        <div
            style={{ width: '100%', height: '100%', touchAction: 'pan-y' }}
            onClick={(e) => {
                // If clicking on the container (not on a line), deselect
                if (e.target === e.currentTarget) {
                    setSelectedLine(null);
                }
            }}
        >
        <ResponsiveContainer width="100%" height="100%">
            <LineChart
                data={chartData}
                margin={chartMargins}
                style={{ touchAction: 'pan-y' }}
                onClick={(e) => {
                    // If clicking on chart background (not on a line), deselect
                    if (!e || !e.activeLabel) {
                        setSelectedLine(null);
                    }
                }}
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
                    domain={valueType === '%' ? ['auto', 'auto'] : ['dataMin - 100', 'dataMax + 100']}
                    tickCount={isMobile ? 5 : 6}
                    width={yAxisWidth}
                />
                <Tooltip
                    content={<CustomTooltip valueType={valueType} selectedLine={selectedLine} />}
                    cursor={selectedLine ? {
                        stroke: MODELS_DATA.find(m => m.id === selectedLine)?.color || 'rgba(255, 255, 255, 0.3)',
                        strokeWidth: 2,
                        strokeDasharray: '5 5'
                    } : false}
                    animationDuration={0}
                />

                {MODELS_DATA.map((model: ModelData) => {
                    // Calculate opacity based on selected state
                    let lineOpacity = model.id === 'btcHold' ? 0.7 : 1;
                    if (selectedLine) {
                        // If a line is selected, dim all other lines
                        lineOpacity = selectedLine === model.id
                            ? 1  // Selected line at full opacity
                            : 0.15;  // Other lines dimmed
                    } else if (hoveredLine && hoveredLine !== model.id) {
                        // If hovering over a different line, slightly dim this one
                        lineOpacity = model.id === 'btcHold' ? 0.4 : 0.3;
                    }

                    // Calculate stroke width based on selected and hover state
                    const baseStrokeWidth = model.id === 'btcHold' ? 2 : 2.5;
                    let strokeWidth = baseStrokeWidth;

                    // If selected, make thicker
                    if (selectedLine === model.id) {
                        strokeWidth = baseStrokeWidth + 1.5;
                    }
                    // If hovered, make slightly thicker for immediate feedback
                    else if (hoveredLine === model.id) {
                        strokeWidth = baseStrokeWidth + 1;
                    }

                    // Find the last valid data point index for this specific model
                    let lastValidIndex = -1;
                    for (let i = chartData.length - 1; i >= 0; i--) {
                        const value = chartData[i]?.[model.id];
                        if (value !== undefined && value !== null && !isNaN(value)) {
                            lastValidIndex = i;
                            break;
                        }
                    }

                    const handleLineClick = () => {
                        // Toggle selection: if already selected, deselect; otherwise select
                        setSelectedLine(prev => prev === model.id ? null : model.id);
                    };

                    return (
                        <React.Fragment key={model.id}>
                            {/* Invisible wider line for easier clicking/hovering */}
                            <Line
                                type="monotone"
                                dataKey={model.id}
                                stroke="transparent"
                                strokeWidth={15}
                                dot={false}
                                activeDot={false}
                                isAnimationActive={false}
                                onMouseEnter={() => setHoveredLine(model.id)}
                                onMouseLeave={() => setHoveredLine(null)}
                                onClick={handleLineClick}
                                style={{ cursor: 'pointer' }}
                            />
                            {/* Visible line with styling */}
                            <Line
                                type="monotone"
                                dataKey={model.id}
                                stroke={model.color}
                                strokeWidth={strokeWidth}
                                dot={(props: any) => {
                                    // Only show dot at the last valid point for this model
                                    if (props.index === lastValidIndex) {
                                        return <CustomDot {...props} onClick={handleLineClick} />;
                                    }
                                    return null;
                                }}
                                activeDot={selectedLine === model.id ? {
                                    r: isMobile ? 6 : 7,
                                    strokeWidth: 3,
                                    stroke: model.color,
                                    fill: 'rgba(13, 13, 13, 0.95)',
                                    style: { cursor: 'pointer' },
                                    onClick: (e: any) => {
                                        e.stopPropagation();
                                        handleLineClick();
                                    }
                                } : false}
                                strokeDasharray={model.id === 'btcHold' ? '5 5' : '0'}
                                animationDuration={isMobile ? 0 : 800}
                                animationEasing="ease-in-out"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                opacity={lineOpacity}
                                isAnimationActive={false}
                                style={{
                                    cursor: 'pointer',
                                    pointerEvents: 'none' // Let the invisible line handle clicks
                                }}
                            />
                        </React.Fragment>
                    );
                })}
            </LineChart>
        </ResponsiveContainer>
        </div>
    );
};
