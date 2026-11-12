import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash, timingSafeEqual} from 'node:crypto';
const samples = new Set(['SampleA1815.pdf', 'SampleL16.pdf', 'SampleM28.pdf']);
export const config = { maxDuration: 120 };
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({error:'POST required'});
  try {
    const {images, accessCode, sample, model:choice = 'gpt-4.1-mini'} = req.body || {};
    const expected = process.env.OPENAI_ACCESS_CODE;
    const hash = value => createHash('sha256').update(value).digest();
    const authorized = typeof expected === 'string' && expected.length > 0 && typeof accessCode === 'string' && timingSafeEqual(hash(accessCode), hash(expected));
    if (!authorized) {
      if (!samples.has(sample)) return res.status(403).json({error:'A valid access code is required for uploaded PDFs. Choose a bundled sample to use saved results.'});
      try {
        const data = JSON.parse(await readFile(path.join(process.cwd(), 'samples', sample.replace(/\.pdf$/, '.json')), 'utf8'));
        if (!data.header || !Array.isArray(data.visits)) throw new Error('Invalid sample');
        return res.status(200).json({...data, source:'sample'});
      } catch { return res.status(503).json({error:'Saved results for this sample are unavailable.'}); }
    }
    if (!process.env.OPENAI_API_KEY) return res.status(503).json({error:'Configure OPENAI_API_KEY in Vercel.'});
    if (!['gpt-4.1-mini','latest'].includes(choice)) return res.status(400).json({error:'Unsupported model selection.'});
    const model = choice === 'latest' ? (process.env.OPENAI_LATEST_MODEL || 'gpt-6.1-sol') : 'gpt-4.1-mini';
    if (!Array.isArray(images) || images.length !== 2 || images.some(x => typeof x !== 'string' || !x.startsWith('data:image/jpeg;base64,'))) return res.status(400).json({error:'Two JPEG page images are required.'});
    if (JSON.stringify(images).length > 4000000) return res.status(413).json({error:'Images are too large. Reduce preview quality.'});
    const upstream = await fetch('https://api.openai.com/v1/responses', {
      method:'POST', headers:{Authorization:`Bearer ${process.env.OPENAI_API_KEY}`,'Content-Type':'application/json'},
      signal:AbortSignal.timeout(110000),
      body:JSON.stringify({model,store:false,text:{format:{type:'json_object'}},input:[{role:'user',content:[{type:'input_text',text:'Transcribe this two-page PMTCT pink card faithfully as JSON {"header":{},"visits":[]}. Use snake_case field keys matching the card: header unique_child_id,hcc_reg_no,transfer_in_date,birth_cohort_month,birth_cohort_year,child_name,guardian_name,physical_address,sex,child_age,agrees_to_fup,guardian_relation,guardian_phone,mother_status_enrolment,art_reg_no,art_start_date,age_at_enrolment,nvp_start_date,nvp_duration,birth_date,birth_weight_kg and hiv_test_0_sample_date,type,sample_id,result,date_received (repeat complete hiv_test_N_ prefix for N=0,1,2,3). Visits: age_months,visit_date,height_cm,weight_kg,muac_cm,wasting_malnutrition,breastfeeding,stopped_lt6m,stopped_ge6m,mother_status,abdominal_exam,hiv_testing,hiv_infection,cpt,follow_up,next_appointment_date. Use empty strings for unreadable or absent values, preserve codes and doses, dates YYYY-MM-DD only where unambiguous, never invent values. All values strings. Include every recorded visit.'},...images.map(image_url=>({type:'input_image',image_url,detail:'high'}))]}]})
    });
    if (!upstream.ok) return res.status(502).json({error:`OpenAI request failed (${upstream.status}). Check model access, quota, and server configuration.`});
    const response = await upstream.json();
    const text = (response.output || []).flatMap(x=>x.content || []).filter(x=>x.type==='output_text').map(x=>x.text).join('');
    const data = JSON.parse(text);
    if (response.status !== 'completed' || !data.header || !Array.isArray(data.visits)) throw new Error('Incomplete extraction');
    return res.status(200).json({...data, source:'openai'});
  } catch { return res.status(502).json({error:'Extraction did not complete. Please retry.'}); }
}
