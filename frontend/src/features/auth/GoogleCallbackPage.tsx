import { useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router'
import { api, ApiError } from '@/api/client'
import { authApi, useAplicarLogin } from '@/api/auth'
import { googleBinding, clearGoogleFlow, saveGoogleRegistration, saveGoogleFlowError, type GoogleResult } from './googleAuth'
import { AuthLayout } from './AuthLayout'

export default function GoogleCallbackPage() {
  const started = useRef(false)
  const apply = useAplicarLogin()
  const navigate = useNavigate()
  useEffect(() => {
    if (started.current) return
    started.current = true
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code'), state = params.get('state')
    window.history.replaceState(null, '', window.location.pathname)
    if (!code || !state || params.has('error')) {
      saveGoogleFlowError('La verificación con Google se canceló o no es válida. Tus datos empresariales se conservaron.')
      navigate('/registro', { replace: true }); return
    }
    void api.post<GoogleResult>('/auth/google/complete', { code, state, binding: googleBinding() }, { auth: false }).then(result => {
      if (result.registration_required && result.registration_ticket) {
        saveGoogleRegistration(result.registration_ticket, result.verified_email, result.company)
        navigate('/registro?google=continuar', { replace: true })
      } else {
        apply(authApi.fromGoogle(result))
        clearGoogleFlow()
        navigate('/', { replace: true })
      }
    }).catch((err: unknown) => {
      saveGoogleFlowError(err instanceof ApiError ? err.detail : 'No se pudo completar la verificación con Google. Intenta nuevamente.')
      navigate('/registro', { replace: true })
    })
  }, [apply, navigate])
  return <AuthLayout title="Verificación de Gmail" subtitle="Validando tu identidad…" footer={<Link to="/registro">Volver al registro</Link>}>
    <p role="status">Estamos comprobando tu correo de registro.</p>
  </AuthLayout>
}
