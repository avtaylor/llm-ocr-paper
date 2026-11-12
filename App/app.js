const appState = {
  folderHandle: null,
  folderName: '',
  pdfFile: null,
  pdfFileName: '',
  outputFormat: 'png',
  scale: 2,
  pdfDoc: null,
  rotations: { page1: 0, page2: 0 },
  savedImages: [],
  reviewFileName: '',
  reviewRows: [],
  reviewGroups: new Map(),
  selectedChildId: '',
  cohortFileName: '',
  cohortRows: [],
  cohortGroups: new Map(),
  selectedFacility: '__all__'
};

import * as pdfjsLib from 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs';
if (pdfjsLib) {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs';
}

const els = {
  workingDirDisplay: document.getElementById('workingDirDisplay'),
  selectFolderBtn: document.getElementById('selectFolderBtn'),
  pdfFileDisplay: document.getElementById('pdfFileDisplay'),
  selectPdfBtn: document.getElementById('selectPdfBtn'),
  outputFormat: document.getElementById('outputFormat'),
  scaleSelect: document.getElementById('scaleSelect'),
  openPdfWorkspaceBtn: document.getElementById('openPdfWorkspaceBtn'),
  openFormBtn: document.getElementById('openFormBtn'),
  statusMessage: document.getElementById('statusMessage'),
  homeSection: document.getElementById('homeSection'),
  pdfSection: document.getElementById('pdfSection'),
  formSection: document.getElementById('formSection'),
  reviewSection: document.getElementById('reviewSection'),
  cohortSection: document.getElementById('cohortSection'),
  page1Canvas: document.getElementById('page1Canvas'),
  page2Canvas: document.getElementById('page2Canvas'),
  page1RotationValue: document.getElementById('page1RotationValue'),
  page2RotationValue: document.getElementById('page2RotationValue'),
  savedImagesDisplay: document.getElementById('savedImagesDisplay'),
  pinkFormFrame: document.getElementById('pinkFormFrame'),
  sidebarFolderStatus: document.getElementById('sidebarFolderStatus'),
  sidebarPdfStatus: document.getElementById('sidebarPdfStatus'),
  sidebarImagesStatus: document.getElementById('sidebarImagesStatus'),
  reviewFileDisplay: document.getElementById('reviewFileDisplay'),
  openReviewBtn: document.getElementById('openReviewBtn'),
  reviewEmpty: document.getElementById('reviewEmpty'),
  reviewContent: document.getElementById('reviewContent'),
  reviewSubtitle: document.getElementById('reviewSubtitle'),
  reviewChildSelect: document.getElementById('reviewChildSelect'),
  previousChildBtn: document.getElementById('previousChildBtn'),
  nextChildBtn: document.getElementById('nextChildBtn'),
  reviewPatientMeta: document.getElementById('reviewPatientMeta'),
  reviewVisitCount: document.getElementById('reviewVisitCount'),
  reviewIssueCount: document.getElementById('reviewIssueCount'),
  reviewLatestWeight: document.getElementById('reviewLatestWeight'),
  reviewLatestVisit: document.getElementById('reviewLatestVisit'),
  weightChart: document.getElementById('weightChart'),
  dateStatusBadge: document.getElementById('dateStatusBadge'),
  dateIssues: document.getElementById('dateIssues'),
  reviewHistoryBody: document.getElementById('reviewHistoryBody'),
  testMatchSummary: document.getElementById('testMatchSummary'),
  testAnalysisEmpty: document.getElementById('testAnalysisEmpty'),
  testAnalysisTableWrap: document.getElementById('testAnalysisTableWrap'),
  testAnalysisBody: document.getElementById('testAnalysisBody'),
  cohortFileDisplay: document.getElementById('cohortFileDisplay'),
  openCohortBtn: document.getElementById('openCohortBtn'),
  cohortEmpty: document.getElementById('cohortEmpty'),
  cohortContent: document.getElementById('cohortContent'),
  cohortSubtitle: document.getElementById('cohortSubtitle'),
  cohortFacilitySelect: document.getElementById('cohortFacilitySelect'),
  cohortMeta: document.getElementById('cohortMeta'),
  scheduleEvidenceBadge: document.getElementById('scheduleEvidenceBadge'),
  scheduleAnalysisSummary: document.getElementById('scheduleAnalysisSummary'),
  scheduleAnalysedCount: document.getElementById('scheduleAnalysedCount'),
  consistentRetentionRate: document.getElementById('consistentRetentionRate'),
  issueRetentionRate: document.getElementById('issueRetentionRate'),
  scheduleOddsRatio: document.getElementById('scheduleOddsRatio'),
  scheduleAnalysisBody: document.getElementById('scheduleAnalysisBody')
};

function setStatus(text) {
  els.statusMessage.textContent = `Status: ${text}`;
}

function showSection(section) {
  [els.homeSection, els.pdfSection, els.formSection, els.reviewSection, els.cohortSection].forEach(el => el.classList.remove('active'));
  section.classList.add('active');
  render();
}

function normalizeRotation(v) {
  let n = v % 360;
  if (n < 0) n += 360;
  return n;
}

function render() {
  els.workingDirDisplay.textContent = appState.folderName || 'Not selected';
  els.pdfFileDisplay.value = appState.pdfFileName || '';
  els.outputFormat.value = appState.outputFormat;
  els.scaleSelect.value = String(appState.scale);
  els.openPdfWorkspaceBtn.disabled = !appState.pdfFile;
  els.page1RotationValue.textContent = `${appState.rotations.page1}°`;
  els.page2RotationValue.textContent = `${appState.rotations.page2}°`;
  els.savedImagesDisplay.textContent = appState.savedImages.length ? appState.savedImages.join('\n') : 'No images saved yet';
  els.sidebarFolderStatus.textContent = appState.folderName || 'Not selected';
  els.sidebarPdfStatus.textContent = appState.pdfFileName ? 'Yes' : 'No';
  els.sidebarImagesStatus.textContent = appState.savedImages.length ? appState.savedImages.join(', ') : 'None yet';
  els.reviewFileDisplay.value = appState.reviewFileName;
  els.openReviewBtn.disabled = !appState.reviewRows.length;
  els.cohortFileDisplay.value = appState.cohortFileName;
  els.openCohortBtn.disabled = !appState.cohortRows.length;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function parseCsv(text) {
  const records = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (char === '"') quoted = false;
      else field += char;
    } else if (char === '"') quoted = true;
    else if (char === ',') { row.push(field); field = ''; }
    else if (char === '\n') { row.push(field.replace(/\r$/, '')); records.push(row); row = []; field = ''; }
    else field += char;
  }
  if (field || row.length) { row.push(field.replace(/\r$/, '')); records.push(row); }
  const headers = (records.shift() || []).map((h) => h.trim().replace(/^\uFEFF/, ''));
  if (!headers.includes('visit_date')) throw new Error('This CSV does not contain a visit_date column.');
  return records.filter((r) => r.some((v) => v.trim())).map((values, sourceIndex) => {
    const item = { _sourceIndex: sourceIndex };
    headers.forEach((header, index) => { item[header] = (values[index] || '').trim(); });
    return item;
  });
}

