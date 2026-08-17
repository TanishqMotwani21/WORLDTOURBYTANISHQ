import { JSDOM } from 'jsdom'
import fs from 'fs'

const html = fs.readFileSync('dist/index.html', 'utf8')
const jsFile = fs.readdirSync('dist/assets').find(f => f.endsWith('.js'))
const js = fs.readFileSync('dist/assets/' + jsFile, 'utf8')

const pages = ['#/dashboard', '#/verify', '#/similar', '#/history', '#/how-it-works']
let failures = 0

for (const route of pages) {
  const dom = new JSDOM(html, {
    url: 'http://localhost:8000/' + route,
    runScripts: 'outside-only',
    pretendToBeVisual: true,
  })
  // polyfills the app needs
  dom.window.fetch = (...a) => fetch(...a)
  dom.window.matchMedia = dom.window.matchMedia || (() => ({ matches:false, addListener(){}, removeListener(){} }))
  try {
    dom.window.eval(js)
    // give React time to render + effects to fire
    await new Promise(r => setTimeout(r, 1200))
    const text = dom.window.document.body.textContent
    const hasRoot = dom.window.document.querySelector('#root').children.length > 0
    const keywords = {
      '#/dashboard': 'AI Title Verification',
      '#/verify': 'Verify a New Title',
      '#/similar': 'Similar Titles',
      '#/history': 'Submission History',
      '#/how-it-works': 'How It Works',
    }
    const ok = hasRoot && text.includes(keywords[route]) && text.includes('CODECRAFTERS')
    console.log(`${ok ? 'PASS' : 'FAIL'} ${route}  (root children: ${dom.window.document.querySelector('#root').children.length}, keyword: ${text.includes(keywords[route])})`)
    if (!ok) failures++
  } catch (e) {
    console.log(`FAIL ${route} — exception: ${e.message.slice(0, 150)}`)
    failures++
  }
}
console.log(failures === 0 ? 'ALL PAGES RENDER' : `${failures} PAGE(S) FAILED`)
process.exit(failures ? 1 : 0)
