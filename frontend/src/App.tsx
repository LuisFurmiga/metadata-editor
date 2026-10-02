import { useEffect, useRef, useState } from 'react';
import { Header } from './components/Header';
import { Modal } from './components/Modal';
import { UploadZone } from './components/UploadZone';
import { useTheme } from './contexts/ThemeContext';
import { Dashboard } from './pages/Dashboard';
import { api } from './services/api';
import type { FileMetadata, Health } from './types';

const FILE_ROUTE = /^\/files\/([0-9a-f-]{36})$/i;

export default function App() {
  const [data, setData] = useState<FileMetadata | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [uploading, setUploading] = useState(false);
  const [settings, setSettings] = useState(false);
  const [toast, setToast] = useState('');
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() =>
      setHealth({ status: 'offline', exiftool: { available: false, version: null } }),
    );
    const fileId = window.location.pathname.match(FILE_ROUTE)?.[1];
    if (fileId) {
      setUploading(true);
      api.metadata(fileId)
        .then(setData)
        .catch(() => {
          history.replaceState(null, '', '/');
          setToast('A sessão deste arquivo expirou ou já foi encerrada.');
        })
        .finally(() => setUploading(false));
    }
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(''), 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  const upload = async (file: File) => {
    controller.current = new AbortController();
    setUploading(true);
    try {
      const uploaded = await api.upload(file, controller.current.signal);
      setData(uploaded);
      history.pushState({ fileId: uploaded.file.id }, '', `/files/${uploaded.file.id}`);
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        setToast(error instanceof Error ? error.message : 'Falha ao enviar arquivo');
      }
    } finally {
      setUploading(false);
    }
  };

  const closeSession = () => {
    setData(null);
    history.replaceState(null, '', '/');
  };

  return (
    <>
      <Header onSettings={() => setSettings(true)} />
      {health && !health.exiftool.available && (
        <div className="flex items-center justify-center gap-3 bg-amber-100 px-4 py-2 text-center text-sm text-amber-900">
          <b>ExifTool não encontrado.</b>
          <span>Instale-o para analisar arquivos.</span>
          <button className="underline" onClick={() => api.health().then(setHealth)}>
            Tentar novamente
          </button>
        </div>
      )}
      {data ? (
        <Dashboard
          data={data}
          setData={setData}
          onClose={closeSession}
          onToast={setToast}
        />
      ) : (
        <UploadZone
          onFile={upload}
          busy={uploading}
          onCancel={() => controller.current?.abort()}
        />
      )}
      {settings && <Settings onClose={() => setSettings(false)} />}
      {toast && (
        <div
          role="status"
          className="fixed bottom-5 right-5 z-[60] max-w-sm rounded-xl bg-ink-900 px-5 py-4 text-sm text-white shadow-xl dark:bg-white dark:text-ink-900"
        >
          {toast}
        </div>
      )}
    </>
  );
}

function Settings({ onClose }: { onClose: () => void }) {
  const { theme, setTheme } = useTheme();
  return (
    <Modal title="Configurações" onClose={onClose}>
      <label className="block text-sm font-medium">Tema</label>
      <div className="mt-3 grid grid-cols-3 gap-2">
        {(['light', 'dark', 'system'] as const).map((option) => (
          <button
            key={option}
            onClick={() => setTheme(option)}
            className={`rounded-xl border px-3 py-3 text-sm ${theme === option ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-500/10' : 'border-ink-100 dark:border-white/10'}`}
          >
            {option === 'light' ? 'Claro' : option === 'dark' ? 'Escuro' : 'Sistema'}
          </button>
        ))}
      </div>
      <div className="mt-6 border-t border-ink-100 pt-5 dark:border-white/10">
        <label className="block text-sm font-medium">Idioma</label>
        <select className="field mt-2" disabled>
          <option>Português (Brasil)</option>
        </select>
        <p className="mt-2 text-xs text-ink-400">
          Outros idiomas poderão ser adicionados futuramente.
        </p>
      </div>
    </Modal>
  );
}
