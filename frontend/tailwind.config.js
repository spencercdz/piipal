/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'tiktok-black': '#000000',
        'tiktok-white': '#FFFFFF',
        'tiktok-red': '#FE2C55',
        'tiktok-gray': '#8A8B91',
        'tiktok-dark-gray': '#121212',
      },
      fontFamily: {
        sans: ['var(--font-tiktok-sans)', 'sans-serif'],
        mono: ['var(--font-tiktok-mono)', 'monospace'],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};