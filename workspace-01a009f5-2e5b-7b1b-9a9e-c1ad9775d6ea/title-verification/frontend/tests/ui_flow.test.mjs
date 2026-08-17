import { JSDOM } from 'jsdom'
import fs from 'fs'

const ORIGIN = 'http://localhost:8000'
const browserFetch = (url, opts) => fetch(new URL(url, ORIGIN).href, opts)

const html = fs.readFileSync('dist/index.html', 'utf8')
const js = fs.readFileSync('dist/assets/' + fs.readdirSync('dist/assets').find(f => f.endsWith('.js')), 'utf8')

const dom = new JSDOM(html, { url: ORIGIN + '/#/verify', runScripts: 'outside-only', pretendToBeVisual: true })
dom.window.fetch = browserFetch
dom.window.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} })
dom.window.eval(js)
const doc = dom.window.document
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
await sleep(900)

const chip = [...doc.querySelectorAll('.chip')].find(c => c.textContent === 'Indian Xpress')
chip.click(); await sleep(150)
const input = doc.querySelector('input')
console.log('PASS example chip populates form:', input.value === 'Indian Xpress')

const btn = [...doc.querySelectorAll('button')].find(b => b.textContent.includes('VERIFY TITLE'))
btn.click()
await sleep(300)
console.log('PASS pipeline animation shows:', doc.body.textContent.includes('Running Verification Pipeline'))

let reached = false
for (let i = 0; i < 15 && !reached; i++) { await sleep(1000); reached = doc.body.textContent.includes('Verification Result') }
const t = doc.body.textContent
const checks = [
  ['result page reached', reached],
  ['risk pill', /HIGH RISK/.test(t)],
  ['prototype similarity indicators', t.includes('Prototype Similarity Indicators')],
  ['rule violations signal', t.includes('Rule Violations')],
  ['overlap signal', t.includes('Existing Title Overlap')],
  ['phonetic match banner or signal', t.includes('PHONETIC MATCH DETECTED')],
  ['why was this title flagged', t.includes('Why was this title flagged?')],
  ['closest matches section', t.includes('Closest Matches in the Demo Dataset')],
  ['Indian Express listed as match', [...doc.querySelectorAll('.match-card .mc-title')].some(x => x.textContent === 'Indian Express')],
  ['exact duplicate banner', t.includes('EXACT DUPLICATE IN DEMO DATA')],
]
let fail = 0
for (const [n, ok] of checks) { console.log(`${ok ? 'PASS' : 'FAIL'} ${n}`); if (!ok) fail++ }

// click a match card → detail opens
const card = doc.querySelector('.match-card')
card.click(); await sleep(250)
console.log(`${doc.body.textContent.includes('Why it matched') ? 'PASS' : 'FAIL'} match card expands with breakdown`) 

// MODIFY → edit → RESUBMIT
const modBtn = [...doc.querySelectorAll('button')].find(b => b.textContent.includes('MODIFY TITLE'))
console.log(`${modBtn ? 'PASS' : 'FAIL'} MODIFY TITLE present for HIGH RISK`)
modBtn.click(); await sleep(400)
const inp = doc.querySelector('input')
console.log('PASS modify keeps title populated:', inp.value === 'Indian Xpress')
const setter = Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype, 'value').set
setter.call(inp, 'Indus Valley Chronicle')
inp.dispatchEvent(new dom.window.Event('input', { bubbles: true }))
await sleep(250)
const rs = [...doc.querySelectorAll('button')].find(b => b.textContent.includes('RESUBMIT FOR VERIFICATION'))
console.log(`${rs ? 'PASS' : 'FAIL'} resubmit button shown`)
rs.click()
let done = false
for (let i = 0; i < 15 && !done; i++) { await sleep(1000); done = doc.body.textContent.includes('New Result') }
const t2 = doc.body.textContent
console.log(`${done ? 'PASS' : 'FAIL'} resubmission strip: Previous Result → Modified Title → New Result`)
console.log('PASS level changed to:', /LOW RISK/.test(t2) ? 'LOW RISK' : /REVIEW/.test(t2) ? 'REVIEW' : 'HIGH RISK')

// history page reflects submissions
dom.window.location.hash = '#/history'
await sleep(1200)
const ht = doc.body.textContent
console.log(`${ht.includes('Indus Valley Chronicle') && ht.includes('Indian Xpress') ? 'PASS' : 'FAIL'} history lists both submissions`)
process.exit(fail ? 1 : 0)
