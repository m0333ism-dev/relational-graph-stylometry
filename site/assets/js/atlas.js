'use strict';
const DATA=JSON.parse(document.getElementById('data').textContent);
const REGISTER=JSON.parse(document.getElementById('candidates').textContent);
const $=id=>document.getElementById(id);
const ALL=Array.from({length:DATA.ids.length},(_,i)=>i);
const GENRES=['email','review','legal','abstracts','articles','papers'].filter(g=>DATA.genres.includes(g));
const COLORS=['#0072b2','#d55e00','#009e73','#cc79a7','#e69f00','#555555','#56b4e9','#882255'];
const featureLetter=index=>index<26?String.fromCharCode(65+index):String(index+1);
let selected=[...REGISTER.records.find(c=>c.id==='M01').features];
let committed=null,apiState=null,dirty=true,busy=false;
let picked={human:[],ai:[]};
const rankCache=new Map();

function extent(values){let lo=Infinity,hi=-Infinity;for(const v of values){lo=Math.min(lo,v);hi=Math.max(hi,v)}if(lo===hi){const d=Math.abs(lo)*.05||.5;return[lo-d,hi+d]}const pad=(hi-lo)*.04;return[lo-pad,hi+pad]}
function rankColumn(j){
  if(rankCache.has(j))return rankCache.get(j);
  const result=ViewMath.rankColumn(DATA,j);
  rankCache.set(j,result);return result;
}
function column(name,scale){
  const j=DATA.names.indexOf(name);if(j<0)throw Error('Unknown feature');
  if(scale==='rank')return rankColumn(j);
  return ViewMath.column(DATA,j,scale);
}
function rowsFor(view){
  const rows=ViewMath.rowsFor(DATA,view);
  if(view.visual_window!=='entropy')return rows;
  const spec=DATA.visual_windows[view.genre];
  if(!spec||!['char_bigram_entropy','char_trigram_entropy'].every(f=>view.features.includes(f)))throw Error('The recorded entropy window requires both character-entropy anchors and one named large genre.');
  const a=column('char_bigram_entropy','minmax'),b=column('char_trigram_entropy','minmax');
  return rows.filter(i=>a[i]>=spec.A[0]&&a[i]<=spec.A[1]&&b[i]>=spec.B[0]&&b[i]<=spec.B[1]);
}
function customSelection(){$('candidate').value='CUSTOM';updateGuide()}
function currentSettings(){return{candidate:$('candidate').value,genre:$('genre').value,mode:$('mode').value,scale:$('scale').value,framing:$('framing').value,order:$('order').value,features:[...selected],collapse_duplicates:$('collapse').checked,visual_window:$('band-window').checked?'entropy':'none'}}
function changed(){dirty=true;$('pending').textContent='Settings changed. Apply the view before recording it.';$('save').disabled=true;updateScaleNote()}
function updateScaleNote(){const explanations={raw:'Original units. Features can have different scales; line proximity is not a linguistic distance.',minmax:'Same full-corpus minimum and maximum per feature for both classes. This reproduces the original exploratory scale.',rank:'Average percentile rank within each genre and class, using all original rows. This shows dependence shape and removes marginal levels/ranges; it is not a deployable scoring transform.'};$('scale-note').textContent=explanations[$('scale').value]}

