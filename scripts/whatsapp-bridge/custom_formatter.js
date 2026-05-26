export const DEFAULT_REPLY_PREFIX = '⚕ *Rok*\n────────────\n';

export function formatCard(card) {
  const { title, rows, footer } = card;
  const width = 34; // standard whatsapp width for monospace
  const borderTop = '╔' + '═'.repeat(width - 2) + '╗';
  const borderBottom = '╚' + '═'.repeat(width - 2) + '╝';
  const separator = '╟' + '─'.repeat(width - 2) + '╢';

  function padLine(text) {
    let clean = String(text || '');
    if (clean.length > width - 4) {
      clean = clean.substring(0, width - 7) + '...';
    }
    const padding = ' '.repeat(width - 4 - clean.length);
    return `║ ${clean}${padding} ║`;
  }

  const lines = [borderTop, padLine(title), separator];
  
  for (const row of rows || []) {
    lines.push(padLine(row));
  }

  if (footer) {
    lines.push(separator);
    lines.push(padLine(footer));
  }

  lines.push(borderBottom);
  return '```\n' + lines.join('\n') + '\n```';
}
