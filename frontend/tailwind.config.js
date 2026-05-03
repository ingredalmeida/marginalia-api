export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        serif: ['Fraunces', 'Georgia', 'serif'],
      },
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        teal: '#2d6a6a',
        coral: '#e07a5f',
        pink: '#e8b4bc',
        mustard: '#c9a227',
        ink: '#2c2420',
        terracotta: '#c67b5c',
        cream: '#faf6f0',
        sand: '#e8e0d5',
      },
      backgroundImage: {
        'gradient-warm':
          'linear-gradient(165deg, hsl(28 40% 96%) 0%, hsl(18 45% 92%) 45%, hsl(15 35% 88%) 100%)',
        'gradient-hero': 'linear-gradient(135deg, #2c2420 0%, #2d6a6a 55%, #e07a5f 100%)',
      },
      boxShadow: {
        soft: '0 4px 24px -4px rgba(44, 36, 32, 0.12)',
        book: '0 12px 40px -12px rgba(44, 36, 32, 0.25)',
      },
      keyframes: {
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s ease-out forwards',
        float: 'float 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
