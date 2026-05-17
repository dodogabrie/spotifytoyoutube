import colors from 'tailwindcss/colors'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,js}'],
  theme: {
    extend: {
      colors: {
        // Semantic roles — these are the names Claude Design (or any restyling
        // pass) should target. The default mapping below can be tuned without
        // touching the views.
        page: colors.slate[50],
        surface: colors.white,
        'surface-muted': colors.slate[100],
        border: colors.slate[200],
        divider: colors.slate[200],

        'fg-primary': colors.slate[900],
        'fg-secondary': colors.slate[500],
        'fg-muted': colors.slate[400],

        // Provider brand families — keep two parallel scales so the UI can
        // mirror Spotify/YT Music symmetrically.
        spotify: colors.emerald,
        ytmusic: colors.rose,

        // Status semantics
        success: colors.emerald,
        warning: colors.amber,
        danger: colors.red,
        info: colors.sky,
        accent: colors.slate, // primary CTA (e.g. "Continue") stays neutral
      },
      borderRadius: {
        card: '0.875rem',  // ~rounded-xl
        control: '0.5rem',
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 1px rgba(15, 23, 42, 0.04)',
        'card-hover': '0 10px 30px -10px rgba(15, 23, 42, 0.18)',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      maxWidth: {
        shell: '64rem', // page container
      },
    },
  },
  plugins: [],
}
