export const formatBytes = (bytes: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'unit',
    unit: bytes > 1048576 ? 'megabyte' : 'kilobyte',
    maximumFractionDigits: 1,
  }).format(bytes / (bytes > 1048576 ? 1048576 : 1024));

/** Format ExifTool list values for editing without exposing JSON syntax. */
export const stringify = (value: unknown): string => {
  if (Array.isArray(value)) {
    return value.map((item) => stringify(item)).join('; ');
  }
  if (value !== null && typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value ?? '');
};
