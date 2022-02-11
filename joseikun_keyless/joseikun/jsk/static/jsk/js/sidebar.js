function check(){
  check_box = document.getElementById("openSidebarMenu");
  // check_box = document.getElementsByClassName("openSidebarMenu");
  if (check_box.checked){
    // console.log("チェックされています。");
    document.getElementById("openSidebarMenu").checked = false;
  }else{
    // console.log("チェックされていません。");
  }
}