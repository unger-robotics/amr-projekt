import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import fs from 'fs'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    https: {
      key:  fs.readFileSync(path.resolve(__dirname, 'amr.local+5-key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, 'amr.local+5.pem')),
    },
  },
})
