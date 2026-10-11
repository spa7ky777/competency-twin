import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/subjects': 'http://localhost:8000',
      '/units': 'http://localhost:8000',
      '/topics': 'http://localhost:8000',
      '/competencies': 'http://localhost:8000',
      '/documents': 'http://localhost:8000',
      '/demo': 'http://localhost:8000',
      '/rag': 'http://localhost:8000',
      '/quizzes': 'http://localhost:8000',
      '/attempts': 'http://localhost:8000',
      '/questions': 'http://localhost:8000',
      '/diagnostic': 'http://localhost:8000',
      '/students': 'http://localhost:8000',
      '/trainer': 'http://localhost:8000',
      '/config': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
