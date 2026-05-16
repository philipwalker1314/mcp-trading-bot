'use client'

import { useEffect, useRef } from 'react'
import { api } from '@/lib/api'
import { useStrategiesStore, StrategyConfig } from '@/store/strategies'

export function useStrategies() {
  const {
    setStrategies,
    upsertStrategy,
    removeStrategy,
    setLoading,
    setSaving,
    setValidating,
    setValidationResult,
    setVersions,
    setVersionsLoading,
  } = useStrategiesStore()

  const pollRef = useRef<ReturnType<typeof setInterval>>()

  async function reload() {
    setLoading(true)
    try {
      const res = await api.strategies.list()
      setStrategies(res.data ?? [])
    } catch {
      // silent — keep stale data
    } finally {
      setLoading(false)
    }
  }

  async function createStrategy(data: Partial<StrategyConfig>) {
    setSaving(true)
    try {
      const res = await api.strategies.create(data)
      upsertStrategy(res.data)
      return res.data
    } finally {
      setSaving(false)
    }
  }

  async function updateStrategy(id: number, data: Partial<StrategyConfig>) {
    setSaving(true)
    try {
      const res = await api.strategies.update(id, data)
      upsertStrategy(res.data)
      return res.data
    } finally {
      setSaving(false)
    }
  }

  async function deleteStrategy(id: number) {
    await api.strategies.delete(id)
    removeStrategy(id)
  }

  async function enableStrategy(id: number) {
    const res = await api.strategies.enable(id)
    upsertStrategy(res.data)
    return res.data
  }

  async function disableStrategy(id: number) {
    const res = await api.strategies.disable(id)
    upsertStrategy(res.data)
    return res.data
  }

  async function rollbackStrategy(id: number, targetVersion: number) {
    const res = await api.strategies.rollback(id, targetVersion)
    upsertStrategy(res.data)
    await reload()
    return res.data
  }

  async function validateStrategy(data: Partial<StrategyConfig>) {
    setValidating(true)
    setValidationResult(null)
    try {
      const res = await api.strategies.validate(data)
      setValidationResult(res.data)
      return res.data
    } finally {
      setValidating(false)
    }
  }

  async function loadVersions(id: number) {
    setVersionsLoading(true)
    try {
      const res = await api.strategies.versions(id)
      setVersions(res.data ?? [])
    } finally {
      setVersionsLoading(false)
    }
  }

  useEffect(() => {
    reload()
    pollRef.current = setInterval(reload, 30_000)
    return () => clearInterval(pollRef.current)
  }, [])

  return {
    reload,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    enableStrategy,
    disableStrategy,
    rollbackStrategy,
    validateStrategy,
    loadVersions,
  }
}
