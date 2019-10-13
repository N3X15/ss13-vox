# I hate javascript, especially this broke-ass edition of it. So, I use coffeescript to make the hell more bearable. - N3X
# The ES5 output is run through babel so that (hopefully) we get working IE8 support.

# Max number of phrase IDs.
MAX_WORDS = 30

# jQuery holders
$errPane = null
$resetButton = null
$submitButton = null
$wordlen = null
$words = null

# POLYFILL for Array.prototype.filter
unless Array::filter
  Array::filter = (callback) ->
    element for element in this when callback(element)

addError = (message) ->
  $errPane.append $('<li>').text(message)
  return

###
# Get rid of zero-length entries in the wordlist.
# effectively words=words.filter(word => word && word.length > 0);
# but LOL IE8
###
removeEmpties = (arr) ->
  w for w in arr when w and w.length > 0

###
# A unit test, kinda.
###
testRemoveEmpties = ->
  input = ['a', null, undefined, 2, 'c']
  expected = ['a', 2, 'c']
  actual = removeEmpties input
  console.assert expected == output, expected, output
  return

validate = ->
  v = $words.val()
  # Clear previous errors.
  $errPane.html ''
  # Make sure there's SOMETHING in the textbox.
  if v.length <= 0
    # Update wordcount.
    $wordlen.text '0/' + MAX_WORDS.toString()
    $wordlen.css 'color', '#ff0000'
    # Throw error.
    addError 'Empty field.'
    return false
  words = removeEmpties v.split(' ')
  word = ''
  errored = false
  i = 0
  # Update word counter
  $wordlen.text words.length.toString() + '/' + MAX_WORDS.toString()
  $wordlen.css 'color', if words.length > 0 and words.length < MAX_WORDS then '#cccccc' else '#ff0000'
  # Check word count
  if words.length < 1
    addError 'At least one word is required.'
    return false
  if words.length > MAX_WORDS
    addError 'Too many words, maximum is ' + MAX_WORDS.toString() + '.'
    return false
  # Check if the words are in our list.
  for word in words
    # God I wish we had `in`
    if window.availableWords.indexOf(word) == -1
      addError 'Word "' + word + '" does not exist in the voicepack. Use another word.'
      errored = true
    i++
  !errored

# Once the document initializes...
$(document).ready ->
  # Hook into all our needed elements.
  $errPane = $('#errors')
  $submitButton = $('#submit')
  $resetButton = $('#reset')
  $wordlen = $('#wordcount')
  # Set up autocomplete
  # Note: /vg/ uses a fucking ancient version of jQuery, so we don't get on() and friends.
  $words = $('#words').autocomplete(
    lookup: window.availableWords
    delimiter: ' '
    onSelect: (a) ->
      $submitButton.prop 'disabled', !validate()
      return
  ).keyup((e) ->
    $submitButton.prop 'disabled', !validate()
    return
  )
  $submitButton.click (e) ->
    words = removeEmpties $words.val().split(' ')
    if validate()
      window.location = '?src=' + airef + ';play_announcement=' + words.join('+')
    return
  $resetButton.click (e) ->
    $words.val ''
    validate()
    return
  $submitButton.prop 'disabled', !validate()
  return
