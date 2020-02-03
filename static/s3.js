// Following code comes from django-s3file. It is copied here
// because it is not possible to customize upload.
// Reference: https://github.com/codingjoe/django-s3file

'use strict';

(() => {
  // Provides django-like error alerts.
  function errorAlert (message) {
    return (
      '<div role="alert" class="alert alert-danger">' +
      '   <ul class="errorlist"><li>' + message + '</li></ul>' +
      '</div>'
    );
  }

  $('#form').on('progress', function (event) {
    const progress = parseInt(event.detail.progress * 100)
    $('.progress-bar')
      .attr('aria-valuenow', progress)
      .css('width', `${progress}%`)
      .html(`${progress}%`)
  })

  function hasConstructsChecked () {
    return (
      $('.construct.bg-success').length > 0
      || $('#id_no_constructs').prop('checked')
    )
  }

  function hasStudentsChecked () {
    return $('.student.bg-warning').length > 0
  }

  function hasNoDate () {
    return $('#id_observation_date').val() == ""
  }

  function constructsErrorHtml () {
    return errorAlert('You must choose at least one learning construct for the observation')
  }

  function studentsErrorHtml () {
    return errorAlert('You must choose at least one student for the observation')
  }

  function requiredErrorHtml () {
    return errorAlert('This field is required.')
  }

  // Client side validation is required due to S3 direct upload. It is coupled
  // with server side validation to provide consistency.
  function is_valid_form (form) {
    $('.alert').remove()
    let isValid = true

    if (!hasConstructsChecked ()) {
      $(constructsErrorHtml ()).insertBefore("#constructs-choices");
        isValid = false
    }

    if (!hasStudentsChecked ()) {
      $(studentsErrorHtml ()).insertBefore('#student-empty-frame')
        isValid = false
    }

    if (hasNoDate ()) {
      $(requiredErrorHtml ()).insertBefore('#date-frame')
        isValid = false
    }

    return isValid;
  }

  function parseURL (text) {
    const xml = new window.DOMParser().parseFromString(text, 'text/xml')
    const tag = xml.getElementsByTagName('Key')[0]
    return decodeURI(tag.childNodes[0].nodeValue)
  }

  function addHiddenInput (body, name, form) {
    const key = parseURL(body)
    const input = document.createElement('input')
    input.type = 'hidden'
    input.value = key
    input.name = name
    form.appendChild(input)
  }

  function waitForAllFiles (form) {
    if (window.uploading !== 0) {
      setTimeout(() => {
        waitForAllFiles(form)
      }, 100)
    } else {
      window.HTMLFormElement.prototype.submit.call(form)
    }
  }

  function request (method, url, data, fileInput, file, form) {
    file.loaded = 0
    return new Promise((resolve, reject) => {
      const xhr = new window.XMLHttpRequest()
      xhr.open(method, url)
      xhr.onload = () => {
        if (xhr.status === 201) {
          resolve(xhr.responseText)
        } else {
          reject(xhr.statusText)
        }
      }

      xhr.upload.onprogress = function (e) {
        var diff = e.loaded - file.loaded
        form.loaded += diff
        fileInput.loaded += diff
        file.loaded = e.loaded
        var defaultEventData = {
          currentFile: file,
          currentFileName: file.name,
          currentFileProgress: Math.min(e.loaded / e.total, 1),
          originalEvent: e
        }
        form.dispatchEvent(new window.CustomEvent('progress', {
          detail: Object.assign({
            progress: Math.min(form.loaded / form.total, 1),
            loaded: form.loaded,
            total: form.total
          }, defaultEventData)
        }))
        fileInput.dispatchEvent(new window.CustomEvent('progress', {
          detail: Object.assign({
            progress: Math.min(fileInput.loaded / fileInput.total, 1),
            loaded: fileInput.loaded,
            total: fileInput.total
          }, defaultEventData)
        }))
      }

      xhr.onerror = () => {
        reject(xhr.statusText)
      }
      xhr.send(data)
    })
  }

  function uploadFiles (form, fileInput, name) {
    const url = fileInput.getAttribute('data-url')
    fileInput.loaded = 0
    fileInput.total = 0

    const promises = Array.from(fileInput.files).map((file) => {
      form.total += file.size
      fileInput.total += file.size
      const s3Form = new window.FormData()
      Array.from(fileInput.attributes).forEach(attr => {
        let name = attr.name
        if (name.startsWith('data-fields')) {
          name = name.replace('data-fields-', '')
          s3Form.append(name, attr.value)
        }
      })
      s3Form.append('success_action_status', '201')
      s3Form.append('Content-Type', file.type)
      s3Form.append('file', file)
      return request('POST', url, s3Form, fileInput, file, form)
    })
    Promise.all(promises).then((results) => {
      results.forEach((result) => {
        addHiddenInput(result, name, form)
      })

      const input = document.createElement('input')
      input.type = 'hidden'
      input.name = 's3file'
      input.value = fileInput.name
      fileInput.name = ''
      form.appendChild(input)
      window.uploading -= 1
    }, (err) => {
      console.log(err)
      fileInput.setCustomValidity(err)
      fileInput.reportValidity()
    })
  }

  function clickSubmit (e) {
    let submitButton = e.target
    let form = submitButton.closest('form')
    const submitInput = document.createElement('input')
    submitInput.type = 'hidden'
    submitInput.value = submitButton.value || '1'
    submitInput.name = submitButton.name
    form.appendChild(submitInput)
  }

  function uploadS3Inputs (form) {
    window.uploading = 0
    form.loaded = 0
    form.total = 0
    const inputs = form.querySelectorAll('.s3file')
    Array.from(inputs).forEach(input => {
      window.uploading += 1
      uploadFiles(form, input, input.name)
    })
    waitForAllFiles(form)
  }

  $( document ).ready(function() {
    let forms = Array.from(document.querySelectorAll('.s3file')).map(input => {
      return input.closest('form')
    })
    forms = new Set(forms)
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        e.preventDefault()

        // Do not validate form when draft observation is saved.
        if ($('#draft-hidden').val() === 'True') {
          document.getElementsByTagName("body")[0].style = 'background-color: rgba(211,211,211,3);';
          document.getElementById('loader-frame').style.visibility = "visible";

          if (!window.draft_update) {
            uploadS3Inputs(e.target)
          } else {
            window.HTMLFormElement.prototype.submit.call(form)
          }
        } else if (is_valid_form(form)) {
          document.getElementsByTagName("body")[0].style = 'background-color: rgba(211,211,211,3);';
          document.getElementById('loader-frame').style.visibility = "visible";
          
          if ($('#draft-hidden').val() !== 'True' || !window.draft_update) {
            uploadS3Inputs(e.target)
          } else {
            window.HTMLFormElement.prototype.submit.call(form)
          }
        }
      })

      let submitButtons = form.querySelectorAll('input[type=submit], button[type=submit]')
      Array.from(submitButtons).forEach(submitButton => {
        submitButton.addEventListener('click',  clickSubmit)
      })
    })
  })
})()
