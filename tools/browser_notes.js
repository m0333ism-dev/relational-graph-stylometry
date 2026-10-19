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
