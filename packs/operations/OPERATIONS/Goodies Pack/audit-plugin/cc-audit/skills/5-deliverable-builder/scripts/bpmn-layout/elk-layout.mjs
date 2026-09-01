import ELK from 'elkjs/lib/elk.bundled.js';
import { readFileSync, writeFileSync } from 'fs';

const input = process.argv[2];
const output = process.argv[3];

if (!input || !output) {
  process.stderr.write('Usage: node elk-layout.mjs <input.json> <output.json>\n');
  process.exit(1);
}

const graph = JSON.parse(readFileSync(input, 'utf8'));
const elk = new ELK();

try {
  const result = await elk.layout(graph);
  writeFileSync(output, JSON.stringify(result));
} catch (err) {
  process.stderr.write(`ELK error: ${err.message}\n`);
  process.exit(1);
}
