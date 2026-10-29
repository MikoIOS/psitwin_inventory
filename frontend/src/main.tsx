import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import './index.css'
import { installChunkRecovery } from './lib/chunkRecovery'

installChunkRecovery()

const root = document.getElementById('root')
if (!root) throw new Error('No se encontró #root')

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
