Turkle Template Guide
=====================

How Turkle renders Templates
----------------------------

The HTML template code that you write should not be a complete HTML
document with ``head`` and ``body`` tags.  Turkle renders the page for a
Task by inserting your HTML template code into an HTML ``form`` element
in the body of an HTML document.  The document looks like this::

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

Turkle displays the combined HTML document in an iframe, so that your
code is isolated from any CSS and JavaScript libraries used by the
Turkle UI.  If your Project's HTML template code does not include an
HTML 'Submit' button, then Turkle will add a 'Submit' button to the
combined document.

Template Variables
------------------

An HTML template includes template variables, which have the form
``${variable_name}``.  The CSV files used to create Task Batches include
a header row with the names of the template variables.  When a Worker
visits a Task web page, the variables in the HTML template will be
replaced with the corresponding values from a row of the CSV file.

If a Project's HTML template file uses template variables named
``${foo}`` and ``${bar}``::

    <p>The variable 'foo' has the value: ${foo}</p>
    <p>The variable 'bar' has the value: ${bar}</p>
    <input type="text" name="my_input" />

then the CSV input file's header row should have fields named 'foo'
and 'bar'::

    "foo","bar"
    "1","one"
    "2","two"

When a Worker views the web page for a Task or Task Assignment, the
template variables will be replaced with the corresponding values from
a row of the CSV file::

    <p>The variable 'foo' has the value: 1</p>
    <p>The variable 'bar' has the value: one</p>
    <input type="text" name="my_input" />

The HTML template can include any HTML form input fields, such as text
boxes, radio buttons, and check boxes.

Serialized Data
---------------

More sophisticated tasks may require loading or saving serialized data.
For example, a tagging task starts with tokenized text and that may be
saved in JSON or Concrete_.

Here is a sample CSV file that contains a JSON array::

    "json_array"
    "[3,6,9]"

JavaScript code in a template can access this JSON array using::

     <script>
       var a = ${json_array};
       // a[0]=3, a[1]=6, a[2]=9
     </script>

Please note that when you are passing in JSON data through template
variables, you should NOT use ``JSON.parse()`` to deserialize the data.
Turkle replaces the template variables with their corresponding values
on the server side.  For this example, the HTML that the Turkle server
sends to the browser is::

     <script>
       var a = [3,6,9];
       // a[0]=3, a[1]=6, a[2]=9
     </script>

However, if you want to save JSON data as a form value, then you need
to use ``JSON.stringify()`` to convert the in-memory JavaScript object
to a JSON string representation.  As an example, this jQuery-based
code serializes output and adds it to the DOM as an input element when
the submit button is pressed::

     $('input[type="submit"]').on("click", function(event) {
       var output = my_function_that_grabs_output();
       var string = escapeHtml(JSON.stringify(output));
       $("#mturk_form").append('<input name="output" type="hidden" value="' + string + '">');
     });

The data is then available in the output CSV as JSON as the variable Answer.output.

JavaScript and CSS
------------------

JavaScript and CSS can be placed in the template itself or linked to from
another web server. If the users will have access to the Internet, using
public CDNs is an excellent option. Otherwise, a local web server could
be used to host common JavaScript and CSS files.

The ``emotion detection`` and ``image contains`` template examples uses
Bootstrap and jQuery. The ``translate validate`` template uses the
Parsley validation library.

Preventing Default Browser Behavior that Affects Data Quality
-------------------------------------------------------------

Users will accidentally trigger form submission by pressing the Enter
key outside of a text field.  Some browsers use the Backspace key to
trigger the "Back" action.  Users will accidentally navigate away from
the form (discarding their work) if they hit Backspace outside of a
text field.

This jQuery-based code disables the default behavior for the Enter and
Backspace keys when the user is not editing a text field::

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

Gotchas
-------

Do not include text like this ``${variable}`` in your template unless it is
a variable in your input CSV file. Accidentally adding something like this
in your JavaScript code will cause Turkle's template rendering to modify it.

Do not include a form element in your template. The template is
inserted into a form element and a form in a form is invalid HTML.

Because your entire HTML template is wrapped in a form element, the
default behavior for any buttons in your template will be to trigger
form submission.  To prevent a button from submitting the form, set
the "type" of the button to "button" (instead of the default button
type, "submit")::

    <button type="button">

Do not use JavaScript or CSS resources included with Turkle. There is no
guarantee that those resources will be there in the future.

Mechanical Turk requires at least one element of type input, select, or textarea.
Turkle requires the same to maintain compatibility. If generating your form
body using JavaScript, add a dummy hidden field in the template to pass this
validation check.

.. _Concrete: https://github.com/hltcoe/concrete
