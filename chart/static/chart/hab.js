function expand(id){
      var objGroup = document.getElementById(id);
      if(objGroup.style.display=="block"){objGroup.style.display = "none";}
      else{objGroup.style.display = "block";}      
}

function detail(id){
      var objGroup = document.getElementById(id);
      if(objGroup.style.display=="inline-block"){objGroup.style.display = "none";}
      else{objGroup.style.display = "inline-block";}      
}

function handler( event ) {
      var target = $( event.target );
      if ( target.is( "li" ) ) {
        target.children().toggle();
      }
    }
    $( "ul" ).click( handler ).find( "ul" ).hide();
