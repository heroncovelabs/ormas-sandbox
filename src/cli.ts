import { slugify } from './slugify.ts';

const [input = ''] = process.argv.slice(2);
console.log(slugify(input));