function parseClinicalDate(value) {
  let text = String(value || '').trim();
  if (!text || /^(?:n\/?a|nd|none|null|unknown|[-–—])$/i.test(text)) return null;

  // Correct common OCR substitutions only inside date-like values.
  if (/^[\dOo\s./\\-]+$/.test(text)) text = text.replace(/[Oo]/g, '0');
  text = text.replace(/[,]/g, ' ').replace(/\s+/g, ' ').trim();

  // Excel's 1900 date system (with its historical leap-year offset).
  if (/^\d{5}(?:\.0+)?$/.test(text)) {
    const serial = Number(text);
    if (serial >= 20000 && serial <= 80000) return new Date(Date.UTC(1899, 11, 30) + serial * 86400000);
  }

  const monthNames = {
    jan: 1, january: 1, feb: 2, february: 2, mar: 3, march: 3, apr: 4, april: 4,
    may: 5, jun: 6, june: 6, jul: 7, july: 7, aug: 8, august: 8,
    sep: 9, sept: 9, september: 9, oct: 10, october: 10, nov: 11, november: 11,
    dec: 12, december: 12
  };
  const makeDate = (yearValue, monthValue, dayValue) => {
    let year = Number(yearValue), month = Number(monthValue), day = Number(dayValue);
    if (year < 100) year += year <= 49 ? 2000 : 1900;
    const date = new Date(Date.UTC(year, month - 1, day));
    return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day ? date : null;
  };

  let match = text.match(/^(\d{4})[-/.\\](\d{1,2})[-/.\\](\d{1,2})$/);
  if (match) return makeDate(match[1], match[2], match[3]);

  // Data-entry form convention: day/month/year.
  match = text.match(/^(\d{1,2})[-/.\\](\d{1,2})[-/.\\](\d{2}|\d{4})$/);
  if (match) return makeDate(match[3], match[2], match[1]);

  match = text.match(/^(\d{1,2})[-/.\s]+([A-Za-z]+)[-/.\s]+(\d{2}|\d{4})$/);
  if (match && monthNames[match[2].toLowerCase()]) return makeDate(match[3], monthNames[match[2].toLowerCase()], match[1]);

  match = text.match(/^([A-Za-z]+)[-/.\s]+(\d{1,2})[-/.\s]+(\d{2}|\d{4})$/);
  if (match && monthNames[match[1].toLowerCase()]) return makeDate(match[3], monthNames[match[1].toLowerCase()], match[2]);

  // Compact DDMMYYYY, YYYYMMDD, or DDMMYY values.
  if (/^(?:19|20)\d{6}$/.test(text)) return makeDate(text.slice(0, 4), text.slice(4, 6), text.slice(6, 8));
  if (/^\d{8}$/.test(text)) return makeDate(text.slice(4, 8), text.slice(2, 4), text.slice(0, 2));
  if (/^\d{6}$/.test(text)) return makeDate(text.slice(4, 6), text.slice(2, 4), text.slice(0, 2));
  return null;
}

function formatDate(date, fallback = '—') {
  if (!date) return fallback;
  return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(date);
}

function monthsBetween(a, b) {
  return (b.getUTCFullYear() - a.getUTCFullYear()) * 12 + b.getUTCMonth() - a.getUTCMonth() + (b.getUTCDate() - a.getUTCDate()) / 30.4;
}

function meaningfulValue(value) {
  const text = String(value ?? '').trim();
  return text && !/^(?:n\/?a|nd|none|null|unknown|[-–—])$/i.test(text) ? text : '';
}

function childIdentifier(row, index = 0) {
  const directId = meaningfulValue(row.unique_child_id) || meaningfulValue(row.hcc_reg_no);
  if (directId) return directId;
  const sourceName = meaningfulValue(row.file_name);
  if (sourceName) return sourceName.replace(/_visits_export(?:\.csv)?$/i, '').replace(/\.csv$/i, '');
  return `Record ${index + 1}`;
}

function groupReviewRows(rows) {
  const groups = new Map();
  rows.forEach((row, index) => {
    const id = childIdentifier(row, index);
    const facility = meaningfulValue(row.facility) || meaningfulValue(row.facility_name) || meaningfulValue(row.health_facility) || meaningfulValue(row.clinic) || meaningfulValue(row.site) || meaningfulValue(row.site_name);
    const key = facility ? `${facility}::${id}` : id;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  });
  return groups;
}

async function selectReviewCsv() {
  const input = document.createElement('input');
  input.type = 'file'; input.accept = '.csv,text/csv';
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file) return;
    try {
      const rows = parseCsv(await file.text());
      if (!rows.length) throw new Error('The CSV has no visit records.');
      appState.reviewFileName = file.name;
      appState.reviewRows = rows;
      appState.reviewGroups = groupReviewRows(rows);
      appState.selectedChildId = appState.reviewGroups.keys().next().value;
      populateChildSelector(); renderReview(); render();
      setStatus(`Loaded ${rows.length} visit record${rows.length === 1 ? '' : 's'}`);
    } catch (error) { setStatus(`Could not load review CSV: ${error.message}`); }
  };
  input.click();
}

function facilityValue(row) {
  const keys = ['facility', 'facility_name', 'health_facility', 'clinic', 'site', 'site_name'];
  const key = keys.find((candidate) => meaningfulValue(row[candidate]));
  return key ? meaningfulValue(row[key]) : 'Facility not specified';
}

