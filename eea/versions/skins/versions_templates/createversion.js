var latestVersionUrl = "";

function checkLatestVersion(repeat) {
    var timeout_count = 0,
        timeout_step = 5000,
        timeout_max = timeout_step * 24; // max timeout of 2 minutes
    jQuery.ajax({
      url     : context_url + "/@@getLatestVersionUrl",
      success : function(data) {
        if (data == latestVersionUrl) {
          timeout_count += timeout_step;
          if (repeat) {
          jQuery.fancybox(
            '<div style="text-align:center;width:250px;">' +
            '<strong>The operation will take some time.</strong><br/><br/>' +
            '<span>The new version will be created shortly. Please refresh ' +
            'this page after a few minutes and check for the new version ' +
            'notification message.</span><br/><br/></div>',
            {'modal': false}
          );
          }
          else if (timeout_count == timeout_max) {
            setTimeout(function(){ return checkLatestVersion(false) },
                       timeout_step);
          } else {
            setTimeout(function(){ return checkLatestVersion(true) },
                       timeout_step);
          }
        } else {
          jQuery.fancybox(
            '<div style="text-align:center;width:250px;">' +
            '<span>The new version was created, you can see ' +
            'it by clicking on the following link:</span><br/><br/>' +
            '<a href="' + data + '">' + data + '</a></div>',
            {'modal': false}
          );
        }
      }
  });
}

function startCreationOfNewVersion() {
  var timeout_codes = [502, 503, 504];
  jQuery.ajax({ // get the latest version url, before new version
      url     : context_url + "/@@getLatestVersionUrl",
      success : function(data) {
        latestVersionUrl = data;
        jQuery.fancybox('<div style="text-align:center;width:250px;"><span>' +
          'Please wait, a new version is being created.</span><br/><br/><img ' +
          'src="++resource++jqzoom/zoomloader.gif"/></div>',
          {'modal': true}
        );
        jQuery.ajax({
            url     : context_url + "/@@createVersionAjax",
            type    : "POST",
            success : function(data) {
              if (data.indexOf("SEEURL")===0) {
                  var url = data.replace("SEEURL:", "");
                  window.location.href = url;
              } else {
                  checkLatestVersion(true);
              }
            },
            error   : function(xhr, ajaxOptions, thrownError) {
              if (jQuery.inArray(xhr.status, timeout_codes) != -1) {
                // timeout, check if the new versions was created
                checkLatestVersion(true);
              }
              else {
                jQuery.fancybox('<div style="text-align:center;width:250px;">' +
                  '<span>An internal error occured, please contact the administrator' +
                  '</span></div>',
                  {'modal': false}
                );
              }
            }
        });
      }
  });
}

jQuery(document).ready(function($) {
    var $show_older_versions = $(".showOlderVersions"),
        $previous_versions = $("#previous-versions");

    $previous_versions.css('display', 'none');

    $show_older_versions.click( function( e ) {
        $previous_versions.slideToggle();
        e.preventDefault();
    });
});
