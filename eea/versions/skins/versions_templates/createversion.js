var newURL = "";
function checkNewVersion(){
    $.ajax({url     : newURL,
            success : function(){
                $.fancybox('<div style="text-align:center;width:250px;"><span>The new version was created, you can see it by clicking on the following link:</span><br/><br/><a href="'+newURL+'">'+newURL+'</a></div>',{'modal':false});
            },
            error : function(xhr, ajaxOptions, thrownError){
                setTimeout("checkNewVersion()",5000);
            }
    });
}
function startCreationOfNewVersion(){
    $.fancybox('<div style="text-align:center;width:250px;"><span>Please wait, a new version is being created.</span><br/><br/><img src="++resource++jqzoom/zoomloader.gif"/></div>',{'modal':true});
    $.ajax({url     : context_url+"/@@createVersionId",
            success : function(new_obj){
                newURL = parent_url+"/"+new_obj;
                $.ajax({ url : context_url+"/@@justCreateVersion"});
                checkNewVersion();
            }
    });
}