function renderFeatures(){
  $('selected-features').replaceChildren();
  selected.forEach((name,index)=>{
    const item=document.createElement('li');const text=document.createElement('span');text.className='name';text.textContent=featureLetter(index)+' · '+name;item.append(text);
    for(const[action,label,disabled,fn]of[['up','↑',index===0,()=>[selected[index-1],selected[index]]=[selected[index],selected[index-1]]],['down','↓',index===selected.length-1,()=>[selected[index+1],selected[index]]=[selected[index],selected[index+1]]],['remove','×',selected.length<=2,()=>selected.splice(index,1)]]){
      const button=document.createElement('button');button.type='button';button.textContent=label;button.disabled=disabled;button.setAttribute('aria-label',action+' '+name);button.onclick=()=>{fn();customSelection();renderFeatures();changed()};item.append(button)}
    $('selected-features').append(item);
  });renderLibrary();
}
function renderLibrary(){
  const query=$('feature-search').value.trim().toLowerCase();$('feature-library').replaceChildren();
  for(const name of DATA.names.filter(n=>n.toLowerCase().includes(query))){const label=document.createElement('label');const box=document.createElement('input');box.type='checkbox';box.checked=selected.includes(name);box.setAttribute('aria-label','Include '+name);box.onchange=()=>{if(box.checked)selected.push(name);else if(selected.length>2)selected=selected.filter(n=>n!==name);customSelection();renderFeatures();changed()};label.append(box,document.createTextNode(name));$('feature-library').append(label)}
}
function updateGuide(){
  const c=REGISTER.records.find(c=>c.id===$('candidate').value);
  const custom={title:'Custom multivariate exploration',observed:'You are selecting a new combination. Record the visible pattern before fitting a mathematical explanation.',question:'What does the joint configuration suggest, and which genres contradict it?',remains:'No test, composite or transfer claim has been established for this selection.',status:'EXPLORATORY · UNTESTED'};
  const guide=c?.graph_first_guide||c||custom;$('guide-title').textContent=guide.title;$('guide-observed').textContent=guide.observed;$('guide-question').textContent=guide.question;$('guide-remains').textContent=guide.remains;$('candidate-status').textContent=guide.status.replaceAll('_',' ');
  $('focused-example').hidden=c?.id!=='M01';
  if($('formula-attempt'))$('formula-attempt').hidden=c?.id!=='M01';
}
function initializeRecurrenceBoard(query){
  const genre=$('evidence-genre'),scope=$('evidence-scope');if(!genre||!scope)return;
  if(GENRES.includes(query.get('genre')))genre.value=query.get('genre');
  function showEvidence(){
    const papers=genre.value==='papers';scope.options[0].disabled=papers;if(papers)scope.value='full';
    for(const card of document.querySelectorAll('[data-evidence-genre]')){
      card.hidden=card.dataset.evidenceGenre!==genre.value;
      for(const figure of card.querySelectorAll('[data-evidence-view]'))figure.hidden=figure.dataset.evidenceView!==scope.value;
    }
  }
  genre.onchange=showEvidence;scope.onchange=showEvidence;showEvidence();
}
function initializeWorkingGraphs(query){
  const group=$('working-group'),page=$('working-page');if(!group||!page)return;
  group.value=query.get('candidate')==='M07'?'R03':'R02';
  page.value=['abstracts','articles','papers'].includes(query.get('genre'))?'2':'1';
  function show(){for(const card of document.querySelectorAll('[data-working-group]')){card.hidden=card.dataset.workingGroup!==group.value;for(const figure of card.querySelectorAll('[data-working-page]'))figure.hidden=figure.dataset.workingPage!==page.value}}
  group.onchange=show;page.onchange=show;show();
}
function axisTitle(name,scale){return name+(scale==='rank'?' · percentile':scale==='minmax'?' · shared min–max':' · raw')}
function baseLayout(){return{template:'plotly_white',margin:{l:70,r:25,t:25,b:100},hovermode:'closest',showlegend:true,legend:{orientation:'h',y:-.3,itemclick:false,itemdoubleclick:false},uirevision:Date.now()}}
function colorSpec(name,view,rows,columns){const range=view.scale==='raw'?extent(rows.map(i=>columns[name][i])):[0,1];return{colorscale:'Viridis',cmin:range[0],cmax:range[1],showscale:true,colorbar:{title:{text:name.replaceAll('_',' ')},thickness:10,len:.75}}}
function tracesFor(view,label,rows,columns){
  const ix=rows.filter(i=>DATA.labels[i]===label);const f=view.features;const id=ix.map(i=>DATA.ids[i]);
  const metadata=ix.map(i=>[DATA.ids[i],DATA.genres[i]]);
  if(view.mode==='joint'){
    const marker={size:6,opacity:.55,color:label==='human'?'#1764a1':'#c94c18'};
    if(f[2])Object.assign(marker,colorSpec(f[2],view,rows,columns),{color:ix.map(i=>columns[f[2]][i])});
    if(f[3]){const vals=rows.map(i=>columns[f[3]][i]);const lo=Math.min(...vals),hi=Math.max(...vals);marker.size=ix.map(i=>hi===lo?6:4+6*(columns[f[3]][i]-lo)/(hi-lo))}
    return[{type:'scattergl',mode:'markers',x:ix.map(i=>columns[f[0]][i]),y:ix.map(i=>columns[f[1]][i]),ids:id,customdata:metadata,marker,showlegend:false,hovertemplate:'%{customdata[0]}<br>%{customdata[1]}<br>A=%{x}<br>B=%{y}<extra></extra>'}];
  }
  if(view.mode==='three_d'){
    if(f.length<3)throw Error('Choose at least three features for a 3D view');
    const marker={size:3,opacity:.65,color:label==='human'?'#1764a1':'#c94c18'};
    if(f[3])Object.assign(marker,colorSpec(f[3],view,rows,columns),{color:ix.map(i=>columns[f[3]][i])});
    return[{type:'scatter3d',mode:'markers',x:ix.map(i=>columns[f[0]][i]),y:ix.map(i=>columns[f[1]][i]),z:ix.map(i=>columns[f[2]][i]),customdata:metadata,marker,showlegend:false,hovertemplate:'%{customdata[0]}<br>%{customdata[1]}<br>A=%{x}<br>B=%{y}<br>C=%{z}<extra></extra>'}];
  }
  if(view.mode==='traces'){
    const ordered=view.order==='anchor'?[...ix].sort((a,b)=>columns[f[0]][a]-columns[f[0]][b]):ix;
    return f.map((name,j)=>({type:'scattergl',mode:'lines',x:ordered.map((i,k)=>view.order==='anchor'?columns[f[0]][i]:k),y:ordered.map(i=>columns[name][i]),name,line:{color:COLORS[j%COLORS.length],width:1},customdata:ordered.map(i=>[DATA.ids[i],DATA.genres[i]]),hovertemplate:'%{customdata[0]}<br>%{customdata[1]}<br>%{y}<extra>'+name+'</extra>'}));
  }
  const line={color:ix.map(i=>columns[f.at(-1)][i]),...colorSpec(f.at(-1),view,rows,columns)};
  line.colorbar.title.text=featureLetter(f.length-1);
  return[{type:'parcoords',line,dimensions:f.map((name,j)=>({label:featureLetter(j),values:ix.map(i=>columns[name][i]),range:view.scale==='raw'||view.framing==='displayed'?extent(rows.map(i=>columns[name][i])):[0,1]})),labelfont:{size:13},tickfont:{size:9}}];
}
function layoutFor(view,rows,columns){
  const layout=baseLayout(),f=view.features;
  const range=name=>view.scale==='raw'||view.framing==='displayed'?extent(rows.map(i=>columns[name][i])):[-.02,1.02];
  if(view.mode==='joint'){layout.xaxis={title:{text:axisTitle(f[0],view.scale)},range:range(f[0]),automargin:true};layout.yaxis={title:{text:axisTitle(f[1],view.scale)},range:range(f[1]),automargin:true}}
  if(view.mode==='three_d'){layout.margin={l:0,r:0,t:0,b:0};layout.scene={xaxis:{title:{text:'A'},range:range(f[0])},yaxis:{title:{text:'B'},range:range(f[1])},zaxis:{title:{text:'C'},range:range(f[2])},aspectmode:'cube',camera:{eye:{x:1.3,y:1.5,z:1.1},up:{x:0,y:0,z:1},center:{x:0,y:0,z:0}}}}
  if(view.mode==='traces'){layout.xaxis={title:{text:view.order==='anchor'?axisTitle(f[0],view.scale):'Document index within class · not time or paired between classes'},automargin:true};layout.yaxis={title:{text:view.scale==='raw'?'Raw measurements · mixed feature units':'Original shared min–max'},range:view.scale==='raw'||view.framing==='displayed'?extent(rows.flatMap(i=>f.map(name=>columns[name][i]))):[-.02,1.02],automargin:true}}
  if(view.mode==='traces'){
    layout.margin.b=Math.min(250,55+22*f.length);
    layout.xaxis.range=view.order==='anchor'?range(f[0]):[-.5,Math.max(...['human','ai'].map(label=>rows.filter(i=>DATA.labels[i]===label).length))-.5];
  }
  if(view.mode==='parallel')layout.margin={l:45,r:45,t:60,b:45};
  return layout;
}