function groupCohortRows(rows) {
  const groups = new Map();
  rows.forEach((row, index) => {
    const childId = childIdentifier(row, index);
    const key = `${facilityValue(row)}::${childId}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  });
  return groups;
}

function populateFacilitySelector() {
  const facilities = [...new Set(appState.cohortRows.map(facilityValue))].sort((a, b) => a.localeCompare(b));
  els.cohortFacilitySelect.innerHTML = '<option value="__all__">All facilities</option>' + facilities.map((facility) => `<option value="${escapeHtml(facility)}">${escapeHtml(facility)}</option>`).join('');
  if (appState.selectedFacility !== '__all__' && !facilities.includes(appState.selectedFacility)) appState.selectedFacility = '__all__';
  els.cohortFacilitySelect.value = appState.selectedFacility;
}

async function selectCohortCsv() {
  const input = document.createElement('input');
  input.type = 'file'; input.accept = '.csv,text/csv';
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file) return;
    try {
      const rows = parseCsv(await file.text());
      if (!rows.length) throw new Error('The CSV has no visit records.');
      appState.cohortFileName = file.name;
      appState.cohortRows = rows;
      appState.cohortGroups = groupCohortRows(rows);
      appState.selectedFacility = '__all__';
      populateFacilitySelector(); renderCohortAnalysis(); render();
      setStatus(`Loaded cohort with ${appState.cohortGroups.size} child record${appState.cohortGroups.size === 1 ? '' : 's'}`);
    } catch (error) { setStatus(`Could not load cohort CSV: ${error.message}`); }
  };
  input.click();
}

function populateChildSelector() {
  els.reviewChildSelect.innerHTML = [...appState.reviewGroups.entries()].map(([key, rows]) => {
    const first = rows[0] || {};
    const id = childIdentifier(first);
    const nameValue = meaningfulValue(first.child_name);
    const facility = meaningfulValue(first.facility) || meaningfulValue(first.facility_name) || meaningfulValue(first.health_facility) || meaningfulValue(first.clinic) || meaningfulValue(first.site) || meaningfulValue(first.site_name);
    const name = nameValue ? ` — ${nameValue}` : '';
    const facilityLabel = facility ? `${facility} • ` : '';
    return `<option value="${escapeHtml(key)}">${escapeHtml(facilityLabel + id + name)} (${rows.length} visit${rows.length === 1 ? '' : 's'})</option>`;
  }).join('');
  els.reviewChildSelect.value = appState.selectedChildId;
  updatePatientNavigation();
}

function updatePatientNavigation() {
  const index = els.reviewChildSelect.selectedIndex;
  const count = els.reviewChildSelect.options.length;
  els.previousChildBtn.disabled = count < 2 || index <= 0;
  els.nextChildBtn.disabled = count < 2 || index < 0 || index >= count - 1;
}

function navigatePatient(offset) {
  const nextIndex = els.reviewChildSelect.selectedIndex + offset;
  if (nextIndex < 0 || nextIndex >= els.reviewChildSelect.options.length) return;
  els.reviewChildSelect.selectedIndex = nextIndex;
  appState.selectedChildId = els.reviewChildSelect.value;
  renderReview();
  updatePatientNavigation();
}

function findDateIssues(rows) {
  const issues = [];
  const add = (title, detail) => issues.push({ title, detail });
  const first = rows[0] || {};
  const birth = parseClinicalDate(first.birth_date);
  const datedSourceRows = rows.map((row) => ({ row, date: parseClinicalDate(row.visit_date) }));
  datedSourceRows.forEach(({ row, date }, index) => {
    if (row.visit_date && !date) add('Invalid visit date', `Row ${index + 1}: “${row.visit_date}” is not a valid supported date.`);
    if (birth && date && date < birth) add('Visit precedes birth', `${row.visit_date} occurs before birth date ${first.birth_date}.`);
    const next = parseClinicalDate(row.next_appointment_date);
    if (row.next_appointment_date && !next) add('Invalid appointment date', `Visit ${row.visit_date || index + 1}: “${row.next_appointment_date}” could not be interpreted.`);
    if (date && next && next < date) add('Appointment precedes visit', `Next appointment ${row.next_appointment_date} is before visit ${row.visit_date}.`);
    const recordedAge = Number(row.age_months);
    if (birth && date && date >= birth && row.age_months !== '' && Number.isFinite(recordedAge)) {
      const expected = monthsBetween(birth, date);
      if (Math.abs(recordedAge - expected) > 2) add('Age and visit date differ', `At ${row.visit_date}, recorded age is ${recordedAge} months; dates imply about ${Math.round(expected)} months.`);
    }
  });
  for (let i = 1; i < datedSourceRows.length; i += 1) {
    if (datedSourceRows[i - 1].date && datedSourceRows[i].date && datedSourceRows[i].date < datedSourceRows[i - 1].date) {
      add('Visits out of sequence', `${datedSourceRows[i].row.visit_date} appears after ${datedSourceRows[i - 1].row.visit_date} in the source, but is earlier.`);
    }
  }
  ['hiv_test_0', 'hiv_test_1', 'hiv_test_2'].forEach((prefix, index) => {
    const sampleText = first[`${prefix}_sample_date`], receivedText = first[`${prefix}_date_received`];
    const sample = parseClinicalDate(sampleText), received = parseClinicalDate(receivedText);
    if (sampleText && !sample) add(`Invalid HIV test ${index + 1} sample date`, `“${sampleText}” could not be interpreted.`);
    if (receivedText && !received) add(`Invalid HIV test ${index + 1} result date`, `“${receivedText}” could not be interpreted.`);
    if (sample && received && received < sample) add(`HIV test ${index + 1} result precedes sample`, `Result date ${receivedText} is before sample date ${sampleText}.`);
  });
  return issues;
}

function renderWeightChart(rows) {
  const dated = rows.map((row) => {
    const cptMatch = String(row.cpt || '').match(/-?\d+(?:\.\d+)?/);
    return { date: parseClinicalDate(row.visit_date), weight: Number(row.weight_kg), cpt: cptMatch ? Number(cptMatch[0]) : NaN, cptRaw: row.cpt };
  }).filter((p) => p.date).sort((a, b) => a.date - b.date);
  const points = dated.filter((p) => Number.isFinite(p.weight) && p.weight > 0);
  const cptPoints = dated.filter((p) => Number.isFinite(p.cpt));
  const visitTests = reconcileVisitTests(rows).map((item) => ({ ...item, date: parseClinicalDate(item.visit.visit_date) })).filter((item) => item.date);
  if (!points.length && !cptPoints.length && !visitTests.length) { els.weightChart.innerHTML = '<div class="chart-empty">No dated weight, numeric CPT, or HIV test events are available for this child.</div>'; return; }
  const width = 720, height = 300, left = 48, right = 52, top = 34, bottom = 48;
  const allDates = [...points, ...cptPoints, ...visitTests].sort((a, b) => a.date - b.date);
  const firstTime = allDates[0].date.getTime(), lastTime = allDates.at(-1).date.getTime();
  const x = (p) => firstTime === lastTime ? (left + width - right) / 2 : left + ((p.date.getTime() - firstTime) / (lastTime - firstTime)) * (width - left - right);
  const weights = points.map((p) => p.weight);
  const minW = points.length ? Math.min(...weights) : 0, maxW = points.length ? Math.max(...weights) : 1;
  const pad = Math.max((maxW - minW) * .2, .5), yMin = Math.max(0, minW - pad), yMax = maxW + pad;
  const y = (p) => top + (1 - (p.weight - yMin) / (yMax - yMin)) * (height - top - bottom);
  const cptValues = cptPoints.map((p) => p.cpt);
  const cptMinValue = cptPoints.length ? Math.min(...cptValues) : 0, cptMaxValue = cptPoints.length ? Math.max(...cptValues) : 1;
  const cptPad = Math.max((cptMaxValue - cptMinValue) * .15, cptMaxValue === cptMinValue ? Math.max(Math.abs(cptMaxValue) * .1, 1) : .25);
  const cptMin = cptMinValue - cptPad, cptMax = cptMaxValue + cptPad;
  const cptY = (p) => top + (1 - (p.cpt - cptMin) / (cptMax - cptMin)) * (height - top - bottom);
  const ticks = [0, .25, .5, .75, 1];
  const grid = ticks.map((t) => { const yy = top + t * (height - top - bottom); const weightValue = yMax - t * (yMax - yMin); const cptValue = cptMax - t * (cptMax - cptMin); return `<line class="chart-grid" x1="${left}" y1="${yy}" x2="${width - right}" y2="${yy}"/>${points.length ? `<text class="chart-label" x="${left - 8}" y="${yy + 4}" text-anchor="end">${weightValue.toFixed(1)}</text>` : ''}${cptPoints.length ? `<text class="chart-label chart-axis-cpt" x="${width - right + 8}" y="${yy + 4}">${cptValue.toFixed(1)}</text>` : ''}`; }).join('');
  const line = points.map((p, i) => `${i ? 'L' : 'M'} ${x(p)} ${y(p)}`).join(' ');
  const dots = points.map((p) => `<circle class="chart-dot" cx="${x(p)}" cy="${y(p)}" r="5"><title>${formatDate(p.date)}: ${p.weight} kg</title></circle><text class="chart-value" x="${x(p)}" y="${y(p) - 11}" text-anchor="middle">${p.weight}</text>`).join('');
  const cptLine = cptPoints.map((p, i) => `${i ? 'L' : 'M'} ${x(p)} ${cptY(p)}`).join(' ');
  const cptDots = cptPoints.map((p, i) => {
    const previous = cptPoints[i - 1];
    const direction = previous ? Math.sign(p.cpt - previous.cpt) : 0;
    const marker = direction > 0 ? `<text class="chart-change-up" x="${x(p)}" y="${cptY(p) - 13}" text-anchor="middle">▲ ${p.cpt}</text>` : direction < 0 ? `<text class="chart-change-down" x="${x(p)}" y="${cptY(p) + 20}" text-anchor="middle">▼ ${p.cpt}</text>` : `<text class="chart-value chart-axis-cpt" x="${x(p)}" y="${cptY(p) - 11}" text-anchor="middle">${p.cpt}</text>`;
    return `<circle class="cpt-dot" cx="${x(p)}" cy="${cptY(p)}" r="5"><title>${formatDate(p.date)}: CPT ${escapeHtml(p.cptRaw)}${direction > 0 ? ' (increase)' : direction < 0 ? ' (decrease)' : ''}</title></circle>${marker}`;
  }).join('');
  const testMarkers = visitTests.map((item) => {
    const result = item.test?.result || '';
    const positive = /pos|reactive|detect/i.test(result) && !/neg|non.?reactive|not.?detect/i.test(result);
    const markerY = top + 9;
    const markerClass = positive ? 'test-event-marker test-event-positive' : 'test-event-marker';
    const labelClass = positive ? 'test-event-label test-event-label-positive' : 'test-event-label';
    const resultLabel = result || 'result not recorded';
    return `<line class="test-event-line" x1="${x(item)}" y1="${markerY + 7}" x2="${x(item)}" y2="${height - bottom}"/><rect class="${markerClass}" x="${x(item) - 5}" y="${markerY - 5}" width="10" height="10" transform="rotate(45 ${x(item)} ${markerY})"><title>${formatDate(item.date)}: ${item.visit.hiv_testing} test — ${escapeHtml(resultLabel)}</title></rect><text class="${labelClass}" x="${x(item)}" y="${markerY + 23}" text-anchor="middle">${escapeHtml(item.visit.hiv_testing)}</text>`;
  }).join('');
  const dateLabels = allDates.filter((p, i, values) => i === 0 || p.date.getTime() !== values[i - 1].date.getTime()).map((p) => `<text class="chart-label" x="${x(p)}" y="${height - 20}" text-anchor="middle">${formatDate(p.date).replace(/ \d{4}$/, '')}</text>`).join('');
  els.weightChart.innerHTML = `<div class="chart-legend">${points.length ? '<span class="legend-key">Weight (kg)</span>' : ''}${cptPoints.length ? '<span class="legend-key cpt">CPT (ml/tabs)</span><span class="legend-rise">▲ increase</span><span class="legend-fall">▼ decrease</span>' : ''}${visitTests.length ? '<span class="legend-test">◆ HIV test</span><span class="legend-test-positive">◆ positive result</span>' : ''}</div><svg class="weight-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Weight, CPT, and HIV tests over visit dates">${grid}${points.length ? '<text class="chart-label" x="12" y="20">kg</text>' : ''}${cptPoints.length ? `<text class="chart-label chart-axis-cpt" x="${width - 30}" y="20">CPT</text>` : ''}<path class="chart-line" d="${line}"/><path class="cpt-line" d="${cptLine}"/>${testMarkers}${dots}${cptDots}${dateLabels}</svg>`;
}

function tags(values) {
  const present = values.filter(([, value]) => value && value !== 'No' && value !== '0');
  return present.length ? present.map(([label, value]) => `<span class="clinical-tag">${escapeHtml(label)}: ${escapeHtml(value)}</span>`).join('') : '<span class="cell-muted">Not recorded</span>';
}

function sameClinicalDate(a, b) {
  const first = parseClinicalDate(a), second = parseClinicalDate(b);
  return Boolean(first && second && first.getTime() === second.getTime());
}

function normalizeTestType(value) {
  return String(value || '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
}

function getHivTestRecords(row) {
  return [0, 1, 2, 3].map((index) => ({
    number: index + 1,
    sampleDate: row[`hiv_test_${index}_sample_date`] || '',
    type: row[`hiv_test_${index}_type`] || '',
    sampleId: row[`hiv_test_${index}_sample_id`] || '',
    result: row[`hiv_test_${index}_result`] || '',
    receivedDate: row[`hiv_test_${index}_date_received`] || ''
  })).filter((test) => test.sampleDate || test.type || test.sampleId || test.result || test.receivedDate);
}

function reconcileVisitTests(rows) {
  const tests = getHivTestRecords(rows[0] || {});
  return rows.filter((row) => {
    const type = normalizeTestType(row.hiv_testing);
    return Boolean(type) && !['NO','NONE','N','ND','NOTDONE','NOTPERFORMED','NA','NULL','UNKNOWN','0'].includes(type);
  }).map((visit) => {
    const visitType = normalizeTestType(visit.hiv_testing);
    const exact = tests.find((test) => normalizeTestType(test.type) === visitType && sameClinicalDate(test.sampleDate, visit.visit_date));
    if (exact) return { visit, test: exact, status: 'exact', assessment: 'Date and test type match' };
    const dateMatch = tests.find((test) => sameClinicalDate(test.sampleDate, visit.visit_date));
    if (dateMatch) return { visit, test: dateMatch, status: 'partial', assessment: `Date matches, but record type is ${dateMatch.type || 'missing'}` };
    const typeMatch = tests.find((test) => normalizeTestType(test.type) === visitType);
    if (typeMatch) return { visit, test: typeMatch, status: 'partial', assessment: `Type matches, but sample date is ${typeMatch.sampleDate || 'missing'}` };
    return { visit, test: null, status: 'missing', assessment: 'No testing-record entry matches this visit' };
  });
}

function renderTestAnalysis(rows) {
  const matches = reconcileVisitTests(rows);
  const exactCount = matches.filter((item) => item.status === 'exact').length;
  const reviewCount = matches.length - exactCount;
  els.testMatchSummary.innerHTML = matches.length ? `<span class="summary-chip">${matches.length} visit test${matches.length === 1 ? '' : 's'}</span><span class="summary-chip matched">${exactCount} matched</span>${reviewCount ? `<span class="summary-chip review">${reviewCount} to review</span>` : ''}` : '';
  els.testAnalysisEmpty.hidden = Boolean(matches.length);
  els.testAnalysisTableWrap.hidden = !matches.length;
  els.testAnalysisBody.innerHTML = matches.map(({ visit, test, status, assessment }) => {
    const resultText = test?.result || 'Not recorded';
    const resultClass = /pos|reactive|detect/i.test(resultText) ? 'positive' : /neg|non.?reactive|not.?detect/i.test(resultText) ? 'negative' : '';
    const badgeText = status === 'exact' ? 'Matched' : status === 'partial' ? 'Partial match' : 'No match';
    return `<tr><td><div class="cell-primary">${escapeHtml(visit.hiv_testing)}</div><div class="cell-muted">${escapeHtml(formatDate(parseClinicalDate(visit.visit_date), visit.visit_date || 'Undated visit'))}</div></td><td>${test ? `<div class="cell-primary">${escapeHtml(test.type || 'Type missing')}</div><div class="cell-muted">Sampled ${escapeHtml(formatDate(parseClinicalDate(test.sampleDate), test.sampleDate || 'date missing'))}</div>` : '<span class="cell-muted">No matching record</span>'}</td><td>${escapeHtml(test?.sampleId || '—')}</td><td><span class="test-result ${resultClass}">${escapeHtml(resultText)}</span></td><td>${escapeHtml(formatDate(parseClinicalDate(test?.receivedDate), test?.receivedDate || '—'))}</td><td><span class="match-badge match-${status}">${badgeText}</span><div class="cell-muted">${escapeHtml(assessment)}</div></td></tr>`;
  }).join('');
}

function classifyFollowUp(value) {
  const code = String(value || '').trim().toUpperCase().replace(/[^A-Z]/g, '');
  if (['CON', 'CONT', 'CONTINUE', 'CONTINUED'].includes(code)) return 'retained';
  if (['DIS', 'DEF', 'D', 'DISCONTINUED', 'DEFAULTED', 'DEAD'].includes(code)) return 'unfavourable';
  return 'other';
}

function latestFollowUp(rows) {
  const candidates = rows.filter((row) => String(row.follow_up || '').trim()).sort((a, b) => {
    const first = parseClinicalDate(a.visit_date)?.getTime() ?? -Infinity;
    const second = parseClinicalDate(b.visit_date)?.getTime() ?? -Infinity;
    return first - second || a._sourceIndex - b._sourceIndex;
  });
  return candidates.at(-1)?.follow_up || '';
}

function formatFollowUpOutcome(value) {
  const raw = meaningfulValue(value);
  if (!raw) return 'Not recorded';
  const labels = { CON: 'Continued', DIS: 'Discontinued', ART: 'Started ART', TO: 'Transferred out', DEF: 'Defaulted', D: 'Died' };
  const code = raw.toUpperCase().replace(/[^A-Z]/g, '');
  return labels[code] ? `${raw} — ${labels[code]}` : raw;
}

function percent(numerator, denominator) {
  return denominator ? `${Math.round((numerator / denominator) * 100)}%` : '—';
}

function renderScheduleAnalysis(childGroups) {
  const children = [...childGroups.entries()].map(([id, rows]) => {
    const outcome = latestFollowUp(rows);
    return { id, consistent: findDateIssues(rows).length === 0, outcome, classification: classifyFollowUp(outcome) };
  });
  const groups = {
    consistent: { retained: 0, unfavourable: 0, other: 0, total: 0 },
    issues: { retained: 0, unfavourable: 0, other: 0, total: 0 }
  };
  children.forEach((child) => {
    const group = child.consistent ? groups.consistent : groups.issues;
    group[child.classification] += 1; group.total += 1;
  });
  const classifiable = groups.consistent.retained + groups.consistent.unfavourable + groups.issues.retained + groups.issues.unfavourable;
  els.scheduleAnalysedCount.textContent = `${classifiable} / ${children.length}`;
  els.consistentRetentionRate.textContent = percent(groups.consistent.retained, groups.consistent.retained + groups.consistent.unfavourable);
  els.issueRetentionRate.textContent = percent(groups.issues.retained, groups.issues.retained + groups.issues.unfavourable);

  const rawCells = [groups.consistent.retained, groups.consistent.unfavourable, groups.issues.retained, groups.issues.unfavourable];
  const corrected = rawCells.some((value) => value === 0);
  const [a, b, c, d] = corrected ? rawCells.map((value) => value + 0.5) : rawCells;
  const canEstimate = classifiable > 0 && (groups.consistent.retained + groups.consistent.unfavourable) > 0 && (groups.issues.retained + groups.issues.unfavourable) > 0;
  let oddsRatio = null, lower = null, upper = null;
  if (canEstimate) {
    oddsRatio = (a * d) / (b * c);
    const standardError = Math.sqrt(1 / a + 1 / b + 1 / c + 1 / d);
    lower = Math.exp(Math.log(oddsRatio) - 1.96 * standardError);
    upper = Math.exp(Math.log(oddsRatio) + 1.96 * standardError);
  }
  els.scheduleOddsRatio.textContent = canEstimate ? `${oddsRatio.toFixed(2)} (${lower.toFixed(2)}–${upper.toFixed(2)})${corrected ? '*' : ''}` : 'Not estimable';
  els.scheduleAnalysisBody.innerHTML = [
    ['No date discrepancies', groups.consistent],
    ['One or more date issues', groups.issues]
  ].map(([label, group]) => `<tr><td class="cell-primary">${label}</td><td>${group.retained}</td><td>${group.unfavourable}</td><td>${group.other}</td><td>${group.total}</td></tr>`).join('');

  let badge = 'Insufficient data', badgeClass = 'status-warning', summary = 'Load a merged cohort CSV containing children in both schedule groups with classifiable follow-up outcomes to estimate the association.';
  let calloutClass = '';
  if (canEstimate) {
    const imprecise = lower <= 1 && upper >= 1;
    if (classifiable < 20) {
      badge = 'Exploratory only';
      summary = `The current estimate uses only ${classifiable} classifiable children, so it is too small for a dependable prediction. The observed odds ratio is ${oddsRatio.toFixed(2)}.`;
    } else if (imprecise) {
      badge = 'No clear evidence';
      summary = `The estimated odds ratio is ${oddsRatio.toFixed(2)}, but its 95% confidence interval includes 1. This dataset does not show clear evidence that date consistency predicts retention.`;
    } else if (oddsRatio > 1) {
      badge = 'Positive association'; badgeClass = 'status-ok'; calloutClass = 'positive-signal';
      summary = `Children with no date discrepancies had approximately ${oddsRatio.toFixed(2)} times the odds of a retained outcome compared with children who had date issues.`;
    } else {
      badge = 'Inverse association'; calloutClass = 'negative-signal';
      summary = `Children with no date discrepancies had approximately ${oddsRatio.toFixed(2)} times the odds of a retained outcome; the observed association is opposite to the proposed prediction.`;
    }
  }
  els.scheduleEvidenceBadge.textContent = badge;
  els.scheduleEvidenceBadge.className = `status-badge ${badgeClass}`;
  els.scheduleAnalysisSummary.className = `analysis-callout ${calloutClass}`.trim();
  els.scheduleAnalysisSummary.textContent = summary + (corrected && canEstimate ? ' *A 0.5 correction was applied because at least one comparison cell was zero.' : '');
}

function renderCohortAnalysis() {
  const hasRows = Boolean(appState.cohortRows.length);
  els.cohortEmpty.hidden = hasRows;
  els.cohortContent.hidden = !hasRows;
  if (!hasRows) return;
  const filteredRows = appState.selectedFacility === '__all__' ? appState.cohortRows : appState.cohortRows.filter((row) => facilityValue(row) === appState.selectedFacility);
  const groups = groupCohortRows(filteredRows);
  const facilities = new Set(filteredRows.map(facilityValue));
  els.cohortSubtitle.textContent = `${appState.cohortFileName} • ${groups.size} children • ${facilities.size} facilit${facilities.size === 1 ? 'y' : 'ies'}`;
  els.cohortMeta.innerHTML = tags([['Selected', appState.selectedFacility === '__all__' ? 'All facilities' : appState.selectedFacility], ['Visits', filteredRows.length], ['Children', groups.size]]);
  renderScheduleAnalysis(groups);
}

function renderReview() {
  const rows = appState.reviewGroups.get(appState.selectedChildId) || [];
  els.reviewEmpty.hidden = Boolean(rows.length); els.reviewContent.hidden = !rows.length;
  if (!rows.length) return;
  const sorted = [...rows].sort((a, b) => (parseClinicalDate(a.visit_date)?.getTime() ?? Infinity) - (parseClinicalDate(b.visit_date)?.getTime() ?? Infinity));
  const first = rows[0], issues = findDateIssues(rows);
  const latestDated = [...sorted].reverse().find((r) => parseClinicalDate(r.visit_date));
  const latestWeightRow = [...sorted].reverse().find((r) => Number(r.weight_kg) > 0);
  const outcome = latestFollowUp(rows);
  els.reviewSubtitle.textContent = `${appState.reviewFileName} • ${appState.reviewGroups.size} child record${appState.reviewGroups.size === 1 ? '' : 's'}`;
  const patientFacility = meaningfulValue(first.facility) || meaningfulValue(first.facility_name) || meaningfulValue(first.health_facility) || meaningfulValue(first.clinic) || meaningfulValue(first.site) || meaningfulValue(first.site_name);
  els.reviewPatientMeta.innerHTML = tags([['ID', childIdentifier(first)], ['Facility', patientFacility], ['Name', meaningfulValue(first.child_name)], ['Sex', meaningfulValue(first.sex)], ['HCC', meaningfulValue(first.hcc_reg_no)], ['Birth date', meaningfulValue(first.birth_date)], ['Outcome', formatFollowUpOutcome(outcome)]]);
  updatePatientNavigation();
  els.reviewVisitCount.textContent = rows.length; els.reviewIssueCount.textContent = issues.length;
  els.reviewLatestWeight.textContent = latestWeightRow ? `${latestWeightRow.weight_kg} kg` : '—';
  els.reviewLatestVisit.textContent = latestDated ? formatDate(parseClinicalDate(latestDated.visit_date)) : '—';
  els.dateStatusBadge.textContent = issues.length ? `${issues.length} to check` : 'Dates consistent';
  els.dateStatusBadge.className = `status-badge ${issues.length ? 'status-warning' : 'status-ok'}`;
  els.dateIssues.innerHTML = issues.length ? issues.map((issue) => `<div class="issue-item"><div class="issue-title">${escapeHtml(issue.title)}</div><div class="issue-detail">${escapeHtml(issue.detail)}</div></div>`).join('') : '<div class="issue-item issue-ok"><div class="issue-title">No discrepancies detected</div><div class="issue-detail">The captured dates pass the current chronological checks.</div></div>';
  renderWeightChart(sorted);
  renderTestAnalysis(sorted);
  els.reviewHistoryBody.innerHTML = sorted.map((row) => `<tr><td><div class="cell-primary">${escapeHtml(formatDate(parseClinicalDate(row.visit_date), row.visit_date || 'Undated'))}</div><div class="cell-muted">Age ${escapeHtml(row.age_months || '—')} months</div></td><td>${tags([['Weight', row.weight_kg && `${row.weight_kg} kg`], ['Height', row.height_cm && `${row.height_cm} cm`], ['MUAC', row.muac_cm && `${row.muac_cm} cm`]])}</td><td>${tags([['Wasting', row.wasting_malnutrition], ['Breastfeeding', row.breastfeeding], ['Abdominal exam', row.abdominal_exam]])}</td><td>${tags([['Testing', row.hiv_testing], ['Infection', row.hiv_infection], ['Mother', row.mother_status]])}</td><td>${tags([['CPT', row.cpt], ['Follow-up', row.follow_up]])}</td><td>${escapeHtml(formatDate(parseClinicalDate(row.next_appointment_date), row.next_appointment_date || '—'))}</td></tr>`).join('');
}

async function selectWorkingDirectory() {
  if (!window.showDirectoryPicker) {
    setStatus('This browser does not support direct folder access. Use Chrome or Edge, or rely on normal downloads.');
    return;
  }
  try {
    const handle = await window.showDirectoryPicker({ mode: 'readwrite' });
    appState.folderHandle = handle;
    appState.folderName = handle.name;
    render();
    setStatus('Working directory selected');
  } catch (error) {
    if (error?.name !== 'AbortError') setStatus(`Could not select folder: ${error.message}`);
  }
}

async function selectPdfFile() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'application/pdf';
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file) return;
    appState.pdfFile = file;
    appState.sampleName = null;
    appState.pdfFileName = file.name;
    appState.pdfDoc = null;
    resetVerificationPages();
    appState.rotations.page1 = 0;
    appState.rotations.page2 = 0;
    render();
    setStatus('PDF selected');
  };
  input.click();
}

async function ensurePdfLoaded() {
  if (appState.pdfDoc) return appState.pdfDoc;
  if (!appState.pdfFile) throw new Error('No PDF selected');
  if (!pdfjsLib) throw new Error('PDF library not loaded');
  const data = new Uint8Array(await appState.pdfFile.arrayBuffer());
  appState.pdfDoc = await pdfjsLib.getDocument({ data }).promise;
  return appState.pdfDoc;
}

async function renderPageToCanvas(pageNumber, canvas, rotation) {
  const pdfDoc = await ensurePdfLoaded();
  const page = await pdfDoc.getPage(pageNumber);
  const viewport = page.getViewport({ scale: appState.scale, rotation });
  const ctx = canvas.getContext('2d');
  canvas.width = viewport.width;
  canvas.height = viewport.height;
  await page.render({ canvasContext: ctx, viewport }).promise;
  document.getElementById(`verifyPage${pageNumber}Btn`).disabled = false;
}

async function refreshPreviews() {
  try {
    const pdfDoc = await ensurePdfLoaded();
    if (pdfDoc.numPages < 2) {
      setStatus('The selected PDF has fewer than 2 pages');
    }
    await renderPageToCanvas(1, els.page1Canvas, appState.rotations.page1);
    if (pdfDoc.numPages >= 2) {
      await renderPageToCanvas(2, els.page2Canvas, appState.rotations.page2);
    }
    render();
    setStatus('PDF preview loaded');
  } catch (error) {
    setStatus(`Could not load PDF preview: ${error.message}`);
  }
}

function fallbackDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

async function saveBlob(blob, filename) {
  if (appState.folderHandle) {
    const fileHandle = await appState.folderHandle.getFileHandle(filename, { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(blob);
    await writable.close();
    return true;
  }
  fallbackDownload(blob, filename);
  return false;
}

function canvasToBlob(canvas, mimeType, quality = 0.95) {
  return new Promise((resolve) => canvas.toBlob(resolve, mimeType, quality));
}

async function createPageImages() {
  if (!appState.pdfFile) {
    setStatus('Select a PDF first');
    return;
  }
  try {
    await refreshPreviews();
    const ext = appState.outputFormat;
    const mimeType = ext === 'jpg' ? 'image/jpeg' : 'image/png';
    const blob1 = await canvasToBlob(els.page1Canvas, mimeType);
    const blob2 = await canvasToBlob(els.page2Canvas, mimeType);
    const name1 = `page1.${ext}`;
    const name2 = `page2.${ext}`;
    await saveBlob(blob1, name1);
    await saveBlob(blob2, name2);
    appState.savedImages = [name1, name2];
    render();
    setStatus(appState.folderHandle ? 'Page images saved to the working folder' : 'Page images downloaded');
  } catch (error) {
    setStatus(`Could not create page images: ${error.message}`);
  }
}

function updateRotation(pageKey, delta) {
  appState.rotations[pageKey] = normalizeRotation(appState.rotations[pageKey] + delta);
  refreshPreviews();
}

function resetRotation(pageKey) {
  appState.rotations[pageKey] = 0;
  refreshPreviews();
}

function setEmbeddedStatus(text) {
  const doc = els.pinkFormFrame.contentDocument;
  const statusEl = doc?.getElementById('statusMsg');
  if (statusEl) statusEl.textContent = text;
}

async function writeTextFile(filename, text) {
  const blob = new Blob([text], { type: 'text/csv;charset=utf-8' });
  const usedFolder = await saveBlob(blob, filename);
  return usedFolder;
}

function wireOriginalFormExport() {
  const frameWindow = els.pinkFormFrame.contentWindow;
  const frameDocument = els.pinkFormFrame.contentDocument;
  if (!frameWindow || !frameDocument) return;

  const exportBtn = frameDocument.getElementById('exportBtn');
  if (!exportBtn) return;

  const originalClearForm = typeof frameWindow.clearForm === 'function' ? frameWindow.clearForm.bind(frameWindow) : null;
  const newBtn = exportBtn.cloneNode(true);
  exportBtn.replaceWith(newBtn);

  newBtn.addEventListener('click', async () => {
    try {
      setEmbeddedStatus('Preparing export…');
      if (typeof frameWindow.collectHeaderData !== 'function' || typeof frameWindow.collectVisitRows !== 'function') {
        throw new Error('Form export helpers are not available');
      }

      const header = frameWindow.collectHeaderData();
      const visits = frameWindow.collectVisitRows();
      if (!visits.length) {
        setEmbeddedStatus('No rows exported: please fill at least one Visit Date.');
        return;
      }

      const columns = [
        'unique_child_id','hcc_reg_no','transfer_in_date','birth_cohort_month','birth_cohort_year',
        'child_name','guardian_name','physical_address','sex','child_age','agrees_to_fup','guardian_relation','guardian_phone',
        'mother_status_enrolment','art_reg_no','art_start_date','age_at_enrolment','nvp_start_date','nvp_duration',
        'hiv_test_0_sample_date','hiv_test_0_type','hiv_test_0_sample_id','hiv_test_0_result','hiv_test_0_date_received',
        'hiv_test_1_sample_date','hiv_test_1_type','hiv_test_1_sample_id','hiv_test_1_result','hiv_test_1_date_received',
        'hiv_test_2_sample_date','hiv_test_2_type','hiv_test_2_sample_id','hiv_test_2_result','hiv_test_2_date_received',
        'birth_date','birth_weight_kg',
        'age_months','visit_date','height_cm','weight_kg','muac_cm',
        'wasting_malnutrition','breastfeeding','stopped_lt6m','stopped_ge6m',
        'mother_status','abdominal_exam','hiv_testing','hiv_infection',
        'cpt','follow_up','next_appointment_date'
      ];

      const lines = [];
      lines.push(columns.map(frameWindow.csvEscape).join(','));
      visits.forEach((v) => {
        const record = { ...header, ...v };
        lines.push(columns.map((c) => frameWindow.csvEscape(record[c])).join(','));
      });
      const csv = lines.join('\n');
      const safeId = (header.unique_child_id || 'pinkcard').replace(/[^a-z0-9_-]/gi, '_');
      const filename = `${safeId}_visits_export.csv`;
      const savedToFolder = await writeTextFile(filename, csv);
      appState.reviewFileName = filename;
      appState.reviewRows = parseCsv(csv);
      appState.reviewGroups = groupReviewRows(appState.reviewRows);
      appState.selectedChildId = appState.reviewGroups.keys().next().value;
      populateChildSelector();
      renderReview();
      render();
      setEmbeddedStatus(savedToFolder ? `Exported to working folder as ${filename}` : `Downloaded ${filename}`);
      if (originalClearForm) originalClearForm();
    } catch (error) {
      setEmbeddedStatus(`Could not export CSV: ${error.message}`);
    }
  });
}

els.selectFolderBtn.addEventListener('click', selectWorkingDirectory);
els.selectPdfBtn.addEventListener('click', selectPdfFile);
els.outputFormat.addEventListener('change', () => { appState.outputFormat = els.outputFormat.value; });
els.scaleSelect.addEventListener('change', () => { appState.scale = Number(els.scaleSelect.value); if (appState.pdfFile) refreshPreviews(); });
els.openPdfWorkspaceBtn.addEventListener('click', async () => { showSection(els.pdfSection); await refreshPreviews(); });
els.openFormBtn.addEventListener('click', () => showSection(els.formSection));
document.getElementById('selectReviewCsvBtn').addEventListener('click', selectReviewCsv);
document.getElementById('changeReviewCsvBtn').addEventListener('click', selectReviewCsv);
els.openReviewBtn.addEventListener('click', () => { renderReview(); showSection(els.reviewSection); });
document.getElementById('backHomeFromReviewBtn').addEventListener('click', () => showSection(els.homeSection));
els.reviewChildSelect.addEventListener('change', () => { appState.selectedChildId = els.reviewChildSelect.value; renderReview(); });
els.previousChildBtn.addEventListener('click', () => navigatePatient(-1));
els.nextChildBtn.addEventListener('click', () => navigatePatient(1));
document.getElementById('selectCohortCsvBtn').addEventListener('click', selectCohortCsv);
document.getElementById('changeCohortCsvBtn').addEventListener('click', selectCohortCsv);
els.openCohortBtn.addEventListener('click', () => { renderCohortAnalysis(); showSection(els.cohortSection); });
document.getElementById('backHomeFromCohortBtn').addEventListener('click', () => showSection(els.homeSection));
els.cohortFacilitySelect.addEventListener('change', () => { appState.selectedFacility = els.cohortFacilitySelect.value; renderCohortAnalysis(); });
document.getElementById('backHomeFromPdfBtn').addEventListener('click', () => showSection(els.homeSection));
document.getElementById('continueToFormBtn').addEventListener('click', () => showSection(els.formSection));
document.getElementById('backHomeFromFormBtn').addEventListener('click', () => showSection(els.homeSection));
document.getElementById('createImagesBtn').addEventListener('click', createPageImages);
document.getElementById('page1LeftBtn').addEventListener('click', () => updateRotation('page1', -90));
document.getElementById('page1RightBtn').addEventListener('click', () => updateRotation('page1', 90));
document.getElementById('page1ResetBtn').addEventListener('click', () => resetRotation('page1'));
document.getElementById('page2LeftBtn').addEventListener('click', () => updateRotation('page2', -90));
document.getElementById('page2RightBtn').addEventListener('click', () => updateRotation('page2', 90));
document.getElementById('page2ResetBtn').addEventListener('click', () => resetRotation('page2'));
els.pinkFormFrame.addEventListener('load', wireOriginalFormExport);

render();
setStatus('Ready');

document.getElementById('loadSampleBtn').addEventListener('click', async () => {
  const button = document.getElementById('loadSampleBtn');
  const filename = document.getElementById('samplePdfSelect').value;
  button.disabled = true;
  try {
    setStatus('Loading sample PDF…');
    const response = await fetch(`./samples/${encodeURIComponent(filename)}`);
    if (!response.ok) throw new Error('Sample PDF could not be loaded.');
    appState.pdfFile = new File([await response.blob()], filename, {type:'application/pdf'});
    appState.pdfFileName = filename;
    appState.sampleName = filename;
    appState.pdfDoc = null;
    resetVerificationPages();
    appState.rotations = {page1:0,page2:0};
    appState.savedImages = [];
    showSection(els.pdfSection);
    await refreshPreviews();
  } catch(error) { setStatus(error.message); }
  finally { button.disabled = false; }
});

const aiPanel = document.createElement('section');
const formReviewDialog = document.getElementById('formReviewDialog');
let savedReviewState;
document.getElementById('reviewCurrentFormBtn').onclick = () => {
  const frame = els.pinkFormFrame.contentWindow;
  const header = frame.collectHeaderData();
  // Read all populated rows, including incomplete ones omitted by CSV export.
  const rows = [...frame.document.querySelectorAll('#visitsBody tr')].map((tr,index) => {
    const row = {...header, _sourceIndex:index};
    tr.querySelectorAll('[data-field]').forEach(el => {
      row[el.dataset.field] = el.matches('input,select,textarea') ? el.value.trim() : (el.dataset.value || '');
    });
    return row;
  }).filter(row => Object.keys(row).some(key => !(key in header) && key !== '_sourceIndex' && row[key]));
  const missingDates = rows.filter(row => !meaningfulValue(row.visit_date)).length;
  savedReviewState = {
    reviewFileName:appState.reviewFileName, reviewRows:appState.reviewRows,
    reviewGroups:appState.reviewGroups, selectedChildId:appState.selectedChildId
  };
  appState.reviewFileName = 'Unsaved form entries';
  appState.reviewRows = rows;
  appState.reviewGroups = new Map([['current-form',rows]]);
  appState.selectedChildId = 'current-form';
  populateChildSelector();
  document.getElementById('formReviewHost').append(els.reviewContent);
  renderReview();
  document.getElementById('formReviewNotice').textContent = !rows.length ? 'No populated visit rows to analyse yet.' : `${rows.length} populated visit rows analysed.${missingDates ? ` ${missingDates} rows have missing visit dates and cannot be positioned on the chart.` : ''} Unrecognised or impossible dates remain flagged rather than guessed.`;
  // Patient navigation belongs to the loaded CSV, not this single-form review.
  els.reviewChildSelect.closest('.review-toolbar').hidden = true;
  formReviewDialog.showModal();
};
document.getElementById('closeFormReviewBtn').onclick = () => formReviewDialog.close();
formReviewDialog.addEventListener('close', () => {
  els.reviewChildSelect.closest('.review-toolbar').hidden = false;
  els.reviewSection.append(els.reviewContent);
  if(savedReviewState) Object.assign(appState,savedReviewState);
  savedReviewState = null;
  populateChildSelector();renderReview();render();
});
let verificationPage = 1;
let verificationZoom = 100;
let verificationUrl;
const verifyDialog = document.getElementById('pageVerifyDialog');
function resetVerificationPages() {
  [1,2].forEach(page => { document.getElementById(`verifyPage${page}Btn`).disabled = true; });
}
async function openVerificationPage(page) {
  if (document.getElementById(`verifyPage${page}Btn`).disabled) return;
  verificationPage = page;
  const canvas = page === 1 ? els.page1Canvas : els.page2Canvas;
  const blob = await canvasToBlob(canvas, 'image/png');
  if (!blob) return;
  if (verificationUrl) URL.revokeObjectURL(verificationUrl);
  verificationUrl = URL.createObjectURL(blob);
  document.getElementById('verifyPageImage').src = verificationUrl;
  document.getElementById('pageVerifyTitle').textContent = `${appState.pdfFileName} — Page ${page}`;
  document.getElementById('verifySwitchBtn').disabled = document.getElementById(`verifyPage${page === 1 ? 2 : 1}Btn`).disabled;
  verificationZoom = 100;
  document.getElementById('verifyPageImage').style.width = '100%';
  if (!verifyDialog.open) verifyDialog.showModal();
  document.querySelector('.verify-image-scroll').scrollTo(0,0);
}
[1,2].forEach(page => { document.getElementById(`verifyPage${page}Btn`).onclick = () => openVerificationPage(page); });
document.getElementById('verifyCloseBtn').onclick = () => verifyDialog.close();
document.getElementById('verifySwitchBtn').onclick = () => openVerificationPage(verificationPage === 1 ? 2 : 1);
function zoomVerification(change) {
  verificationZoom = Math.max(50, Math.min(400, verificationZoom + change));
  document.getElementById('verifyPageImage').style.width = `${verificationZoom}%`;
}
document.getElementById('verifyZoomInBtn').onclick = () => zoomVerification(25);
document.getElementById('verifyZoomOutBtn').onclick = () => zoomVerification(-25);
verifyDialog.addEventListener('close', () => {
  document.getElementById('verifyPageImage').removeAttribute('src');
  if (verificationUrl) URL.revokeObjectURL(verificationUrl);
  verificationUrl = null;
});
aiPanel.className = 'card';
aiPanel.innerHTML = '<h2>Extract card data</h2><p>Enter an access code for live GPT extraction. Without a valid code, bundled samples use saved results.</p><label for="extractionAccessCode">Access code (optional)</label><input id="extractionAccessCode" type="password" autocomplete="off" maxlength="256"><button id="extractAi" class="btn btn-primary">Get results</button><p id="aiStatus" role="status"></p><pre id="aiJson" style="max-height:300px;overflow:auto;white-space:pre-wrap"></pre><button id="aiCsv" class="btn btn-secondary" disabled>Save CSV</button> <button id="aiEdit" class="btn btn-primary" disabled>Open in editable form</button>';
els.pdfSection.append(aiPanel);
let extraction;
const aiStatus = document.getElementById('aiStatus');
document.getElementById('extractAi').onclick = async () => {
  const button = document.getElementById('extractAi');
  button.disabled = true;
  document.getElementById('aiCsv').disabled = document.getElementById('aiEdit').disabled = true;
  extraction = null;
  document.getElementById('aiJson').textContent = '';
  try {
    const accessCode = document.getElementById('extractionAccessCode').value;
    let images;
    if (accessCode) {
    aiStatus.textContent = 'Rendering page images…';
    const pdf = await ensurePdfLoaded();
    if (pdf.numPages !== 2) throw new Error('Select a PDF containing exactly two pages.');
    await renderPageToCanvas(1, els.page1Canvas, appState.rotations.page1);
    await renderPageToCanvas(2, els.page2Canvas, appState.rotations.page2);
    images = [els.page1Canvas,els.page2Canvas].map(source => {
      const canvas = document.createElement('canvas');
      const scale = Math.min(1,2000/Math.max(source.width,source.height));
      canvas.width = Math.round(source.width*scale); canvas.height = Math.round(source.height*scale);
      const ctx = canvas.getContext('2d'); ctx.fillStyle = 'white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(source,0,0,canvas.width,canvas.height);
      return canvas.toDataURL('image/jpeg',.85);
    });
    }
    aiStatus.textContent = accessCode ? 'Requesting extraction…' : 'Loading saved sample results…';
    const response = await fetch('/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({images,accessCode,sample:appState.sampleName,model:document.getElementById('extractionModel').value})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Extraction failed');
    extraction = result;
    document.getElementById('aiJson').textContent = JSON.stringify(result,null,2);
    document.getElementById('aiCsv').disabled = document.getElementById('aiEdit').disabled = false;
    aiStatus.textContent = result.source === 'sample' ? (result.accessStatus === 'unconfigured' ? 'Live GPT is not configured: set OPENAI_ACCESS_CODE in Vercel and redeploy. ' : result.accessStatus === 'incorrect' ? 'Access code did not match. ' : '') + 'Saved sample results loaded; no OpenAI request was made. Review before saving.' : 'Live GPT extraction ready. Review the transcription before saving.';
  } catch(error) { aiStatus.textContent = error.message; }
  finally { button.disabled = false; }
};
document.getElementById('aiCsv').onclick = () => {
  const rows = extraction.visits.map(visit=>({...extraction.header,...visit}));
  const columns = [...new Set(rows.flatMap(Object.keys))];
  const quote = value => '"'+String(value ?? '').replace(/"/g,'""')+'"';
  fallbackDownload(new Blob([columns.map(quote).join(',')+'\n'+rows.map(row=>columns.map(key=>quote(row[key])).join(',')).join('\n')],{type:'text/csv'}),'extracted_visits.csv');
};
document.getElementById('aiEdit').onclick = () => {
  const frame = els.pinkFormFrame.contentWindow;
  frame.clearForm();frame.fillAllAboveTableFromRow(extraction.header);
  const blankRow = frame.document.querySelector('#visitsBody tr');
  extraction.visits.forEach((visit,index)=>{const row=index === 0 && blankRow ? blankRow : frame.addVisitRow(visit.age_months ?? '');frame.fillVisitRow(row,visit);});
  frame.refreshToggleUI(frame.document);
  showSection(els.formSection);
  setStatus(`Opened ${extraction.visits.length} visit rows for editing`);
};
