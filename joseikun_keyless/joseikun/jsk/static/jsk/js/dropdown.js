[].slice.call(document.querySelectorAll('.dropdown .nav-link')).forEach(function(el){
  el.addEventListener('click', onClick, false);
});

function onClick(e){
  e.preventDefault();
  var el = this.parentNode;
  el.classList.contains('show-submenu') ? hideSubMenu(el) : showSubMenu(el);
}

function showSubMenu(el){
  el.classList.add('show-submenu');
  document.addEventListener('click', function onDocClick(e){
      // e.preventDefault();sampleでリンクが飛べないように制限できる。
      if(el.contains(e.target)){
          return;
      }
      document.removeEventListener('click', onDocClick);
      hideSubMenu(el);
  });
}

function hideSubMenu(el){
  el.classList.remove('show-submenu');
}

var flag = false;
var count;
// var one = false;
function tag_display(counter){
  // var last_tag_table = document.getElementsByClassName("tag_table")[count];
  var tag_table = document.getElementsByClassName("tag_table")[counter-1];
  if(flag){
    tag_table.style.display = 'none';
    flag = false;
  }else{
    // if (one){
    //   last_tag_table.style.display = 'none';
    // }
    tag_table.style.display = 'table-row';
    flag = true;
    // one = true;
    // count = counter-1;
    }
}