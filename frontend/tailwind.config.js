/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 纯黑高级配色方案
        primary: {
          50: '#fefce8',   // 极浅金
          100: '#fef9c3',  // 浅金
          200: '#fef08a',  // 金色
          300: '#fde047',  // 亮金
          400: '#facc15',  // 金黄
          500: '#eab308',  // 深金
          600: '#ca8a04',  // 浓金
          700: '#a16207',  // 暗金
          800: '#854d0e',  // 深暗金
          900: '#713f12',  // 最深金
        },
        // 银色系
        silver: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
        },
        // 高级黑
        elite: {
          950: '#0a0a0a',  // 微亮黑
          975: '#050505',  // 深黑
          990: '#020202',  // 纯黑边缘
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-premium': 'linear-gradient(135deg, #000000 0%, #0a0a0a 50%, #000000 100%)',
        'gradient-gold': 'linear-gradient(135deg, #ca8a04 0%, #eab308 100%)',
        'gradient-card': 'linear-gradient(135deg, rgba(10,10,10,0.8) 0%, rgba(0,0,0,0.95) 100%)',
        'grid-white': 'linear-gradient(to right, rgba(255, 255, 255, 0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
      },
      boxShadow: {
        'premium': '0 0 20px rgba(234, 179, 8, 0.1), 0 0 40px rgba(0, 0, 0, 0.5)',
        'gold': '0 0 30px rgba(234, 179, 8, 0.3)',
        'elite': '0 4px 20px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.03)',
        input: "0px 2px 3px -1px rgba(0,0,0,0.1), 0px 1px 0px 0px rgba(25,28,33,0.02), 0px 0px 0px 1px rgba(25,28,33,0.08)",
      },
      borderColor: {
        'gold': '#ca8a04',
        'gold-light': '#eab308',
      },
      animation: {
        aurora: "aurora 60s linear infinite",
        shimmer: "shimmer 2s linear infinite",
        "shimmer-slide": "shimmer-slide var(--speed) ease-in-out infinite alternate",
        "spin-around": "spin-around calc(var(--speed) * 2) infinite linear",
      },
      keyframes: {
        aurora: {
          from: {
            backgroundPosition: "50% 50%, 50% 50%",
          },
          to: {
            backgroundPosition: "350% 50%, 350% 50%",
          },
        },
        shimmer: {
          from: {
            backgroundPosition: "0 0",
          },
          to: {
            backgroundPosition: "-200% 0",
          },
        },
        "shimmer-slide": {
          to: {
            transform: "translate(calc(100cqw - 100%), 0)",
          },
        },
        "spin-around": {
          "0%": {
            transform: "translateZ(0) rotate(0)",
          },
          "15%, 35%": {
            transform: "translateZ(0) rotate(90deg)",
          },
          "65%, 85%": {
            transform: "translateZ(0) rotate(270deg)",
          },
          "100%": {
            transform: "translateZ(0) rotate(360deg)",
          },
        },
      },
    },
  },
  plugins: [
    function ({ addUtilities }) {
      addUtilities({
        '.bg-grid-white': {
          backgroundImage: 'linear-gradient(to right, rgba(255, 255, 255, 0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
        },
      });
    },
  ],
}
