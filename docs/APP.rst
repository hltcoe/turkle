App
======

Instead of running Turkle as its own site, you can install Turkle
as a Django app to an existing site.  The amount of configuration
and modifications required will depend on the site and we cannot
enumerate every possible conflict with other Django apps. We
recommend that you begin by checking Turkle's dependencies against
the dependencies for your site for possible conflicts in versions.
Other aspects to check are Turkle's custom user/group admins and
its use of the guardian app for permissions.

Installing
-------------------
You can install the Turkle package using::

    pip install turkle

After the python package is installed, add Turkle as an app
along with its other required apps::

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        'turkle',
        'guardian',
        'admin_auto_filters',
    )

Next add the guardian permissions as an authentication backend::

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',  # example default auth backend
        'guardian.backends.ObjectPermissionBackend',
    )

Turkle uses a standard set of middleware that are likely already added::

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

Finally, add Turkle's context processor::

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'turkle.utils.turkle_vars',
                ],
            },
        },
    ]

This completes the changes to your site's settings.py.
After this, you will need to add Turkle to your site's URLs.
In the below example, Turkle is registered to the /turkle/ base URL::

    path('turkle/', include('turkle.urls')),

Another change you may need to make is to register Turkle's model admins
with your site's admins. This is needed if you use a custom admin site
rather than the default from django.contrib.admin. Take a look at the
bottom of Turkle's admin.py file to see which model admins need to be registered.
