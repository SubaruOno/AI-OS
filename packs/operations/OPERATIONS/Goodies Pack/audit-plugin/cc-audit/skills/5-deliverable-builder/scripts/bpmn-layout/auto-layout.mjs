import { layoutProcess } from 'bpmn-auto-layout-extended';
import { readFileSync, writeFileSync } from 'fs';

const input = process.argv[2];
const output = process.argv[3];

if (!input || !output) {
  process.stderr.write('Usage: node auto-layout.mjs <input.bpmn> <output.bpmn>\n');
  process.exit(1);
}

try {
  const xml = readFileSync(input, 'utf8');
  const result = await layoutProcess(xml);
  writeFileSync(output, result);
} catch (err) {
  process.stderr.write(`Auto-layout error: ${err.message}\n`);
  process.exit(1);
}