async function applyView(){
  busy=true;$('apply').disabled=true;$('save').disabled=true;$('pending').textContent='Drawing the selected document values…';
  try{
    const view=currentSettings();if(view.features.length<2)throw Error('Choose at least two features');
    const rows=rowsFor(view);const columns=Object.fromEntries(view.features.map(name=>[name,column(name,view.scale)]));
    document.querySelector('.plots').classList.toggle('expanded',view.features.length>4&&['parallel','traces'].includes(view.mode));
    picked={human:[],ai:[]};committed=null;const initialScenes={};
    for(const label of ['human','ai']){
      const plot=$(label+'-plot');Plotly.purge(plot);
      const layout=layoutFor(view,rows,columns);
      await Plotly.newPlot(plot,tracesFor(view,label,rows,columns),layout,{responsive:true,displaylogo:false,staticPlot:view.mode==='parallel'});
      if(view.mode==='three_d')initialScenes[label]={camera:structuredClone(layout.scene.camera),axis_ranges:Object.fromEntries(['x','y','z'].map(a=>[a,[...layout.scene[a+'axis'].range]]))};
      if(view.mode==='joint')plot.on('plotly_selected',event=>{picked[label]=(event?.points||[]).map(p=>p.customdata[0]);selectionNote()});
      if(view.mode!=='parallel')plot.on('plotly_relayout',event=>{if(committed){committed.axis_ranges[label]={...(committed.axis_ranges[label]||{}),...Object.fromEntries(Object.entries(event).filter(([k,v])=>/^(xaxis|yaxis)\.(range\[[01]\]|autorange)$/.test(k)&&(typeof v==='number'||typeof v==='boolean')))};if(view.mode==='three_d'){const scene=plot.layout.scene;committed.scene_context[label]={camera:structuredClone(scene.camera),axis_ranges:Object.fromEntries(['x','y','z'].map(a=>[a,[...scene[a+'axis'].range]]))}}}});
    }
    committed={...view,axis_ranges:{human:{},ai:{}},scene_context:initialScenes};dirty=false;
    const counts=['human','ai'].map(label=>{const ix=rows.filter(i=>DATA.labels[i]===label);return label.toUpperCase()+': '+ix.length+' displayed documents, '+new Set(ix.map(i=>DATA.groups[i])).size+' distinct full feature vectors'});
    $('view-title').textContent=(view.genre==='ALL'?'All genres':view.genre)+' · '+{joint:'joint configuration',three_d:'three-dimensional configuration',traces:'feature traces',parallel:'parallel coordinates'}[view.mode];
    $('counts').textContent=counts.join(' | ');
    let encoding=view.mode==='joint'?'A = horizontal axis; B = vertical axis'+(view.features[2]?'; C = colour':'')+(view.features[3]?'; D = point size':'')+'.':view.mode==='three_d'?'A/B/C = three spatial axes'+(view.features[3]?'; D = colour':'')+'.':view.mode==='traces'?'Every feature trace retains values from the same document order.':'Each polyline is one document. Axis letters follow the selected-feature list; colour shows '+featureLetter(view.features.length-1)+'. This overview is read-only; use joint views for point selection.';
    if(['joint','three_d'].includes(view.mode)&&view.features.length>4)encoding+=' This view encodes the first four features; traces and parallel coordinates display all '+view.features.length+'.';
    $('encoding').textContent=encoding;
    const warnings=view.features.filter(n=>DATA.flags[n]).map(n=>n+': '+DATA.flags[n]);
    if(view.genre==='papers')warnings.push('Only 23 documents per class. Treat this panel as descriptive.');
    if(view.genre==='ALL')warnings.push('Genres are pooled in this view; inspect each genre before interpreting recurrence.');
    if(view.mode==='traces')warnings.push('Line connections are a visual aid, not a temporal process.');
    if(view.visual_window==='entropy')warnings.push('Recorded exploratory window: A '+JSON.stringify(DATA.visual_windows[view.genre].A)+' and B '+JSON.stringify(DATA.visual_windows[view.genre].B)+' on the original shared scale. Both limits hold in each selected document.');
    $('warnings').textContent=warnings.join(' ');$('pending').textContent='View applied. You can now record what is visible.';
    selectionNote();$('save').disabled=!apiState;
  }catch(error){$('pending').textContent='View could not be drawn: '+error.message;dirty=true}
  finally{busy=false;$('apply').disabled=false}
}
function selectionNote(){const n=picked.human.length+picked.ai.length;$('selection-note').textContent=n?n+' document points selected. Their IDs will be saved with the observation.':'Each point is one document. Joint views support lasso or box selection; unselected notes retain the full displayed ID list.'}

