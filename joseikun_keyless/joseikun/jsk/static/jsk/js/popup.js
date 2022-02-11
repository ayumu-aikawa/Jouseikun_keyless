function popup(file_name,file_delete_pk){
  var popupWin = document.createElement("div");
  popupWin.id = "popupWin";

  var pop_win = document.createElement("div");
  pop_win.className = "pop-win";


  var message = document.createElement("p");
  message.id = "message";
  message.textContent = `${file_name}を削除しますか？`;

  var yes_button = document.createElement("a");
  yes_button.id = "ok";
  yes_button.className = "button";
  yes_button.textContent = "はい";
  // yes_button.href =  file_delete_url;
  
  yes_button.href = `/file_delete/${file_delete_pk}`;


  var no_button = document.createElement("button");
  no_button.id = "no";
  no_button.className = "button";
  no_button .textContent = "いいえ";
  no_button.onclick = function close(){popupWin.style.display = "none";};

  
  
  pop.appendChild(popupWin);
  popupWin.appendChild(pop_win);
  pop_win.appendChild(message);
  pop_win.appendChild(yes_button);
  pop_win.appendChild(no_button);
  
  popupWin.style.display = 'flex';

}


function user_delete_popup(){
  const close =  document.getElementById('user_delete_no');
  const popupWin = document.getElementById("user_delete_popupWin");
  popupWin.style.display = 'flex';
  close.addEventListener('click', () =>{
    popupWin.style.display = 'none';
  })
}

function log_out_pop(){
  var popupWin = document.createElement("div");
  popupWin.id = "popupWin";

  var pop_win = document.createElement("div");
  pop_win.className = "pop-win";


  var message = document.createElement("p");
  message.id = "message";
  message.textContent = "ログアウトしますか？";

  var yes_button = document.createElement("a");
  yes_button.id = "ok";
  yes_button.className = "button";
  yes_button.textContent = "はい";
  // yes_button.href =  file_delete_url;
  
  yes_button.href="/logout";

  var no_button = document.createElement("button");
  no_button.id = "no";
  no_button.className = "button";
  no_button .textContent = "いいえ";
  no_button.onclick = function close(){popupWin.style.display = "none";};

  
  
  pop.appendChild(popupWin);
  popupWin.appendChild(pop_win);
  pop_win.appendChild(message);
  pop_win.appendChild(yes_button);
  pop_win.appendChild(no_button);
  
  popupWin.style.display = 'flex';

}