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

  function request (method, url, data) {
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
      xhr.onerror = () => {
        reject(xhr.statusText)
      }
      xhr.send(data)
    })
  }

  function uploadFiles (form, fileInput, name) {
    const url = fileInput.getAttribute('data-url')
    const promises = Array.from(fileInput.files).map((file) => {
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
      return request('POST', url, s3Form)
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
    const inputs = form.querySelectorAll('.s3file')
    Array.from(inputs).forEach(input => {
      window.uploading += 1
      uploadFiles(form, input, input.name)
    })
    waitForAllFiles(form)
  }

  document.addEventListener('DOMContentLoaded', () => {
    let forms = Array.from(document.querySelectorAll('.s3file')).map(input => {
      return input.closest('form')
    })
    forms = new Set(forms)
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        // Thera are two types of submit in observation form.
        // First one has name `use_recent_observation` which is used to set media
        // of the previous observation. On such request server responds with
        // redirection to `GET /observation/`` with initialized form.
        // Second one is a submit whick firslty upload media directly to S3
        // and after that submits data to web server.
        if (e.explicitOriginalTarget.name != "use_recent_observation") {
          e.preventDefault()
          if (is_valid_form(form)) {
            document.getElementById('loader-frame').style.visibility = "visible";
            uploadS3Inputs(e.target)
          }
        }
      })
      let submitButtons = form.querySelectorAll('input[type=submit], button[type=submit]')
      Array.from(submitButtons).forEach(submitButton => {
        submitButton.addEventListener('click',  clickSubmit)
      }
      )
    })
  })
})()
