var latestVersionUrl = "";

function checkLatestVersion(){
  jQuery.ajax({url     : context_url+"/getLatestVersionUrl",
      success : function(data){
        if (data == latestVersionUrl){
          setTimeout("checkLatestVersion()", 5000);
        }
        else{
          jQuery.fancybox('<div style="text-align:center;width:250px;">'+
            '<span>The new version was created, you can see'+
            'it by clicking on the following link:</span><br/><br/>'+
            '<a href="'+data+'">'+data+'</a></div>',
            {'modal':false}
          );
        }
      }
  });
}

function startCreationOfNewVersion(){
  jQuery.ajax({
      url     : context_url+"/getLatestVersionUrl",
      success : function(data){
        latestVersionUrl = data;
        jQuery.fancybox('<div style="text-align:center;width:250px;"><span>'+
          'Please wait, a new version is being created.</span><br/><br/><img '+
          'src="++resource++jqzoom/zoomloader.gif"/></div>', 
          {'modal':true}
        );
        jQuery.ajax({url     : context_url+"/@@createVersionAjax",
            success : function() {
              checkLatestVersion();
            },
            error   : function(xhr, ajaxOptions, thrownError){
              if (xhr.status == 504){
                checkLatestVersion();
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
