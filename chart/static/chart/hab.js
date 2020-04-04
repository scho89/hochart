function expandgroup(groupclass){
     var objDiv = document.getElementsByClassName(groupclass);
     if(objDiv.style.display=="block"){ objDiv.style.display = "none"; }
      else{ objDiv.style.display = "block"; }
}

function expand(id){
      var objGroup = document.getElementById(id);
      if(objGroup.style.display=="block"){objGroup.style.display = "none";}
      else{objGroup.style.display = "block"}      
}