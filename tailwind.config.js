module.exports = {
  darkMode: 'class',
  content: [
    './web/index.html',
    './web/**/*.js'
  ],
  safelist: [
    {
      pattern: /(bg|text|border)-(blue|green|red|amber|purple|indigo|orange|gray|slate|pink|emerald|rose)-(50|100|200|300|400|500|600|700|800|900)/
    },
    {
      pattern: /(dark:)?(bg|text|border)-(blue|green|red|amber|purple|indigo|orange|gray|slate|pink|emerald|rose)-(50|100|200|300|400|500|600|700|800|900)\/(10|20|30|40|50|60)/
    }
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Helvetica Neue', 'Segoe UI', 'sans-serif']
      }
    }
  }
}
