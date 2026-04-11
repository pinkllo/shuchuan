import { computed } from 'vue'
import { useSessionStore, type UserRole } from '@/stores/session'

type Action =
  | 'catalog.create' | 'catalog.edit' | 'catalog.delete'
  | 'demand.create' | 'demand.approve' | 'demand.upload'
  | 'task.create' | 'task.manage'
  | 'delivery.download' | 'delivery.feedback'
  | 'integration.configure'

const actionRoles: Record<Action, UserRole[]> = {
  'catalog.create':          ['provider'],
  'catalog.edit':            ['provider'],
  'catalog.delete':          ['provider'],
  'demand.create':           ['aggregator'],
  'demand.approve':          ['provider'],
  'demand.upload':           ['provider'],
  'task.create':             ['aggregator'],
  'task.manage':             ['aggregator'],
  'delivery.download':       ['consumer', 'aggregator'],
  'delivery.feedback':       ['consumer'],
  'integration.configure':   ['aggregator']
}

export function usePermission() {
  const session = useSessionStore()

  const isProvider   = computed(() => session.role === 'provider')
  const isAggregator = computed(() => session.role === 'aggregator')
  const isConsumer   = computed(() => session.role === 'consumer')
  const role         = computed(() => session.role)

  function can(action: Action) {
    return actionRoles[action]?.includes(session.role) ?? false
  }

  return { isProvider, isAggregator, isConsumer, role, can }
}
