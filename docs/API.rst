REST API
==========

Turkle has a REST API for administration of users, groups, projects, and batches.
A full OpenAPI schema of the API is available at `/api/schema/`.

The API uses integer identifiers for all the objects.
These identifiers are included in the response when creating or listing objects.
In the admin UI, the identifier is included in any URL for that object.

Client
----------
ToDo

Authentication
---------------
It requires token-based authentication and tokens can be created per user in the admin UI.
Once a token has been created, it is passed as a header in the request::

  token = 'ABCDEF'
  headers = {'Authorization': f'TOKEN {token}'}
  resp = requests.get('http://localhost:8000/api/users/', headers=headers)

Users
--------
Listing users
`````````````````
Perform a **get** on `/api/users/`.
The response is paginated and includes next and previous links to walk the user list.

Creating a user
`````````````````
Perform a **post** on `/api/users/`.
The payload at a minimum must include username and password::

  {
    "username": "jsmith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "jsmith@example.org",
    "password": "p@ssw0rd"
  }

Retrieving a user
`````````````````
Perform a **get** on `/api/users/{id}/` where id is the user's integer identifier.

To retrieve based on username. perform a **get** on `/api/users/username/{username}/`.

Update a user
`````````````````
Perform a **patch** on `/api/users/{id}/` where id is the user's integer identifier.
The JSON payload is a dictionary of fields to update.

Groups
---------
Listing groups
`````````````````
Perform a **get** on `/api/groups/`.
The response is paginated and includes next and previous links to walk the list.

Creating a group
`````````````````
Perform a **post** on `/api/groups/`.
The payload must include the name of the group and a list of user integer identifiers::

  {
    "name": "Spanish",
    "users": [7, 34, 35, 36]
  }

Retrieving a group
``````````````````
Perform a **get** on `/api/groups/{id}/` where id is the group's integer identifier.

To retrieve based on a group name. perform a **get** on `/api/groups/name/{name}/`.
This will return a list of groups that exactly match that group name.
It is a list since group names are not required to be unique in Turkle.

Adding users to a group
```````````````````````````
Perform a **post** on `/api/groups/{id}/users/` where id is the group's integer identifier.

The payload is a dictionary with a key of *users* which is a list of user integer identifiers.

Projects
----------
Listing projects
`````````````````
Perform a **get** on `/api/projects/`.
The response is paginated and includes next and previous links to walk the list.

Creating a project
```````````````````
Perform a **post** on `/api/projects/`.
The payload must include the name of the project, the html template, and the template filename::

  {
    "name": "Image Contains",
    "html_template": "<html>template as a string here</html>,
    "filename": "image_contains.html"
  }

Optional fields include active, allotted_assignment_time, assignments_per_task, and login_required.

Retrieving a project
`````````````````````
Perform a **get** on `/api/projects/{id}/` where id is the project's integer identifier.

Update a project
`````````````````
Perform a **patch** on `/api/projects/{id}/` where id is the project's integer identifier.
The JSON payload is a dictionary of fields to update and can include the html_template.

Batches
----------
Listing batches
`````````````````
Perform a **get** on `/api/batches/`.
The response is paginated and includes next and previous links to walk the list.

Creating a batch
```````````````````
Perform a **post** on `/api/batches/`.
The payload must include the name of the batch, the project identifier,
and the csv data and filename::

  {
    "name": "Bird Photos",
    "project": 20,
    "filename": "image_contains.csv",
    "csv_text": "csv as string"
  }

Optional fields include active, allotted_assignment_time, assignments_per_task, and login_required.

Retrieving a batch
`````````````````````
Perform a **get** on `/api/batches/{id}/` where id is the batch's integer identifier.

Update a batch
`````````````````
Perform a **patch** on `/api/batches/{id}/` where id is the batch's integer identifier.
The JSON payload is a dictionary of fields to update and cannot include the csv data.
If a bad batch was created, delete it using the admin UI.

Additional tasks can be added to an existing batch by a **post** to `/api/batches/{id}/tasks/`.
The payload is a dictionary with a key of *csv_text*.
The fields in the CSV data must match the fields in html template of the project.

Batch status
`````````````````
To download the input data for a batch as a CSV file, do a **get** on `/api/batches/{id}/input/`.

To download the results data for a batch as a CSV file, do a **get** on `/api/batches/{id}/results/`.

To get up-to-date progress for a batch, do a **get** on `/api/batches/{id}/progress/`.

Permissions
------------
Projects and Batches can be restricted to particular users or groups.
To retrieve the current permissions, perform a **get** on `/api/projects/{id}/permissions/`
(replacing "projects" with "batches" to get a batch's permissions).

To add additional users and groups to a project's permissions, perform a **post** on
`/api/projects/{id}/permissions/` with a payload of users and groups::

  {
    "users": [],
    "groups": [29, 63]
  }

To replace the current permissions for a project, perform a **put** on the endpoint.
