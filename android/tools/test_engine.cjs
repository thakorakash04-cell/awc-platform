const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const root = require('node:path').resolve(__dirname,'../app/src/main/assets');
const context={window:{}};vm.createContext(context);vm.runInContext(fs.readFileSync(root+'/catalog.js','utf8'),context);
const catalog=JSON.parse(JSON.stringify(context.window.AWC_CATALOG));
const engine=require(root+'/engine.js');
assert.equal(catalog.products.length,23);assert.equal(catalog.rows.length,508);
assert.equal(engine.evaluate(catalog,{},true).total_count,0);
for(let i=0;i<5;i++){const flags=[false,false,false,false,false];flags[i]=true;assert.equal(engine.triage(flags,false,0),'emergency');}
assert.equal(engine.triage([false],true,0),'urgent');assert.equal(engine.triage([false],false,4),'urgent');assert.equal(engine.triage([false],false,3),'routine');
// Zero classified pixels must not yield 100% red.
const white=new Uint8ClampedArray(400*400*4).fill(255);
assert.equal(engine.segment(white,400,400).classified,0);
assert.deepEqual(engine.segment(white,400,400).percentages,[0,0,0]);
assert.equal(engine.quality(white,400,400).passed,false);
const dark=new Uint8ClampedArray(400*400*4).fill(0);assert.equal(engine.quality(dark,400,400).passed,false);
const random=new Uint8ClampedArray(400*400*4);for(let i=0;i<random.length;i+=4){const n=((i*1664525+1013904223)>>>0)%170+45;random[i]=n;random[i+1]=n;random[i+2]=n;random[i+3]=255;}
assert.equal(engine.quality(random,400,400).passed,true);
if(process.argv[2]){
 const cases=JSON.parse(fs.readFileSync(process.argv[2]));
 for(const test of cases){const r=engine.evaluate(catalog,test.query);assert.deepEqual(r.all_matches.map(p=>p.product_name),test.names,JSON.stringify(test.query));assert.equal(r.fallback_used,test.fallback);}
 console.log('Python / JavaScript parity:',cases.length,'query cases');
}
console.log('Catalog, triage, quality and segmentation checks passed');
