(function(){
  document.documentElement.classList.add('js');
  var b=document.querySelector('.nav-toggle'),n=document.getElementById('nav');
  if(!b||!n)return;
  b.addEventListener('click',function(){
    var open=n.classList.toggle('open');
    b.setAttribute('aria-expanded',open?'true':'false');
  });
})();
