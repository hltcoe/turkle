# Creating Templates #

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
public CDNs are an excellent option. Otherwise, a local web server could
be used to host common JavaScript and CSS files.

The `emotion detection` and `image contains` template examples include
Bootstrap and jQuery. The `translate validate` template includes the
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

## Gotchas ##

Do not include text like this `%{variable}` in your template unless it is 
a variable in your input CSV file. Accidentally adding something like this
in your JavaScript code will cause Turkle's template rendering to modify it.

Do not include a form in your template. The template is inserted into a form
element and a form in a form is invalid HTML.

Do not use JavaScript or CSS resources included with Turkle. There is no
guarantee that those resources will be there in the future. 
