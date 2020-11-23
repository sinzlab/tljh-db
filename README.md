# tljh-db

Everytime a new user is created in the JupyterHub a corresponding user will
be created in a pre-configured database server by this plugin. Afterwards a
matching DataJoint configuration file will be placed in the home directory
of the newly created JupyterHub user.

## Configuration

This plugin is configured via `/srv/tljh-db.ini`.

Example:

```INI
[DEFAULT]
Host = 127.0.0.1
User = root
Password = root-password
```