// Browser-local research notes for the public static portal.
const NOTES_KEY='exp03.portal.notes.v1.'+DATA.data_sha256;
const publishedNotes=JSON.parse(document.getElementById('published-notes').textContent);
let browserNotes=[];
function loadBrowserNotes(){
  const saved=localStorage.getItem(NOTES_KEY);
  if(saved){const parsed=JSON.parse(saved);if(!Array.isArray(parsed))throw Error('Stored notes are not a JSON array');browserNotes=parsed}
  return {notes_count:publishedNotes.length+browserNotes.length,recent_notes:[...publishedNotes,...browserNotes]};
}
function history(state){
  $('history-count').textContent=publishedNotes.length+' published observation'+(publishedNotes.length===1?'':'s')+' · '+browserNotes.length+' private note'+(browserNotes.length===1?'':'s')+' in this browser. Export your notes to keep a copy.';
  $('recent-notes').replaceChildren();
  for(const note of [...state.recent_notes].reverse()){
    const div=document.createElement('div');div.className='note';
    const strong=document.createElement('strong');strong.textContent=note.view.candidate+' · '+note.view.genre+' · '+note.decision.replaceAll('_',' ')+' · '+note.author.replaceAll('_',' ');
    const p=document.createElement('p');p.textContent=note.observation;div.append(strong,p);$('recent-notes').append(div);
  }
}
async function saveNote(){
  if(dirty||busy||!committed){$('save-status').textContent='Apply the current view before saving.';return}
  $('save').disabled=true;
  try{
    const observation=$('observation').value.trim(),decision=$('decision').value;
    if(observation.length<5)throw Error('Describe the observation in at least five characters');
    const graph_target={pattern_id:$('pattern-id').value.trim(),interaction_description:$('interaction-description').value.trim(),must_preserve:$('must-preserve').value.trim(),formula_idea:$('formula-idea').value.trim()};
    if(graph_target.pattern_id&&!/^[A-Za-z0-9_-]{1,64}$/.test(graph_target.pattern_id))throw Error('Use letters, digits, underscores or hyphens in the pattern ID');
    if(decision==='nominate_for_formula'&&(!graph_target.pattern_id||graph_target.interaction_description.length<5||graph_target.must_preserve.length<5))throw Error('Specify the pattern, collective interaction and required capture before nominating a formula');
    const rows=rowsFor(committed),ids=rows.map(i=>DATA.ids[i]),selected_ids=[...new Set([...picked.human,...picked.ai])].sort();
    if(selected_ids.some(id=>!ids.includes(id)))throw Error('A selected point is outside the current view');
    const record={id:new Date().toISOString()+'_'+crypto.randomUUID(),schema_version:'exp03.graph_observation.v1',saved_at_utc:new Date().toISOString(),author:$('author').value,decision,view:structuredClone(committed),observation,interpretation:$('interpretation').value.trim(),counterexamples:$('counterexamples').value.trim(),next_question:$('next-question').value.trim(),graph_target,displayed_document_ids:ids,selected_document_ids:selected_ids,counts:Object.fromEntries(['human','ai'].map(label=>[label,rows.filter(i=>DATA.labels[i]===label).length])),data_sha256:DATA.data_sha256,workspace_build_sha256:document.documentElement.dataset.researchBuild,scope:'FULL_CORPUS_EXPLORATORY',inference_status:'VISUAL_OBSERVATION_NOT_FORMULA_VALIDATION',storage:'VISITOR_BROWSER_ONLY'};
    const current=loadBrowserNotes(),next=[...browserNotes,record];
    localStorage.setItem(NOTES_KEY,JSON.stringify(next));browserNotes=next;
    apiState={notes_count:publishedNotes.length+next.length,recent_notes:[...publishedNotes,...next]};history(apiState);
    $('save-status').textContent='Saved in this browser. Your exact view and document IDs are preserved. Export your notes for a backup; the published notebook is unchanged.';
  }catch(error){$('save-status').textContent='Not saved: '+error.message+'. Your text remains in the form.'}
  finally{$('save').disabled=dirty||!apiState}
}
function exportBrowserNotes(){
  try{
    loadBrowserNotes();
    const value={schema_version:'exp03.browser_notes_export.v1',exported_at_utc:new Date().toISOString(),source_sha256:DATA.data_sha256,workspace_build_sha256:document.documentElement.dataset.researchBuild,notes:browserNotes};
    const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='exp03-observations-'+new Date().toISOString().slice(0,10)+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('save-status').textContent='Exported '+browserNotes.length+' private notes with their exact view context.';
  }catch(error){$('save-status').textContent='Export failed: '+error.message}
}

