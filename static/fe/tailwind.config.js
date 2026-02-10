/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.html",
    "./src/components/**/*.html",
    "./src/js/**/*.js",
  ],
theme: {
    container: {
      center: true, 
      padding: '1rem', 
    },
    screens: {
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px', 
    },
    extend: {
      gridTemplateColumns: {
            
            'custom-3': '2fr 1fr', 
        },
      fontFamily: {
        poppins: ['Poppins', 'sans-serif'],
      },
    },
  },
  
  plugins: [],
}

