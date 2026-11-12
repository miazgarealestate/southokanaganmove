(function(){
  document.documentElement.classList.add('js');
  var b=document.querySelector('.nav-toggle'),n=document.getElementById('nav');
  if(!b||!n)return;
  b.addEventListener('click',function(){
    var open=n.classList.toggle('open');
    b.setAttribute('aria-expanded',open?'true':'false');
  });
})();

(function(){
  // Guide inquiry: /contact/?guide=<slug>&t=<title> fills hidden fields, subject and a starter message.
  var f=document.querySelector('form.form');if(!f)return;
  var q=new URLSearchParams(location.search),g=(q.get('guide')||'').toLowerCase();
  if(!/^[a-z0-9-]{1,60}$/.test(g))return;
  var t=(q.get('t')||'').replace(/[^\w\s,.:&'()\/-]/g,'').slice(0,90);
  var set=function(n,v){var e=f.querySelector('[name="'+n+'"]');if(e)e.value=v;};
  set('guide',g);set('guide_title',t);
  set('_subject','Guide inquiry: '+(t||g)+' (southokanaganmove.ca)');
  var m=f.querySelector('textarea[name="message"]');
  if(m&&!m.value&&t)m.value='I read your guide "'+t+'" and have a question about ';
  var n=document.createElement('p');n.className='note';n.setAttribute('role','status');
  n.textContent='About the guide: '+(t||g);
  f.insertBefore(n,f.firstChild);
})();
