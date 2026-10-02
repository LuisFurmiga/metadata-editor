import { ChevronDown, Copy, Info, Star } from 'lucide-react';
import { useState } from 'react';
import type { MetadataField } from '../types';
import { stringify } from '../utils/format';

interface MetadataTableProps {
  fields: MetadataField[];
  pending: Record<string, unknown>;
  favorites: string[];
  technical: boolean;
  onEdit: (tag: string, value: unknown) => void;
  onFavorite: (tag: string) => void;
  onToast: (message: string) => void;
}

export function MetadataTable({
  fields,
  pending,
  favorites,
  technical,
  onEdit,
  onFavorite,
  onToast,
}: MetadataTableProps) {
  const groups = fields.reduce<Record<string, MetadataField[]>>((result, field) => {
    (result[field.group] ??= []).push(field);
    return result;
  }, {});
  const [closed, setClosed] = useState<string[]>([]);
  const [openHelp, setOpenHelp] = useState<string | null>(null);

  const copy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    onToast('Copiado para a área de transferência');
  };

  return (
    <div className="space-y-4">
      {Object.entries(groups).map(([group, items]) => (
        <section
          key={group}
          className="rounded-2xl border border-ink-100 bg-white dark:border-white/10 dark:bg-ink-800"
        >
          <button
            onClick={() =>
              setClosed((current) =>
                current.includes(group)
                  ? current.filter((item) => item !== group)
                  : [...current, group],
              )
            }
            className="flex w-full items-center justify-between px-5 py-4 text-left"
          >
            <span className="text-xs font-bold uppercase tracking-[.14em] text-ink-500">
              {group}
              <b className="ml-2 rounded-full bg-ink-50 px-2 py-1 text-[10px] dark:bg-white/5">
                {items.length}
              </b>
            </span>
            <ChevronDown size={16} className={closed.includes(group) ? '-rotate-90' : ''} />
          </button>

          {!closed.includes(group) && (
            <div className="divide-y divide-ink-100 dark:divide-white/10">
              {items.map((field) => {
                const changed = field.fullName in pending;
                const value = changed ? pending[field.fullName] : field.value;
                const helpVisible = openHelp === field.fullName;

                return (
                  <div
                    key={field.fullName}
                    className={`grid gap-3 px-5 py-4 transition md:grid-cols-[minmax(220px,.8fr)_minmax(240px,1.2fr)_72px] ${changed ? 'bg-amber-50/80 dark:bg-amber-500/5' : ''}`}
                  >
                    <div className="relative">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onFavorite(field.fullName)}
                          aria-label={`Favoritar ${field.displayName}`}
                        >
                          <Star
                            size={15}
                            className={
                              favorites.includes(field.fullName)
                                ? 'fill-amber-400 text-amber-400'
                                : 'text-ink-400'
                            }
                          />
                        </button>
                        <span className="font-medium">{field.displayName}</span>
                        {field.helpText && (
                          <button
                            type="button"
                            className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-ink-400 hover:bg-ink-50 hover:text-brand-600 dark:hover:bg-white/5"
                            aria-label={`Como preencher ${field.displayName}`}
                            aria-expanded={helpVisible}
                            onClick={() => setOpenHelp(helpVisible ? null : field.fullName)}
                          >
                            <Info size={15} />
                          </button>
                        )}
                        {changed && (
                          <span className="badge bg-amber-100 text-amber-700">alterado</span>
                        )}
                        {field.suggested && !changed && (
                          <span className="badge bg-brand-100 text-brand-700">disponível</span>
                        )}
                      </div>
                      {technical && (
                        <code className="mt-1 block text-xs text-ink-400">{field.fullName}</code>
                      )}
                      {field.helpText && helpVisible && (
                        <div
                          id={`help-${field.fullName}`}
                          role="note"
                          className="mt-3 max-w-md rounded-xl border border-brand-100 bg-brand-50 p-3 text-xs leading-relaxed text-ink-700 dark:border-brand-500/20 dark:bg-brand-500/10 dark:text-ink-100"
                        >
                          <b className="mb-1 block text-brand-700 dark:text-brand-100">
                            Como preencher
                          </b>
                          {field.helpText}
                        </div>
                      )}
                    </div>

                    {field.editable ? (
                      <input
                        className="field"
                        aria-label={field.displayName}
                        aria-describedby={field.helpText ? `help-${field.fullName}` : undefined}
                        type={field.valueType === 'number' ? 'number' : 'text'}
                        value={stringify(value)}
                        onChange={(event) => onEdit(field.fullName, event.target.value)}
                      />
                    ) : (
                      <span className="break-all text-sm text-ink-600 dark:text-ink-300">
                        {stringify(value) || <em className="text-ink-400">vazio</em>}
                      </span>
                    )}
                    <div className="flex justify-end gap-1">
                      <button
                        className="icon-btn-sm"
                        onClick={() => copy(stringify(value))}
                        title="Copiar valor"
                      >
                        <Copy size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
