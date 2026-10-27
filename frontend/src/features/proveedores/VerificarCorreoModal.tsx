/**
 * Verificación del correo de un proveedor: se envía un código al correo y se confirma aquí.
 * Sin correo verificado el backend no envía órdenes de reposición a ese proveedor.
 */
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { ApiError } from '@/api/client'
import { proveedoresApi } from '@/api/proveedores'
import { queryKeys } from '@/api/queryKeys'
import type { Proveedor } from '@/api/types'
import { Button, Field, Input, Modal, useToast } from '@/components/ui'
import { FormAlert } from '@/features/inventario/formUtils'

export function VerificarCorreoModal({ proveedor, onClose }: { proveedor: Proveedor | null; onClose: () => void }) {
  return proveedor ? <Abierto proveedor={proveedor} onClose={onClose} /> : null
}

function Abierto({ proveedor, onClose }: { proveedor: Proveedor; onClose: () => void }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [codigo, setCodigo] = useState('')
  const [aviso, setAviso] = useState<{ tone: 'info' | 'danger'; texto: string } | null>(null)
  const [ocupado, setOcupado] = useState(false)

  const correr = async (f: () => Promise<void>) => {
    setOcupado(true)
    try {
      await f()
    } catch (e) {
      setAviso({ tone: 'danger', texto: e instanceof ApiError ? e.detail : 'Ocurrió un error inesperado.' })
    } finally {
      setOcupado(false)
    }
  }

  const enviar = () =>
    correr(async () => {
      const r = await proveedoresApi.enviarVerificacion(proveedor.id_proveedor)
      // El backend devuelve su propio estado (enviado, en espera, error de envío…): se muestra tal cual.
      const detalle = [r.status, r.reason, r.remaining_seconds ? `espera ${r.remaining_seconds} s` : null].filter(Boolean).join(' · ')
      setAviso({ tone: /error|bloque|fall/i.test(r.status) ? 'danger' : 'info', texto: `Respuesta del servidor: ${detalle}` })
    })

  const verificar = () =>
    correr(async () => {
      const r = await proveedoresApi.verificarCorreo(proveedor.id_proveedor, codigo.trim())
      if (!r.verified) {
        setAviso({ tone: 'danger', texto: `Código no válido (${r.status})${r.remaining_attempts != null ? ` · intentos restantes: ${r.remaining_attempts}` : ''}` })
        return
      }
      await qc.invalidateQueries({ queryKey: queryKeys.proveedores.all })
      toast.success(`El correo de ${proveedor.nombre} quedó verificado.`, 'Correo verificado')
      onClose()
    })

  return (
    <Modal open onClose={onClose} dismissable={!ocupado} size="sm" title="Verificar correo" description={`${proveedor.nombre} · ${proveedor.correo}`}>
      <div className="flex flex-col gap-4">
        <p className="text-sm text-fg-muted">Envía un código al correo del proveedor y escríbelo aquí. Sin esto no se le pueden enviar órdenes.</p>
        <Button variant="secondary" onClick={() => void enviar()} loading={ocupado}>
          Enviar código
        </Button>
        {aviso && <FormAlert tone={aviso.tone}>{aviso.texto}</FormAlert>}
        <Field label="Código recibido">
          <Input className="font-mono" inputMode="numeric" autoComplete="one-time-code" value={codigo} onChange={(e) => setCodigo(e.target.value)} />
        </Field>
        <Button onClick={() => void verificar()} loading={ocupado} disabled={codigo.trim() === ''}>
          Verificar
        </Button>
      </div>
    </Modal>
  )
}
