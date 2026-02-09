# API Testing

These tests make real API calls (including POSTs) and modify the database.

A file-based switch is used to control which database the backend connects to.

---

## Before testing

1. Recreate the test database (`charging_database_test`) using the provided SQL script /database/testing_db_creator.

2. Create the flag file in the project root.

Windows:

```powershell
New-Item .USE_TEST_DB
```
```cmd
type nul > .USE_TEST_DB
```

macOS / Linux:

```bash
touch .USE_TEST_DB
```

3. Start the backend.

4. Run tests:

```bash
py -m API-testing
```

---

## After testing

Delete the flag file.

Windows:

```powershell
Remove-Item .USE_TEST_DB
```

```cmd
del .USE_TEST_DB
```

macOS / Linux:

```bash
rm .USE_TEST_DB
```

Backend will reconnect to the main database automatically.

.USE_TEST_DB is supposed to be in .gitignore
