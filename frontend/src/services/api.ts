import type { ApiError, FileMetadata, Health, PrivacyItem } from '../types';

const base = import.meta.env.VITE_API_URL ?? '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, init);
  if (!response.ok) {
    let message = 'Não foi possível concluir a operação.';
    try {
      message = ((await response.json()) as ApiError).error.message;
    } catch {
      // The fallback remains useful for an empty or non-JSON response.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function editedName(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot > 0
    ? `${name.slice(0, dot)}-editado${name.slice(dot)}`
    : `${name}-editado`;
}

export const api = {
  health: () => request<Health>('/health'),
  upload: (file: File, signal?: AbortSignal) => {
    const form = new FormData();
    form.append('file', file);
    return request<FileMetadata>('/files', { method: 'POST', body: form, signal });
  },
  metadata: (id: string) => request<FileMetadata>(`/files/${id}/metadata`),
  save: (id: string, changes: { tag: string; value: unknown }[]) =>
    request<FileMetadata>(`/files/${id}/metadata`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ changes }),
    }),
  restore: (id: string) =>
    request<FileMetadata>(`/files/${id}/restore`, { method: 'POST' }),
  removeGps: (id: string) =>
    request<FileMetadata>(`/files/${id}/remove-gps`, { method: 'POST' }),
  removeAll: (id: string) =>
    request<FileMetadata>(`/files/${id}/remove-metadata`, { method: 'POST' }),
  privacy: async (id: string) =>
    (await request<{ items: PrivacyItem[] }>(`/files/${id}/privacy`)).items,
  removeSelected: (id: string, tags: string[]) =>
    request<FileMetadata>(`/files/${id}/remove-selected`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags }),
    }),
  exportUrl: (id: string, format: string) =>
    `${base}/files/${id}/export/${format}`,
  downloadAndFinalize: async (id: string, originalName: string) => {
    const response = await fetch(`${base}/files/${id}/download?finalize=true`);
    if (!response.ok) throw new Error('Não foi possível baixar o arquivo editado.');
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = editedName(originalName);
    anchor.click();
    URL.revokeObjectURL(url);
  },
  delete: (id: string) => request<void>(`/files/${id}`, { method: 'DELETE' }),
};
