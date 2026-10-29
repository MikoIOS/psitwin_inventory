import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { authApi } from '@/api/auth'
import { Button } from '@/components/ui'
import { AuthLayout } from './AuthLayout'

export default function VerifyEmailPage() {
  const [token] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get('token') || '')
  useEffect(() => { window.history.replaceState(null, '', window.location.pathname) }, [])
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')
  async function confirm() {
    setBusy(true); setError('')
    try { await authApi.confirmVerification(token); setDone(true) }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo verificar el enlace.') }
    finally { setBusy(false) }
  }
  return <AuthLayout title="Verificar correo" subtitle="Activa tu cuenta PsiTwin."
    footer={<Link to="/login">Inicia sesión</Link>}>
    {done ? <p role="status">Correo verificado. Tu cuenta está activa; ya puedes iniciar sesión con tu Gmail y contraseña de PsiTwin.</p> : <>
      <p className="mb-4">Confirma tu correo para activar tu empresa. Este enlace solo puede utilizarse una vez.</p>
      {error && <p role="alert" className="mb-4 text-danger">{error}</p>}
      <Button disabled={!token} loading={busy} onClick={() => void confirm()}>Verificar correo y activar cuenta</Button>
      {!token && <p className="mt-4">No hay un enlace válido. Abre el enlace de tu correo o solicita otro.</p>}
      <p className="mt-5"><Link to="/registro">Solicitar otro enlace</Link></p>
    </>}
  </AuthLayout>
}
