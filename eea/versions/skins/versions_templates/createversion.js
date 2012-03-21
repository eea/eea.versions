var latestVersionUrl = "";

function checkLatestVersion(repeat){
  jQuery.ajax({
      url     : context_url+"/getLatestVersionUrl",
      success : function(data){
        if (data == latestVersionUrl){
          if (repeat){ // don't start an uncontrolled number of timeouts
            setTimeout("checkLatestVersion(false)", 5000);
          }
        } else {
          jQuery.fancybox(
            '<div style="text-align:center;width:250px;">'+
            '<span>The new version was created, you can see '+
            'it by clicking on the following link:</span><br/><br/>'+
            '<a href="'+data+'">'+data+'</a></div>',
            {'modal':false}
          );
        }
      }
  });
}

function startCreationOfNewVersion(){
  jQuery.ajax({ // get the latest version url, before new version
      url     : context_url+"/getLatestVersionUrl",
      success : function(data){
        latestVersionUrl = data;
        jQuery.fancybox('<div style="text-align:center;width:250px;"><span>'+
          'Please wait, a new version is being created.</span><br/><br/><img '+
          'src="++resource++jqzoom/zoomloader.gif"/></div>', 
          {'modal':true}
        );
        jQuery.ajax({
            url     : context_url+"/@@createVersionAjax",
            success : function(data) {
              if (data.indexOf("SEEURL")===0){
                  var url = data.replace("SEEURL:", ""); 
                  window.location.href = url;
              } else {
                  checkLatestVersion(true);
              }
            },
            error   : function(xhr, ajaxOptions, thrownError){
              if (xhr.status == 504){
                checkLatestVersion(true);
              }
              else {
                jQuery.fancybox('<div style="text-align:center;width:250px;">'+
                  '<span>An internal error occured, please contact the administrator'+
                  '</span></div>',
                  {'modal':false}
                );
              }
            }
        });
      }
  });
}
