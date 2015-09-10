/* global document, context_url */
var latestVersionUrl = "";

function checkLatestVersion(repeat) {
    var timeout_count = 0,
        timeout_step = 5000,
        timeout_max = timeout_step * 24; // max timeout of 2 minutes
    jQuery.ajax({
        url: context_url + "/@@getLatestVersionUrl",
        success: function(data) {
            var msg = '<div style="text-align:center;width:250px;">';
            if (data === latestVersionUrl) {
                timeout_count += timeout_step;
                if (repeat) {
                    jQuery.fancybox(
                        msg +
                        '<strong>The operation will take some time.</strong><br/><br/>' +
                        '<span>The new version will be created shortly. Please refresh ' +
                        'this page after a few minutes and check for the new version ' +
                        'notification message.</span><br/><br/></div>',
                        {'modal': false}
                    );
                }
                else if (timeout_count === timeout_max) {
                    setTimeout(function() {
                            return checkLatestVersion(false);
                        },
                        timeout_step);
                } else {
                    setTimeout(function() {
                            return checkLatestVersion(true);
                        },
                        timeout_step);
                }
            } else {
                jQuery.fancybox(
                    msg +
                    '<span>The new version was created, you can see ' +
                    'it by clicking on the following link:</span><br/><br/>' +
                    '<a href="' + data + '">' + data + '</a></div>',
                    {'modal': false}
                );
            }
        }
    });
}

function showFancyboxError() {
    jQuery.fancybox('<div style="text-align:center;width:250px;">' +
        '<span>An internal error occured, please contact the administrator' +
        '</span></div>',
        {'modal': false}
    );
}

function startCreationOfNewVersion() {
    var timeout_codes = [502, 503, 504];
    jQuery.ajax({ // get the latest version url, before new version
        url: context_url + "/@@getLatestVersionUrl"
    }).done(function(data) {
        latestVersionUrl = data;
        var versionChecks = Math.floor((Math.random() * 100) + 1);
        jQuery.ajax({
            type: "POST",
            url: context_url + "/@@ajaxVersion?check=" + versionChecks
        }).done(function(data) {
            if (data === "NO VERSION IN PROGRESS") {
                jQuery.ajax({
                    type: "POST",
                    url: context_url + "/@@ajaxVersion?startVersioning=True"
                }).done(function() {
                    jQuery.fancybox('<div style="text-align:center;width:250px;"><span>' +
                        'Please wait, a new version is being created.</span><br/><br/><img ' +
                        'src="++resource++jqzoom/zoomloader.gif"/></div>',
                        {'modal': true}
                    );
                    jQuery.ajax({
                        url: context_url + "/@@createVersionAjax",
                        type: "POST"
                    }).done(function(data) {
                        if (data.indexOf("SEEURL") === 0) {
                            var url = data.replace("SEEURL:", "");
                            window.location.href = url;
                        } else {
                            checkLatestVersion(true);
                        }
                    }).fail(function(xhr, ajaxOptions, thrownError) {
                        if (jQuery.inArray(xhr.status, timeout_codes) !== -1) {
                            // timeout, check if the new versions was created
                            checkLatestVersion(true);
                        }
                        else {
                            showFancyboxError();
                        }
                    });
                }).fail(function() {
                    showFancyboxError();
                });
            }
            if (data === "IN PROGRESS") {
                window.setTimeout(function() {
                    jQuery.fancybox(
                        '<div style="text-align:center;width:250px;">' +
                        '<strong>A new version creation is already in progress.</strong><br/><br/>' +
                        '<span>Please refresh ' +
                        'this page after a few minutes and check for the new version ' +
                        'notification message.</span><br/><br/></div>',
                        {'modal': false}
                    );
                }, 2000);
            }
        }).fail(function() {
            showFancyboxError();
        });
    });
}
