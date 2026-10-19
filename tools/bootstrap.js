/* Load scientific payloads before executing the unchanged graph explorer. */
(async()=>{
  try{
    const nodes=[...document.querySelectorAll('script[type="application/json"][data-src]')];
    await Promise.all(nodes.map(async node=>{const response=await fetch(node.dataset.src);if(!response.ok)throw Error('Could not load '+node.dataset.src);node.textContent=await response.text();JSON.parse(node.textContent)}));
    for(const name of ['assets/js/view-math.js','assets/js/atlas.js','assets/js/branch-panel.js']){
      await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src=name;script.onload=resolve;script.onerror=()=>reject(Error('Could not load '+name));document.body.append(script)});
    }
    document.getElementById('portal-loading').remove();
  }catch(error){document.getElementById('portal-loading').textContent='The portal could not finish loading: '+error.message+'. Reload the page or check your connection.'}
})();
