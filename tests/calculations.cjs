const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(require('path').join(__dirname,'..','index.html'),'utf8');
const js=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(js); // Entire application must parse.
function extract(name){const start=js.indexOf('function '+name+'(');assert(start>=0,name);let n=0,begin=js.indexOf('{',start);for(let i=begin;i<js.length;i++){if(js[i]==='{')n++;if(js[i]==='}'&&!--n)return js.slice(start,i+1);}}
const ctx=vm.createContext({});
vm.runInContext('const today=new Date(2026,9,29);const MON={JAN:0,FEB:1,MAR:2,APR:3,MAY:4,JUN:5,JUL:6,AUG:7,SEP:8,OCT:9,NOV:10,DEC:11};'+['parseQ','calendarDate','pd','withinMonths','crashKey','isPrimaryLiability'].map(extract).join('\n'),ctx);
let count=0;function check(expr,expected){assert.equal(vm.runInContext(expr,ctx),expected,expr);count++;}
for(const q of ['294345',' USDOT 294345 ','USDOT# 294345','DOT: 294345','us dot 0294345','DOT-294345'])check(`parseQ(${JSON.stringify(q)}).dot`,'294345');
for(const q of ['MC767467','mc-767467','MC # 0767467'])check(`parseQ(${JSON.stringify(q)}).mc`,'767467');
for(const q of ['MC000000','0','DOT:','USDOT 123abc','123456789'])check(`Boolean(parseQ(${JSON.stringify(q)}).error)`,true);
check('parseQ("123").dot','123');check('parseQ("Karl’s Transport").name','Karl’s Transport');check('parseQ("MC Trucking").name','MC Trucking');
for(const d of ['20260229','2026-02-30','31-APR-26','12-XYZ-26','20261301'])check(`pd(${JSON.stringify(d)}) === null`,true);
check('pd("20240229").getDate()',29);check('pd("29-OCT-26").getMonth()',9);check('pd("10/29/2026").getDate()',29);
check('withinMonths(pd("2024-10-29"),24)',true);check('withinMonths(pd("2024-10-28"),24)',false);check('withinMonths(pd("2026-10-30"),24)',false);check('withinMonths(null,24)',false);
check('withinMonths(pd("2024-02-29"),12,new Date(2025,1,28))',true);
check('crashKey({report_number:"A",report_state:"WI"}) === crashKey({report_number:"B",report_state:"WI"})',false);check('crashKey({report_date:"20260101",report_state:"WI"})',null);
for(const form of ['91','91X','BMC-91X'])check(`isPrimaryLiability({src:'Motus',form:'${form}'})`,true);
for(const form of ['34','32','84',''])check(`isPrimaryLiability({src:'Motus',form:'${form}'})`,false);
check('isPrimaryLiability({src:"L&I",type:"BIPD Primary"})',true);check('isPrimaryLiability({src:"L&I",type:"BIPD Excess"})',false);
console.log(`${count} regression assertions passed; full application JavaScript parses.`);