async function init(){
  if(matchMedia('(max-width:1150px)').matches)$('view-controls').open=false;
  $('freeze-status').textContent='Fixed-CSV exploratory research complete · 31 additional inspected sheets';
  for(const c of REGISTER.records){const option=document.createElement('option');option.value=c.id;option.textContent=c.id+' · '+(c.graph_first_guide?.title||c.title);$('candidate').append(option)}
  const custom=document.createElement('option');custom.value='CUSTOM';custom.textContent='Custom feature combination';$('candidate').append(custom);$('candidate').value='M01';
  for(const g of GENRES){const option=document.createElement('option');option.value=g;option.textContent=g;$('genre').append(option)}$('genre').value='review';$('scale').value='minmax';$('mode').value='traces';
  const query=new URLSearchParams(location.search),candidate=REGISTER.records.find(c=>c.id===query.get('candidate'));
  $('band-window').checked=query.get('window')==='entropy';
  if(candidate){$('candidate').value=candidate.id;selected=[...candidate.features];$('genre').value=candidate.graph_first_guide?.genre||candidate.genre}
  for(const[id,values]of [['genre',['ALL',...GENRES]],['mode',['joint','three_d','traces','parallel']],['scale',['minmax','raw']],['order',['csv','anchor']],['framing',['global','displayed']]])if(values.includes(query.get(id)))$(id).value=query.get(id);
  $('candidate').onchange=()=>{const c=REGISTER.records.find(c=>c.id===$('candidate').value);if(c){selected=[...c.features];$('genre').value=c.graph_first_guide?.genre||c.genre;renderFeatures()}updateGuide();changed()};
  for(const id of ['genre','mode','scale','order','collapse','framing','band-window'])$(id).onchange=changed;
  $('feature-search').oninput=renderLibrary;$('apply').onclick=applyView;$('save').onclick=saveNote;
  updateGuide();renderFeatures();updateScaleNote();initializeRecurrenceBoard(query);initializeWorkingGraphs(query);initializeExpandedSearch(query);initializeGraphMicroscope(query);
  $('provenance').textContent='Full-corpus exploratory workspace · '+DATA.ids.length+' documents · '+DATA.names.length+' frozen features · CSV SHA-256 '+DATA.data_sha256+'. Original shared scaling opens by default. Record the collective interaction before designing a formula.';
  try{apiState=loadBrowserNotes();history(apiState);$('export-notes').onclick=exportBrowserNotes}catch(error){$('save-status').textContent='Browser storage is unavailable: '+error.message+'. The graph explorer remains available.'}
  await applyView();
}
function initializeExpandedSearch(query){
  const node=$('expanded-search-data');if(!node)return;
  const context=JSON.parse(node.textContent),group=$('search-group'),view=$('search-view'),page=$('search-page');
  group.value=context.candidate_groups[query.get('candidate')]||'sentence_rhythm';
  page.value=['abstracts','articles','papers'].includes(query.get('genre'))?'2':'1';
  const figures=[...document.querySelectorAll('.expanded-search-figure')];
  function draw(defaultView=false){
    const key=group.value,entry=context.groups[key],available=new Set(figures.filter(f=>f.dataset.group===key).map(f=>f.dataset.view));
    for(const option of view.options)option.disabled=!available.has(option.value);
    if(defaultView||!available.has(view.value))view.value=available.has('slices')?'slices':available.has('focus')?'focus':available.has('full')?'full':'overview';
    page.disabled=view.value==='profiles';
    for(const figure of figures)figure.hidden=!(figure.dataset.group===key&&figure.dataset.view===view.value&&(view.value==='profiles'||figure.dataset.page===page.value));
    $('search-members').textContent=entry.features.map((f,i)=>String.fromCharCode(65+i)+' = '+f).join(' · ');
    $('search-question').textContent=entry.question;
    $('search-framing').textContent=view.value==='slices'?'Same fixed mean/median regions for both classes and every genre. Raw IQR/maximum response axes; minimum length sets marker area. Empty and sparse regions are retained.':view.value==='focus'?'Shared pooled central framing only. Full-range companions are available above; every point and off-screen count is retained. Colours and marker mapping match the full view.':view.value==='profiles'?'All six genres. Each line connects six feature measurements from one document on the original shared scale.':'Complete representative tuples. Human and AI share axes, colour and marker-area mapping within each genre. The repetition frequency comparison uses raw common units where labelled.';
    $('search-interaction').textContent=entry.interaction;
    $('search-control').textContent='Measurement context: '+entry.definition_control;
    $('search-notes').replaceChildren();
    for(const genre of GENRES){const row=document.createElement('tr'),name=document.createElement('th'),note=document.createElement('td');name.scope='row';name.textContent=genre;note.textContent=entry.genres[genre];row.append(name,note);$('search-notes').append(row)}
  }
  group.onchange=()=>draw(true);view.onchange=()=>draw();page.onchange=()=>draw();draw(true);
}
function initializeGraphMicroscope(query){
  const node=$('microscope-data');if(!node)return;
  const data=JSON.parse(node.textContent),topic=$('microscope-topic'),view=$('microscope-view'),page=$('microscope-page');
  const figures=[...document.querySelectorAll('.microscope-figure')];
  topic.value=data.topics[query.get('microscope')]?query.get('microscope'):data.candidate_topics[query.get('candidate')]||'R06';
  page.value=['1','2'].includes(query.get('microscope_page'))?query.get('microscope_page'):['email','review','legal'].includes(query.get('genre'))?'1':'2';
  if(query.get('microscope_view'))view.value=query.get('microscope_view');
  const framing={length_restricted:'The same adjective/amod rectangles and mean sentence length 15–25 for both classes. Adverb and advmod form the spatial band; depth is the third axis; LY sets area. This is a common interval, not exact matching. Full length context remains available.',length_context:'Raw mean sentence length against depth within the same three adjective/amod rectangles. Compare this full context with the common 15–25-token companion.',depth1:'Same adjective/amod regions. Adverb, advmod and depth unfolded spatially; LY sets marker area. Compare the second viewing angle and the length companions.',depth2:'The exact same modifier tuples from the other side: adverb, advmod and depth, with LY marker area.',counts:'Recovered alphabetic word count with original phrase types and POS entropy. Counts are reconstructed from redundancies in the fixed CSV.',states:'The same maximum-bigram / maximum-trigram integer states: (2,1), (3,1), (3,2). Word count remains visible; empty states are retained.',overview:'All representative original tuples on the original shared corpus minmax scale. Human and AI use identical axes and visual mappings within each genre.',profiles:'All six genres. Each line joins six measurements from one document on the original shared scale; this is not a time sequence or cross-class pairing.',joint:'The same fixed anchor rectangles for both classes and every genre. Joint responses use labelled raw units. Empty and sparse regions remain visible.'};
  function draw(reset=false){
    const key=topic.value,entry=data.topics[key],available=new Set(figures.filter(f=>f.dataset.topic===key).map(f=>f.dataset.view));
    for(const option of view.options)option.disabled=!available.has(option.value);
    if(reset||!available.has(view.value))view.value=available.has('length_restricted')?'length_restricted':available.has('states')?'states':available.has('joint')?'joint':'overview';
    page.disabled=view.value==='profiles';
    for(const f of figures)f.hidden=!(f.dataset.topic===key&&f.dataset.view===view.value&&(view.value==='profiles'||f.dataset.page===page.value));
    $('microscope-members').textContent=entry.features.map((f,i)=>String.fromCharCode(65+i)+' = '+f).join(' · ');
    $('microscope-framing').textContent=framing[view.value];$('microscope-observation').textContent=entry.interaction;$('microscope-limits').textContent='Exceptions and limits: '+entry.exceptions;$('microscope-control').textContent=entry.definition_control;
    $('microscope-notes').replaceChildren();for(const genre of GENRES){const row=document.createElement('tr'),label=document.createElement('th'),text=document.createElement('td');label.scope='row';label.textContent=genre;text.textContent=entry.genres[genre];row.append(label,text);$('microscope-notes').append(row)}
    const link=new URL(location.href);link.searchParams.set('microscope',key);link.searchParams.set('microscope_view',view.value);link.searchParams.set('microscope_page',page.value);link.hash='graph-microscope';$('microscope-link').href=link.href;
  }
  topic.onchange=()=>draw(true);view.onchange=()=>draw();page.onchange=()=>draw();draw();
}
init();
