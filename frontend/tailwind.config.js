/** @type {import('tailwindcss').Config} */
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`;
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: v("bg"), surface: v("surface"), surface2: v("surface2"),
        ink: v("ink"), muted: v("muted"),
        primary: v("primary"), secondary: v("secondary"), accent: v("accent"),
        danger: v("danger"),
      },
      fontFamily: {
        display: ['"Bricolage Grotesque Variable"', "system-ui", "sans-serif"],
        body: ['"Figtree Variable"', "system-ui", "sans-serif"],
      },
      borderRadius: { tile: "1.25rem" },
      screens: { lg: "1024px" },
    },
  },
  plugins: [],
};
