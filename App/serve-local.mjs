import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
try {
  const env = await readFile(path.join(root,'.env.local'),'utf8');
  for (const line of env.split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Z_]+)\s*=\s*(.*?)\s*$/);
    // Explicit local configuration takes priority over inherited machine settings.
    if (match) process.env[match[1]] = match[2].replace(/^(['"])(.*)\1$/, '$2');
  }
} catch(error) { if(error.code !== 'ENOENT') throw error; }
const {default:extract} = await import(pathToFileURL(path.join(root,'api/extract.js')).href);
const publicFiles = new Set(['index.html','app.js','styles.css','pink-form-original.html','pink-form-dynamic.html','samples/SampleA1815.pdf','samples/SampleL16.pdf','samples/SampleM28.pdf']);
const types = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.pdf':'application/pdf'};
http.createServer(async(req,res)=>{
  try {
    const pathname = new URL(req.url,'http://localhost').pathname;
    if(pathname === '/api/extract') {
      res.status = status => {res.statusCode=status;return res;};
      res.json = data => {res.setHeader('Content-Type','application/json');res.end(JSON.stringify(data));};
      let size=0;const chunks=[];
      for await(const chunk of req) {size+=chunk.length;if(size>4200000) return res.status(413).json({error:'Request too large'});chunks.push(chunk);}
      try {req.body=JSON.parse(Buffer.concat(chunks).toString() || '{}');} catch {return res.status(400).json({error:'Invalid JSON'});}
      return await extract(req,res);
    }
    const file = decodeURIComponent(pathname === '/' ? 'index.html' : pathname.slice(1));
    if(!publicFiles.has(file)) {res.writeHead(404);return res.end('Not found');}
    const data=await readFile(path.join(root,file));
    res.writeHead(200,{'Content-Type':types[path.extname(file)] || 'application/octet-stream','Cache-Control':'no-store'});res.end(data);
  } catch {res.writeHead(500);res.end('Local server error');}
}).listen(3000,'127.0.0.1',()=>console.log('Pink Card running at http://127.0.0.1:3000'));
