/* Replay saved graph displays. No fitted model or sampling runs in the browser. */
(()=>{'use strict';
  const el=id=>document.getElementById(id);
  const labels={forest_leaf16:'Forest · leaf 16',kernel_k32:'Local kernel · k = 32',legacy_cubic:'Frozen cubic · 56 columns',product_control:'Independent response marginals'};
  const genres=['email','review','legal','abstracts','articles','papers'];
  let data,drawing=false,pending=false;
  const format=value=>Number.isFinite(value)?value.toFixed(4):'—';
  const selection=()=>({family:el('capture-family').value,genre:el('capture-genre').value,model:el('capture-model').value,view:el('capture-view').value});
  function options(){
    const family=el('capture-family').value, model=el('capture-model'), view=el('capture-view');
    const oldModel=model.value,oldView=view.value;
    model.replaceChildren(...(family==='R04'?['forest_leaf16','kernel_k32']:['forest_leaf16','kernel_k32','legacy_cubic','product_control']).map(value=>new Option(labels[value],value)));
    model.value=[...model.options].some(o=>o.value===oldModel)?oldModel:'forest_leaf16';
    view.replaceChildren(...(family==='R04'?[['Envelope shape','shape']]:[['Depth branches','depth'],['Modifier anchors · depth colours','anchors']]).map(([title,value])=>new Option(title,value)));
    view.value=[...view.options].some(o=>o.value===oldView)?oldView:(family==='R04'?'shape':'depth');
  }
  function axisTitles(state){
    if(state.family==='R04')return ['log(1 + IQR / σ)','log(1 + (maximum − mean) / σ)','Median offset'];
    return state.view==='anchors'?['log(1 + adjective-band radius / .05)','log(1 + adverb-band radius / .05)','Average depth']:['Median dependency depth','Maximum dependency depth','Average depth'];
  }
  function hoverRows(response){
    return response.rows.map((row,index)=>[row,data.document_ids[row],response.response_source_rows===null?'Synthetic marginal combination':response.response_source_rows[index]]);
  }
  function traces(sheet,label,method,titles){
    const context=sheet.classes[label].context,response=sheet.classes[label].responses[method];
    return [
      {type:'scatter',mode:'markers',x:context.points.map(p=>p[0]),y:context.points.map(p=>p[1]),name:'Full original context',marker:{color:'#9babb4',size:4,opacity:.28},hoverinfo:'skip'},
      {type:'scatter',mode:'markers',x:response.points.map(p=>p[0]),y:response.points.map(p=>p[1]),customdata:hoverRows(response),name:method==='original'?'Observed queries':labels[method],
        marker:{size:7,opacity:.86,color:response.points.map(p=>p[2]),colorscale:'Viridis',cmin:sheet.color_limits[0],cmax:sheet.color_limits[1],showscale:true,line:{color:'#fff',width:.3},colorbar:{title:{text:titles[2],side:'right',font:{size:10}},thickness:10,len:.85,tickfont:{size:10}}},
        hovertemplate:'CSV row %{customdata[0]}<br>%{customdata[1]}<br>x: %{x:.4f}<br>y: %{y:.4f}<br>colour: %{marker.color:.4f}<br>Response row: %{customdata[2]}<extra></extra>'}
    ];
  }
  function metrics(cell,model){
    if(model!=='product_control')return {raw:cell.models[model].mean_energy,graph:cell.graph_models[model]?.mean_graph_energy,tv:cell.models[model].branch_TV,floor:cell.models[model].unseen_mass_TV_floor};
    const p=cell.product_control;
    return {raw:p.mean_energy_estimate,graph:null,tv:p.branch_TV_exact,floor:null};
  }
  function table(state){
    el('capture-results-caption').textContent=(state.family==='R04'?'R04 sentence envelope':'R06 modifier/depth')+' · '+labels[state.model]+' · all saved genre–class cells';
    const body=el('capture-results-body');body.replaceChildren();
    for(const genre of genres)for(const label of ['human','ai']){
      const cell=data.cells[state.family][genre+'__'+label],m=metrics(cell,state.model),prior=metrics(cell,'empirical_prior');
      const row=document.createElement('tr');
      if(genre===state.genre)row.classList.add('capture-current');
      if(genre==='papers')row.classList.add('capture-descriptive');
      const values=[genre+' / '+(label==='human'?'Human':'AI')+(genre==='papers'?' †':''),cell.scored_queries+' / '+cell.graph_queries,
        format(m.raw)+(state.model==='product_control'?' ± '+format(cell.product_control.energy_Monte_Carlo_SE)+' MC SE':'')+' / '+format(prior.raw),
        format(m.graph)+' / '+format(prior.graph),format(m.tv)+' / '+format(prior.tv),format(m.floor)];
      values.forEach(value=>{const td=document.createElement('td');td.textContent=value;row.append(td)});body.append(row);
    }
    el('capture-table-note').textContent=state.model==='product_control'
      ?'The product control has unchanged forest marginals and a changed joint distribution. Its energy is a Monte Carlo estimate. Graph energy was not computed; the empirical whole-tuple support floor does not apply. † Papers are descriptive.'
      :'Model and empirical-prior losses are shown side by side. The response and graph columns have the displayed query counts; R04 excludes zero-CV queries from graph scoring. † Papers are descriptive.';
  }
  async function draw(){
    const state=selection(),key=state.family+'_'+state.genre+'_'+state.view+'.png',sheet=data.sheets[key],titles=axisTitles(state);
    document.querySelectorAll('.capture-model-name').forEach(node=>{node.textContent=labels[state.model]});
    el('capture-description').textContent=state.family==='R04'
      ?'Five members: mean, median, CV, IQR and maximum sentence length. At each query’s fixed mean/median/CV context, compare the observed joint IQR/maximum response with one saved reconstructed response.'
      :'Eight members: adjective and amod ratios, adverb and advmod ratios, mean sentence length, and average/median/maximum dependency depth. The two modifier bands and length provide context for the joint depth response.';
    el('capture-view-note').textContent=state.family==='R04'
      ?'The median-offset colour is fixed by query context. Reconstruction changes IQR/maximum positions. Shape coordinates are undefined when CV ≤ 10⁻¹⁰.'
      :state.view==='anchors'?'Anchor positions are fixed by construction. Only the associated average-depth colours change. Use Depth branches to inspect reconstructed median/maximum occupancy.'
      :state.model==='product_control'?'Synthetic product responses combine independent marginal depths. They need not be observed whole tuples and may violate depth ordering.'
      :'Both point positions and colours come from the joint depth response. Extra or suppressed strata remain visible on shared full-range axes.';
    el('capture-observation').textContent='Recorded sheet inspection: '+sheet.observation;
    const image=el('capture-sheet-image');image.src=sheet.asset;image.alt=state.family+' '+state.genre+' '+state.view+' complete inspected comparison sheet';
    el('capture-sheet-caption').textContent='Original full sheet · '+state.family+' · '+state.genre+' · '+state.view+'. The interactive panels replay its saved draws.';
    table(state);
    const counts=[];
    for(const label of ['human','ai']){
      const member=sheet.classes[label],cell=data.cells[state.family][state.genre+'__'+label];
      counts.push((label==='human'?'Human':'AI')+': '+member.responses.original.rows.length+'/'+member.query_count+' original queries plotted; '+member.responses[state.model].rows.length+' reconstructed; '+cell.unsupported_queries+' unsupported');
      for(const method of ['original',state.model]){
        const id='capture-'+label+'-'+(method==='original'?'original':'model');
        await Plotly.react(id,traces(sheet,label,method,titles),{
          margin:{l:65,r:75,b:62,t:18},paper_bgcolor:'#fff',plot_bgcolor:'#fff',showlegend:false,
          font:{family:'Segoe UI, sans-serif',size:11,color:'#234355'},
          xaxis:{title:{text:titles[0],font:{size:11}},range:sheet.axis_limits[0],gridcolor:'#e8edf0',zeroline:false,automargin:true},
          yaxis:{title:{text:titles[1],font:{size:11}},range:sheet.axis_limits[1],gridcolor:'#e8edf0',zeroline:false,automargin:true},
          uirevision:key+'__'+state.model
        },{responsive:true,displaylogo:false,modeBarButtonsToRemove:['select2d','lasso2d'],toImageButtonOptions:{format:'png',filename:state.family+'_'+state.genre+'_'+label+'_'+method}});
      }
    }
    el('capture-status').textContent=counts.join(' · ')+(state.genre==='papers'?' · Descriptive cohort only.':'');
    el('capture-study').dataset.renderedSelection=JSON.stringify(state);
    el('capture-study').dataset.renderStatus='ready';
  }
  async function schedule(){
    if(drawing){pending=true;return}drawing=true;el('capture-study').dataset.renderStatus='drawing';
    try{do{pending=false;await draw()}while(pending)}
    catch(error){el('capture-status').textContent='Saved comparison could not render: '+error.message;el('capture-study').dataset.renderStatus='error'}
    finally{drawing=false}
  }
  async function init(){
    try{
      const response=await fetch('data/capture-study.json');if(!response.ok)throw Error('HTTP '+response.status);data=await response.json();
      el('capture-family').addEventListener('change',()=>{options();schedule()});
      for(const id of ['capture-genre','capture-model','capture-view'])el(id).addEventListener('change',schedule);
      options();await schedule();
      if(location.hash==='#capture-study')el('capture-study').scrollIntoView({block:'start'});
      el('freeze-status').textContent='Updated 22 Oct 2026 · graph comparisons and genre exceptions';
    }catch(error){el('capture-status').textContent='Saved comparisons unavailable: '+error.message;el('capture-study').dataset.renderStatus='error'}
  }
  init();
})();
