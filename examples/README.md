# Turkle Template Guide #

## How Turkle renders Templates ##

The HTML template code that you write should not be a complete HTML
document with `head` and `body` tags.  Turkle renders the page for a
Task by inserting your HTML template code into an HTML `form` element
in the body of an HTML document.  The document looks like this:

``` html
<!DOCTYPE html>
<html>
  <head>
    <title></title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  </head>
  <body>
    <form name="mturk_form" method="post" id="mturk_form"
          target="_parent" action='/some/submit/url'>
      <!-- YOUR HTML IS INSERTED HERE -->
      {% if not project_html_template.has_submit_button %}
      <input type="submit" id="submitButton" value="Submit" />
      {% endif %}
    </form>
  </body>
</html>
```

Turkle displays the combined HTML document in an iframe, so that your
code is isolated from any CSS and JavaScript libraries used by the
Turkle UI.  If your Project's HTML template code does not include an
HTML 'Submit' button, then Turkle will add a 'Submit' button to the
combined document.

## Template Variables ##

An HTML template includes template variables, which have the form
`${variable_name}`.  The CSV files used to create Task Batches include
a header row with the names of the template variables.  When a Worker
visits a Task web page, the variables in the HTML template will be
replaced with the corresponding values from a row of the CSV file.

If a Project's HTML template file uses template variables named
`${foo}` and `${bar}`:

``` html
  <p>The variable 'foo' has the value: ${foo}</p>
  <p>The variable 'bar' has the value: ${bar}</p>
  <input type="text" name="my_input" />
```

then the CSV input file's header row should have fields named 'foo'
and 'bar':

    "foo","bar"
	"1","one"
	"2","two"

When a Worker views the web page for a Task or Task Assignment, the
template variables will be replaced with the corresponding values from
a row of the CSV file:

``` html
  <p>The variable 'foo' has the value: 1</p>
  <p>The variable 'bar' has the value: one</p>
  <input type="text" name="my_input" />
```

The HTML template can include any HTML form input fields, such as text
boxes, radio buttons, and check boxes.

## JavaScript and CSS ##

JavaScript and CSS can be placed in the template itself or linked to from
another web server. If the users will have access to the Internet, using
public CDNs is an excellent option. Otherwise, a local web server could
be used to host common JavaScript and CSS files.

The `emotion detection` and `image contains` template examples uses
Bootstrap and jQuery. The `translate validate` template uses the
Parsley validation library.

## Serialized Data ##

More sophisticated tasks may require loading or saving serialized data.
For example, a tagging task starts with tokenized text and that may be
saved in JSON or [Concrete](https://github.com/hltcoe/concrete).
In these cases, JavaScript code will deserialize the inputs to render
the template or serialize the output for submission.

As an example, this jQuery-based code serializes output and adds it to
the DOM as an input element:

```javascript
$('input[type="submit"]').on("click", function(event) {
  var output = my_function_that_grabs_output();
  var string = escapeHtml(JSON.stringify(output));
  $("#mturk_form").append('<input name="output" type="hidden" value="' + string + '">');
});
```
The data is then available in the output CSV as JSON as the variable Answer.output.

## Preventing Default Browser Behavior that Frustrates Users ##

Users will accidentally trigger form submission by pressing the Enter
key outside of a text field.  Some browsers use the Backspace key to
trigger the "Back" action.  Users will accidentally navigate away from
the form (discarding their work) if they hit Backspace outside of a
text field.

This jQuery-based code disables the default behavior for the Enter and
Backspace keys when the user is not editing a text field:

```javascript
$(document).ready(function() {
  $(document).on('keydown', function(e) {
    var keyCode = e.keyCode || e.which;

    // Disable use of enter key UNLESS used within a textarea
    if (keyCode == 13 && !$(document.activeElement).is('textarea')) {
      e.preventDefault();
      return false;
    }

    // Disable backspace key outside of input and textarea fields, since some browsers
    // (such as Firefox on Windows) trigger the "Back" action when backspace is pressed
    if (keyCode == 8 && !$(document.activeElement).is('input') && !$(document.activeElement).is('textarea')) {
      e.preventDefault();
      return false;
    }
  });
});
```

## Gotchas ##

Do not include text like this `%{variable}` in your template unless it is 
a variable in your input CSV file. Accidentally adding something like this
in your JavaScript code will cause Turkle's template rendering to modify it.

Do not include a form in your template. The template is inserted into a form
element and a form in a form is invalid HTML.

Because your entire HTML template is wrapped in a form element, the
default behavior for any buttons in your template will be to trigger
form submission.  To prevent a button from submitting the form, use
the CSS "button" class:

``` html
<button class="button">
```

Do not use JavaScript or CSS resources included with Turkle. There is no
guarantee that those resources will be there in the future. 
