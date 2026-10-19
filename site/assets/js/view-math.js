'use strict';
// The viewer and Node checks use this same transformation code.
(function(root){
  function averageRanks(values){
    const order=Array.from({length:values.length},(_,i)=>i).sort((a,b)=>values[a]-values[b]);
    const result=new Float64Array(values.length);
    let start=0;
    while(start<order.length){let end=start+1;while(end<order.length&&values[order[end]]===values[order[start]])end++;
      const rank=(start+1+end)/(2*order.length);for(let k=start;k<end;k++)result[order[k]]=rank;start=end;}
    return result;
  }
  function rankColumn(data,j){
    const result=new Float64Array(data.ids.length),groups=new Map();
    for(let i=0;i<data.ids.length;i++){const key=JSON.stringify([data.genres[i],data.labels[i]]);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(i)}
    for(const ix of groups.values()){const ranks=averageRanks(ix.map(i=>data.values[i][j]));ix.forEach((i,k)=>result[i]=ranks[k])}
    return result;
  }
  function column(data,j,scale){
    if(scale==='raw')return data.values.map(row=>row[j]);
    if(scale==='rank')return rankColumn(data,j);
    if(scale!=='minmax')throw Error('Unknown scale');
    const lo=data.minimum[j],width=data.maximum[j]-lo;
    return data.values.map(row=>width?(row[j]-lo)/width:0);
  }
  function rowsFor(data,view){
    const seen=new Set(),rows=[];
    for(let i=0;i<data.ids.length;i++){
      if(view.genre!=='ALL'&&data.genres[i]!==view.genre)continue;
      const key=JSON.stringify([data.labels[i],data.genres[i],data.groups[i]]);
      if(view.collapse_duplicates&&seen.has(key))continue;seen.add(key);rows.push(i);
    }
    return rows;
  }
  const api={averageRanks,rankColumn,column,rowsFor};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ViewMath=api;
})(globalThis);
