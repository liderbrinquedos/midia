const $ = s => document.querySelector(s);
const base = window.PORTAL_CONFIG.API_BASE_URL.replace(/\/$/, '');
let products = [], category = '', query = '', selected = null, offset = 0, total = 0;
const mediaURL = value => value?.startsWith('/api/') ? base+value : (value || '');
const more = document.createElement('button');more.className='secondary';more.textContent='Carregar mais';more.hidden=true;$('#grid').after(more);more.onclick=()=>search(true);
const dialog = $('#product-dialog');
const escapeHTML = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path){const r=await fetch(base+path);if(!r.ok)throw new Error('API');return r.json()}
function toast(text){$('#toast').textContent=text;$('#toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').hidden=true,4500)}
function render(){
 const list=products;
 $('#count').textContent=`${total} produtos e coleções${query?' para “'+query+'”':''}`;
 $('#empty').hidden=total>0;more.hidden=products.length>=total;
 $('#empty h3').textContent=$('#sort').value==='popular'?'Ainda não há acessos registrados':'Nenhum produto encontrado';
 $('#grid').innerHTML=list.map(p=>`<button class="card" data-product="${escapeHTML(p.id||p.code)}" aria-label="Abrir mídias de ${escapeHTML(p.name)}"><div class="card-image"><img src="${escapeHTML(mediaURL(p.images[0]?.thumbnail||p.videos[0]?.thumbnail))}" alt="${escapeHTML(p.name)}" loading="lazy"></div><div class="card-meta"><span class="code">${p.code?'CÓD. '+escapeHTML(p.code):'COLEÇÃO'}</span><h3>${escapeHTML(p.name)}</h3><span class="card-category">${escapeHTML(p.category)} · ${escapeHTML(p.line)}</span><div class="card-bottom"><span>${p.images.length} fotos · ${p.videos.length} vídeos</span><b>Ver mídias ↗</b></div></div></button>`).join('');
 document.querySelectorAll('[data-product]').forEach(b=>b.onclick=()=>openProduct(b.dataset.product));
 document.querySelectorAll('.card-image img').forEach(img=>img.onerror=()=>{img.hidden=true;const note=document.createElement('span');note.textContent='Ver arquivos';img.parentElement.append(note)});
}
let requestId=0;
async function search(append=false){
 const id=++requestId;$('#error').hidden=true;more.disabled=true;
 if(!append){offset=0;products=[];$('#grid').innerHTML='';$('#count').textContent='Buscando…';more.hidden=true;}
 try{
  const data=await api('/api/search?q='+encodeURIComponent(query)+'&offset='+offset+'&limit=24&sort='+$('#sort').value);
  if(id!==requestId)return;
  products=append?[...products,...data.results]:data.results;total=data.total;offset=products.length;
  $('.demo-badge').textContent=data.source==='onedrive'?'ONEDRIVE · CATÁLOGO REAL':'CATÁLOGO DEMONSTRATIVO';
  $('.demo-badge').title=data.synced_at?'Atualizado em '+new Date(data.synced_at).toLocaleString('pt-BR'):'';
  render();
 }catch{if(id!==requestId)return;$('#empty').hidden=true;$('#error').hidden=false;$('#count').textContent='Catálogo indisponível'}
 finally{if(id===requestId)more.disabled=false}
}
function setCategory(value){category=value;render()}
async function init(){try{const cats=await api('/api/categories');$('#filters').innerHTML=['',...cats].map(c=>`<button class="filter" data-category="${escapeHTML(c)}">${escapeHTML(c||'Todos os produtos')}</button>`).join('');$('#side-categories').innerHTML=cats.map(c=>`<button class="category-side" data-category="${escapeHTML(c)}">${escapeHTML(c)}</button>`).join('');document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>setCategory(b.dataset.category));await search();const code=new URLSearchParams(location.search).get('produto');if(code)await openProduct(code)}catch{$('#error').hidden=false;$('#count').textContent='Catálogo indisponível'}}
async function openProduct(code){try{selected=await api('/api/products/'+encodeURIComponent(code));$('#product-name').textContent=selected.name;$('#product-category').textContent=selected.category+' / '+selected.line;$('#product-code').textContent=selected.code?'Código '+selected.code:'Coleção de mídias';$('#product-description').textContent=selected.description;$('#reference').textContent=selected.reference||'Não informada';$('#ean').textContent=selected.ean||'Não informado';$('#detail-image').hidden=!selected.images.length;$('#detail-image').src=mediaURL(selected.images[0]?.thumbnail);$('#detail-image').onerror=()=>$('#detail-image').hidden=true;$('#detail-image').alt=selected.name;$('#photo-count').textContent=selected.images.length;$('#video-count').textContent=selected.videos.length;$('#document-count').textContent=selected.documents?.length||0;showMedia(selected.images.length?'images':selected.videos.length?'videos':'documents');if(!dialog.open)dialog.showModal();fetch(base+'/api/products/'+encodeURIComponent(selected.id||selected.code)+'/view',{method:'POST'}).catch(()=>{})}catch{toast('Não foi possível abrir este produto.')}}
function showMedia(type){
 document.querySelectorAll('[data-media]').forEach(b=>b.classList.toggle('selected',b.dataset.media===type));
 const files=selected[type]||[];
 $('#media-content').innerHTML=files.length?files.map(f=>`<div class="file-row"><span>${escapeHTML(f.file)}</span><a href="${escapeHTML(mediaURL(f.url))}" target="_blank" rel="noopener">Visualizar ↗</a><a href="${escapeHTML(mediaURL(f.download||f.url))}" target="_blank" rel="noopener">Baixar ↓</a></div>`).join(''):'<p class="muted">Nenhum arquivo deste tipo disponível.</p>';
}
$('#search-form').onsubmit=e=>{e.preventDefault();query=$('#search').value.trim();search()};
$('#search').oninput=()=>{clearTimeout(search.timer);search.timer=setTimeout(()=>{query=$('#search').value.trim();search()},250)};
$('#sort').onchange=()=>search();
$('#clear').onclick=()=>{category='';query='';$('#search').value='';search()};$('#retry').onclick=init;
document.querySelectorAll('[data-query]').forEach(b=>b.onclick=()=>{query=b.dataset.query;category='';$('#search').value=query;search()});
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-view]').forEach(n=>n.classList.toggle('active',n===b));$('#section-title').textContent=b.dataset.view==='latest'?'Novidades':b.dataset.view==='popular'?'Mais acessados':'Todos os produtos';$('#sort').value=b.dataset.view==='popular'?'popular':'recent';query='';category='';$('#search').value='';search()});
document.querySelectorAll('[data-media]').forEach(b=>b.onclick=()=>showMedia(b.dataset.media));
$('#close-dialog').onclick=()=>dialog.close();dialog.onclick=e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}};
function productURL(){const url=new URL(location.href);url.search='';url.searchParams.set('produto',selected.id||selected.code);return url.href}
$('#copy-link').onclick=async()=>{try{await navigator.clipboard.writeText(productURL());toast('Link copiado. Na prévia local, ele funciona neste computador.')}catch{toast('Não foi possível copiar o link neste navegador.')}};
$('#whatsapp').onclick=()=>{if(['127.0.0.1','localhost'].includes(location.hostname)){toast('O compartilhamento por WhatsApp ficará disponível após a publicação.');return}window.open('https://wa.me/?text='+encodeURIComponent(selected.name+' — '+productURL()),'_blank','noopener')};
init();
