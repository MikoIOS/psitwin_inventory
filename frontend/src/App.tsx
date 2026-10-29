import { MutationCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router'
import { ApiError } from '@/api/client'
import { SessionProvider } from '@/auth/SessionContext'
import { ToastProvider } from '@/components/ui'
import { router } from '@/routes'

export const queryClient = new QueryClient({
  mutationCache: new MutationCache({ onSuccess: () => {
    void queryClient.invalidateQueries({ queryKey: ['plano'] })
  } }),
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // No reintentar errores del cliente (4xx): solo red / 5xx, hasta 2 veces.
      retry: (failureCount, error) => {
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false
        return failureCount < 2
      },
    },
    mutations: { retry: false },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </SessionProvider>
    </QueryClientProvider>
  )
}
