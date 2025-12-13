
# Browser Test Plan

1.  **Admin Login**
    -   Go to /login
    -   User: admin, Pass: admin
    -   Verify redirection to Dashboard (or presence of Dashboard link)
    -   Logout

2.  **Supervisor Login**
    -   Go to /login
    -   User: supervisor, Pass: 123
    -   Verify redirection to Dashboard (or presence of Dashboard link)
    -   Logout

3.  **Collaborator Login**
    -   Go to /login
    -   User: colaborador, Pass: 123
    -   Verify redirection to Index (Dashboard link should NOT be present)
    -   Try to access /dashboard directly -> Expect redirect/error.
    -   Logout
