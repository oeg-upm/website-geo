/*
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
  Ontology Engineering Group
        http://www.oeg-upm.net/
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
  Copyright (C) 2017 Ontology Engineering Group.
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
  GeoLinkeddata Open Data Portal is licensed under a
  Creative Commons Attribution-NC 4.0 International License.
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
*/

// Handler for input radio event
var resetForm = function resetForm(e)
{
    // Stop bubble
    stopPropagation(e);

    // Reset form values
    document['getElementById']('file-form')['reset']();

    // Hide disclaimer
    var fileDisclaimer = document['getElementById']('file-disclaimer');
    if (fileDisclaimer !== null)
    {
        if (fileDisclaimer['className'] === '')
            fileDisclaimer['className'] = 'hidden';
    }

    // Hide errors / info
    var fileError = document['getElementById']('file-error');
    var fileInfo = document['getElementById']('file-info');
    if (fileError !== null && fileError['className'] === '')
        fileError['className'] = 'hidden';
    if (fileInfo !== null && fileInfo['className'] === '')
        fileInfo['className'] = 'hidden';

    // Change icon element
    var iconFile = document['getElementById']('file-icon');
    iconFile['className'] = 'fa fa-angle-double-up';

    // Change status of target
    var target = e['target'];
    target['checked'] = true;

};

// Handler for input file event
var readFile = function readFile(e)
{

    // Stop bubble
    stopPropagation(e);

    // Get target of event
    var target = e['target'];

    // Check if file was selected
    if(target['files'] && target['files'].length > 0 )
    {
        // Get file info
        var fileInformation = target['files'][0];

        // Change icon element
        var iconFile = document['getElementById']('file-icon');
        var radioValue = document['querySelector'](
            'input[type="radio"]:checked'
        )['value'];
        var iconNewFile = '';
        if (radioValue === 'shp' &&
            fileInformation['type'] === 'application/zip')
        {
            iconNewFile = 'fa fa-file-archive-o';
        }
        else if (radioValue === 'kml' &&
            fileInformation['type'] === 'application/vnd.google-earth.kml+xml')
        {
            iconNewFile = 'fa fa-file-text-o';
        }
        else if (radioValue === 'geojson' &&
            fileInformation['type'] === 'application/json')
        {
            iconNewFile = 'fa fa-file-code-o';
        }
        else if (radioValue === 'csv' &&
            fileInformation['type'] === 'text/csv')
        {
            iconNewFile = 'fa fa-file-excel-o'
        }
        else iconNewFile = 'fa fa-close';
        iconFile['className'] = iconNewFile;

        // Show disclaimer
        var fileDisclaimer = document['getElementById']('file-disclaimer');
        if (fileDisclaimer !== null)
        {
            if (fileDisclaimer['className'] === 'hidden')
                fileDisclaimer['className'] = '';
        }

        // Show error /name if it is necessary
        var fileError = document['getElementById']('file-error');
        var fileInfo = document['getElementById']('file-info');
        if (iconNewFile === 'fa fa-close')
        {
            if (fileError !== null && fileError['className'] === 'hidden')
                fileError['className'] = '';
            if (fileInfo !== null && fileInfo['className'] === '')
                fileInfo['className'] = 'hidden';
        }
        else
        {
            if (fileError !== null && fileError['className'] === '')
                fileError['className'] = 'hidden';
            if (fileInfo !== null)
            {
                if (fileInfo['className'] === 'hidden')
                    fileInfo['className'] = '';
                var fileName = fileInformation['name'];
                var fileExt = fileName.split('.').pop();
                if (fileName['length'] > 21)
                    fileName = fileName.slice(
                        0, 21 - fileExt.length
                    ) + ' ...' + fileExt;
                fileInfo['innerHTML'] = fileName;
            }
        }
    }
};

// Execute when DOM is Ready
ready(function()
{
    // Assign handler to input
    var inputFile = document['getElementById']('file-chooser');
    if (inputFile !== null)
    {
        addListener(inputFile, 'change', readFile);
    }

    // Assign handler to radio
    var inputRadio = document['getElementsByClassName']('file-radio');
    if (inputRadio !== null)
    {
        for (var i = 0; i < inputRadio.length; i++)
        {
            addListener(inputRadio[i], 'change', resetForm);
        }
    }

});