(function (mngweb, $, undefined) {
  'use strict';

  var portal = mngweb.portal || {};

  /*
  portal: public methods, properties
  */

  portal.hideMetaFields = function (context) {
    $(context).find('.meta-data-lab, .meta-data-host, .meta-data-environmental, .meta-data-further-details').hide();
  };

  portal.clearMetaFields = function (context) {
    $(context).find('.meta-data-lab, .meta-data-host, .meta-data-environmental').find('input, select').val('');
  };

  portal.showMetaFields = function (context) {
    var studyType, fdHelpText;
    context = $(context);
    studyType = context.find('select[name="study_type"]').val();
    portal.hideMetaFields(context);
    switch (studyType) {
      case 'Lab':
        context.find('.meta-data-lab, .meta-data-further-details').show();
        fdHelpText = $('#lab-fd-help-text').text();
        break;
      case 'Host':
        context.find('.meta-data-host, .meta-data-further-details').show();
        fdHelpText = $('#host-fd-help-text').text();
        break;
      case 'Environmental':
        context.find('.meta-data-environmental, .meta-data-further-details').show();
        fdHelpText = $('#env-fd-help-text').text();
        break;
    }
    context.find('input[name="further_details"]').siblings('.help-block').text(fdHelpText);
  };

  /*
  'Environmental sample type' typeahead
  */
  portal.envSampleTypes = new Bloodhound({
    datumTokenizer: Bloodhound.tokenizers.whitespace,
    queryTokenizer: Bloodhound.tokenizers.whitespace,
    prefetch: '/portal/environmentalsampletype/typeahead/'
  });
  function envSampleTypesWithDefaults(q, sync) {
    if (q === '') {
      sync(envSampleTypes.index.all());
    }

    else {
      envSampleTypes.search(q, sync);
    }
  }
  $('.environmentalsampletype-typeahead input').typeahead({
    hint: true,
    highlight: true,
    minLength: 0
  },
  {
    name: 'envSampleTypes',
    limit: Infinity,
    source: envSampleTypesWithDefaults,
  });

  /*
  'Host sample type' typeahead
  */
  var hostSampleTypes = new Bloodhound({
    datumTokenizer: Bloodhound.tokenizers.whitespace,
    queryTokenizer: Bloodhound.tokenizers.whitespace,
    prefetch: '/portal/hostsampletype/typeahead/'
  });
  function hostSampleTypesWithDefaults(q, sync) {
    if (q === '') {
      sync(hostSampleTypes.index.all());
    }

    else {
      hostSampleTypes.search(q, sync);
    }
  }
  $('.hostsampletype-typeahead input').typeahead({
    hint: true,
    highlight: true,
    minLength: 0
  },
  {
    name: 'hostSampleTypes',
    limit: Infinity,
    source: hostSampleTypesWithDefaults,
  });


  /*
  Expose mngweb.portal object
  */

  mngweb.portal = portal;

  /*
  AJAX sample form submission
  */
  $(document).on('submit', 'form.projectline-form', function(event) {
    event.preventDefault();
    mngweb.ajaxForms.formPOST(this, false, function(form) {
      form = $(form);
      var editRow = form.closest('tr');
      var dataRow = form.closest('tr').prev('tr');
      editRow.collapse('hide');
      dataRow.find('td.pl-taxon').text(form.find('input[name="taxon_name"]').val());
      dataRow.find('td.pl-customers-ref').text(form.find('input[name="customers_ref"]').val());
      dataRow.find('button.pl-edit-button')
        .removeClass('btn-warning')
        .addClass('btn-success')
        .html('<i class="fa fa-check"></i> Saved');
    });
  });

  /*
  AJAX sample sheet upload
  */
  $('#sample_sheet_form').on('submit', function(event){
    event.preventDefault();
    $('#upload_progress_modal').modal('show');

    var formData = new FormData();
    var file = document.getElementById('id_file').files[0];
    if (file) {
      formData.append('file', file, file.name);
    }

    $.ajax({
      url: $(this).attr('action'),
      type: 'POST',
      data: formData,
      cache: false,
      dataType: 'json',
      processData: false, // Don't process the files
      contentType: false, // Set content type to false as jQuery will tell the server its a query string request

      success: function(json) {
        $('#upload_progress_modal').modal('hide');
        $('#sample_sheet_success_modal').modal('show');
        setTimeout(function () {
          window.location.href = json.redirect_url;
        }, 500);
      },

      error: function(xhr,errmsg,err) {
        var json = JSON.parse(xhr.responseText);
        var messages, i, m;

        console.log(xhr.status + ': ' + xhr.responseText); // provide a bit more info about the error to the console

        $('#upload_progress_modal').modal('hide');
        if ('messages' in json) {
          $('#sample_sheet_error_list').html('');
          messages = json.messages;
          for (i = 0; i < messages.length; i++) {
            m = messages[i];
            $('#sample_sheet_error_list').append('<li>' + m.message + '</li>');
          }
        }
        $('#sample_sheet_errors_modal').modal('show');
      },
    });
  });

  /*
  jQuery document ready events
  */
  $(document).ready(function () {
    // Study type meta-data fields
    $('select[name="study_type"]').each(function() {
      var context = $(this).parent().parent();
      portal.showMetaFields(context);
    });

    $('select[name="study_type"]').change(function() {
      var context = $(this).parent().parent();
      portal.clearMetaFields(context);
      portal.showMetaFields(context);
    });
  });

})(window.mngweb = window.mngweb || {}, jQuery);